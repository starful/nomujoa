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
# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# [경로 설정] 프로젝트 루트 디렉토리를 sys.path에 추가하여 config.py를 임포트
# 현재 위치: project/scripts/batch_generator.py
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../scripts
project_root = os.path.dirname(current_dir) # .../ (프로젝트 루트)
sys.path.append(project_root)

from config import Config

# API 키 로드
if not Config.GEMINI_API_KEY:
    logger.error("❌ .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다!")
    exit()
genai.configure(api_key=Config.GEMINI_API_KEY)

# 파일 및 폴더 경로 설정 (Config 사용)
CSV_MASTER_FILE = os.path.join(Config.RAW_DATA_DIR, 'group_master.csv')
GROUPS_JSON_FILE = Config.GROUPS_FILE
DICTS_DIR = Config.DICTS_DIR
MAPPING_FILE = Config.MAPPING_FILE

# 사전 디렉토리 생성 (없으면 생성)
os.makedirs(DICTS_DIR, exist_ok=True)

# ==========================================
# 2. 함수 정의
# ==========================================

def sync_groups_from_csv():
    """CSV를 원본으로 삼아 groups.json을 업데이트하고, 신규/변경 그룹 목록을 반환합니다."""
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
            # 멤버 리스트 파싱 (콤마로 구분)
            members = [m.strip() for m in row['members'].split(',') if m.strip()]
            # 색상 리스트 파싱
            colors = [c.strip() for c in row['colors'].split(',') if c.strip()]
            csv_groups[group_name] = {"members": members, "colors": colors}

    newly_added_groups = {}
    is_updated = False
    
    # CSV 데이터와 JSON 비교하여 업데이트
    for group_name, info in csv_groups.items():
        if group_name not in groups_data or groups_data[group_name] != info:
            logger.info(f"🔄 동기화 감지: '{group_name}' 그룹 정보 업데이트/추가")
            groups_data[group_name] = info
            newly_added_groups[group_name] = info['members']
            is_updated = True
    
    if is_updated:
        with open(GROUPS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ '{GROUPS_JSON_FILE}' 파일 동기화 완료.")
        
    return groups_data, newly_added_groups

def generate_slang_list(group_name, member_name, intent_jp, intent_key):
    """Gemini API를 호출하여 K-POP 슬랭 리스트를 생성합니다."""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    target_desc = f"group '{group_name}'"
    if member_name != "All":
        target_desc = f"member '{member_name}' of group '{group_name}'"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"   🔄 생성 시도: [{group_name}-{member_name}] {intent_key} (시도 {attempt+1}/{max_retries})")
            
            prompt = f"""
            ROLE: K-POP fan creating cheering slogans for {target_desc}.
            INTENT: "{intent_jp}" (Key: {intent_key})
            
            TASK: Create 5 Korean slang phrases with Japanese & English meanings.
            
            RULES:
            1. **KOREAN**: Authentic fandom slang/meme.
            2. **JAPANESE**: Natural meaning in Japanese.
            3. **ENGLISH**: Natural meaning in English.
            4. **FORMAT**: Korean | Japanese | English

            OUTPUT EXAMPLE:
            보라해 | 紫するよ(愛してる) | I purple you
            아포방포 | アポバンポ(永遠に) | ARMY Forever BTS Forever
            
            GENERATE 5 LINES:
            """
            
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=1.0))
            
            raw_text = response.text.strip()
            lines = [line.strip() for line in raw_text.split('\n') if '|' in line]
            
            result_list = []
            for line in lines:
                parts = [p.strip() for p in line.split('|')]
                
                if len(parts) >= 2:
                    korean_text = re.sub(r'^\d+[\.\)]\s*', '', parts[0])
                    item = {
                        "text": korean_text,
                        "meaning_ja": parts[1],
                        "meaning_en": parts[2] if len(parts) > 2 else parts[1]
                    }
                    result_list.append(item)

            if result_list:
                logger.info(f"      ✅ 생성 성공! ({len(result_list)}개)")
                return result_list[:5]

        except Exception as e:
            logger.warning(f"      ⚠️ API 오류 발생: {e}, 재시도합니다.")
            time.sleep(attempt * 2 + 1)
    
    logger.error(f"      🚫 최종 실패: [{group_name}-{member_name}] {intent_key}")
    return []

# ==========================================
# 3. 메인 실행 로직
# ==========================================
def main():
    logger.info("🚀 작업 시작: CSV 동기화 및 생성할 그룹 1팀 스캔...")
    
    # 1. CSV와 groups.json 동기화
    all_groups_data, _ = sync_groups_from_csv() 
    
    # 2. [핵심] 사전 파일이 없는 그룹 '하나만' 찾기
    target_group = None
    target_members = []
    
    # CSV에 정의된 순서대로 순회
    with open(CSV_MASTER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group_name = row['group_name'].strip()
            dict_file = os.path.join(DICTS_DIR, f"{group_name}.json")
            if not os.path.exists(dict_file):
                logger.info(f"✨ 생성 대상 발견: '{group_name}' (사전 파일 없음)")
                target_group = group_name
                target_members = all_groups_data.get(group_name, {}).get('members', [])
                break # <<-- 하나 찾으면 바로 중단! (API 할당량 관리)

    if not target_group:
        logger.info("✅ 모든 그룹의 사전 파일이 이미 존재합니다.")
        logger.info("🏁 작업 종료.")
        return

    logger.info(f"🚀 이번 실행 타겟: [{target_group}] 그룹의 AI 사전 생성을 시작합니다.")

    # 매핑(Intent) 파일 로드
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            INTENTS = list(json.load(f).get("mappings", {}).items())
    except Exception as e:
        logger.error(f"❌ 매핑 파일({MAPPING_FILE}) 로드 실패: {e}")
        return

    # 3. 찾은 그룹 '하나'에 대해서만 사전 생성 실행
    file_path = os.path.join(DICTS_DIR, f"{target_group}.json")
    group_data = {"All": {}}
    for member in target_members:
        group_data[member] = {}

    logger.info(f"📂 [{target_group}] 사전 파일 생성 중...")

    for jp_text, key in INTENTS:
        # 그룹 공통 ('All') 데이터 생성
        slangs_all = generate_slang_list(target_group, "All", jp_text, key)
        if slangs_all: 
            group_data["All"][key] = slangs_all
        time.sleep(1.5)

        # 멤버별 데이터 생성
        for member in target_members:
            slangs_member = generate_slang_list(target_group, member, jp_text, key)
            if slangs_member: 
                group_data[member][key] = slangs_member
            time.sleep(1.5)

    # 최종 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(group_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"🎉 [{target_group}] 사전 파일 생성이 완료되었습니다.")
    logger.info("🏁 작업 종료. 다음 그룹을 생성하려면 스크립트를 다시 실행하세요.")

if __name__ == "__main__":
    main()