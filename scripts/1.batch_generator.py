import csv
import json
import os
import time
import logging
import re
import sys
import google.generativeai as genai

# ==========================================
# 1. 설정 및 초기화
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from config import Config

if not Config.GEMINI_API_KEY:
    logger.error("❌ .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다!")
    exit()
genai.configure(api_key=Config.GEMINI_API_KEY)

CSV_MASTER_FILE = os.path.join(Config.RAW_DATA_DIR, 'group_master.csv')
GROUPS_JSON_FILE = Config.GROUPS_FILE
DICTS_DIR = Config.DICTS_DIR
MAPPING_FILE = Config.MAPPING_FILE

os.makedirs(DICTS_DIR, exist_ok=True)

# ==========================================
# 2. 함수 정의
# ==========================================

def sync_groups_from_csv():
    """CSV를 원본으로 삼아 groups.json을 업데이트"""
    if not os.path.exists(CSV_MASTER_FILE):
        logger.error(f"❌ 마스터 CSV 파일이 없습니다: {CSV_MASTER_FILE}")
        return {}, {}

    try:
        with open(GROUPS_JSON_FILE, 'r', encoding='utf-8') as f:
            groups_data = json.load(f)
    except FileNotFoundError:
        groups_data = {"General": {"members": [], "colors": ["#ff007f", "#000000"]}}

    csv_groups = {}
    with open(CSV_MASTER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group_name = row['group_name'].strip()
            members = [m.strip() for m in row['members'].split(',') if m.strip()]
            colors = [c.strip() for c in row['colors'].split(',') if c.strip()]
            csv_groups[group_name] = {"members": members, "colors": colors}

    is_updated = False
    for group_name, info in csv_groups.items():
        if group_name not in groups_data or groups_data[group_name] != info:
            logger.info(f"🔄 동기화 감지: '{group_name}' 업데이트")
            groups_data[group_name] = info
            is_updated = True
    
    if is_updated:
        with open(GROUPS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups_data, f, ensure_ascii=False, indent=2)
        
    return groups_data

def generate_member_slangs_batch(group_name, member_name, intents):
    """한 명의 멤버에 대해 모든 문구(Intents)를 한 번에 생성"""
    # 2.0-flash 모델은 속도가 빠르고 JSON 모드에 최적화되어 있습니다.
    model = genai.GenerativeModel('gemini-flash-latest')
    
    target_desc = f"group '{group_name}'"
    if member_name != "All":
        target_desc = f"member '{member_name}' of group '{group_name}'"

    # 프롬프트에 전달할 인텐트 목록 구성
    intent_list_text = "\n".join([f"- {key}: {val}" for val, key in intents])

    prompt = f"""
    ROLE: K-POP fan creating cheering slogans for {target_desc}.
    TASK: Generate 5 creative Korean slang phrases for EACH intent listed below.
    
    INTENTS TO GENERATE:
    {intent_list_text}

    RULES:
    1. For EACH intent key, provide exactly 5 phrases.
    2. Provide meanings in Japanese (meaning_ja) and English (meaning_en).
    3. Return the result STRICTLY in JSON format.
    
    JSON STRUCTURE:
    {{
      "intent_key": [
        {{"text": "슬랭1", "meaning_ja": "意味", "meaning_en": "meaning"}},
        ...
      ]
    }}
    """

    for attempt in range(3):
        try:
            logger.info(f"   🚀 일괄 생성 시작: [{group_name}-{member_name}] (시도 {attempt+1}/3)")
            
            # JSON 응답 모드 활성화
            response = model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json", "temperature": 1.0}
            )
            
            # JSON 파싱
            return json.loads(response.text)

        except Exception as e:
            logger.warning(f"      ⚠️ 오류 발생: {e}")
            time.sleep(5)
    
    return {}

# ==========================================
# 3. 메인 실행 로직
# ==========================================
def main():
    logger.info("🚀 작업 시작: CSV 동기화 및 타겟 그룹 스캔...")
    
    all_groups_data = sync_groups_from_csv() 
    
    target_group = None
    target_members = []
    
    # 딕셔너리 파일이 없는 그룹 하나 선택
    for group_name in all_groups_data:
        if group_name == 'General': continue
        dict_file = os.path.join(DICTS_DIR, f"{group_name}.json")
        if not os.path.exists(dict_file):
            target_group = group_name
            target_members = all_groups_data[group_name]['members']
            break

    if not target_group:
        logger.info("✅ 모든 그룹의 사전 파일이 존재합니다.")
        return

    # 매핑(Intent) 파일 로드
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            INTENTS = list(json.load(f).get("mappings", {}).items())
    except Exception as e:
        logger.error(f"❌ 매핑 파일 로드 실패: {e}")
        return

    logger.info(f"🔥 타겟: [{target_group}] 일괄 생성 프로세스 시작")

    file_path = os.path.join(DICTS_DIR, f"{target_group}.json")
    final_dict = {}

    # "All" + 멤버들 리스트 구성
    all_targets = ["All"] + target_members

    for idx, member in enumerate(all_targets):
        logger.info(f"📦 Step {idx+1}/{len(all_targets)}: [{member}] 데이터 생성 중...")
        
        # 한 멤버의 모든 인텐트를 한 번에 호출 (기존 수십 번 -> 1번으로 단축)
        member_data = generate_member_slangs_batch(target_group, member, INTENTS)
        
        if member_data:
            final_dict[member] = member_data
            logger.info(f"      ✅ [{member}] 완료")
        
        # API 할당량(Rate Limit)을 고려하여 멤버당 짧은 대기 시간만 가짐
        time.sleep(2)

    # 최종 결과 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=2)
    
    logger.info(f"🎉 [{target_group}] 사전 파일 생성 완료: {file_path}")

if __name__ == "__main__":
    main()