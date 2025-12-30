import json
import os
import time
import logging
import re
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. 로깅(Logging) 설정 (파일 저장 제거됨)
# ---------------------------------------------------------
# 터미널에만 출력되도록 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()  # 화면 출력만 수행
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 2. 환경변수 및 설정 로드
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    logger.error("❌ GEMINI_API_KEY가 환경변수에 없습니다! .env 파일을 확인하세요.")
    exit()

genai.configure(api_key=api_key)

# 그룹 및 멤버 명단 (groups.json에서 로드)
GROUPS_FILE = os.path.join(BASE_DIR, 'data', 'groups.json')

try:
    with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
        full_group_data = json.load(f)
        GROUP_MEMBERS = {
            k: v['members'] 
            for k, v in full_group_data.items() 
            if k != "General" and v.get('members')
        }
    logger.info(f"✅ 그룹 데이터 로드 완료: {len(GROUP_MEMBERS)}개 그룹")
except Exception as e:
    logger.error(f"❌ 그룹 데이터 로드 실패: {e}")
    exit()

# 매핑 파일 로드
MAPPING_FILE = os.path.join(BASE_DIR, 'data', 'phrase_mapping.json')

if not os.path.exists(MAPPING_FILE):
    logger.error(f"❌ 매핑 파일이 없습니다: {MAPPING_FILE}")
    exit()

try:
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        MAPPINGS = json.load(f).get("mappings", {})
except Exception as e:
    logger.error(f"❌ 매핑 파일 JSON 로드 실패: {e}")
    exit()

INTENTS = [(jp, key) for jp, key in MAPPINGS.items()]


# ---------------------------------------------------------
# 3. AI 생성 함수
# ---------------------------------------------------------
def generate_slang_list(group_name, member_name, intent_jp, intent_key):
    # 유료 API 사용 시 1.5-flash 모델 권장 (속도/비용 최적)
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
            
            response = model.generate_content(
                prompt, 
                generation_config=genai.types.GenerationConfig(temperature=1.0)
            )
            
            raw_text = response.text.strip()
            lines = [line.strip() for line in raw_text.split('\n') if '|' in line]
            
            result_list = []
            for line in lines:
                parts = [p.strip() for p in line.split('|')]
                
                if len(parts) >= 2:
                    korean_text = parts[0]
                    # 숫자 제거 (예: "1. 보라해" -> "보라해")
                    korean_text = re.sub(r'^\d+[\.\)]\s*', '', korean_text)

                    item = {
                        "text": korean_text,
                        "meaning_ja": parts[1],
                        "meaning_en": parts[2] if len(parts) > 2 else parts[1]
                    }
                    result_list.append(item)

            if len(result_list) < 3:
                logger.warning(f"      ⚠️ 결과 부족(3개 미만), 재시도합니다.")
                time.sleep(1)
                continue 
            
            logger.info(f"      ✅ 생성 성공! ({len(result_list)}개)")
            return result_list[:5]

        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                logger.warning("      ⏳ 429 요청 제한. 유료 계정이 아니면 60초 대기...")
                time.sleep(60) 
            else:
                logger.error(f"      ❌ API 오류 발생: {e}")
                time.sleep(1)
    
    logger.error(f"      🚫 최종 실패: [{group_name}-{member_name}] {intent_key}")
    return []


# ---------------------------------------------------------
# 4. 메인 실행 로직
# ---------------------------------------------------------
def main():
    save_dir = os.path.join(BASE_DIR, 'data', 'dicts')
    os.makedirs(save_dir, exist_ok=True)

    logger.info(f"🚀 배치 작업 시작")
    logger.info(f"📂 저장 위치: {save_dir}")

    for group, members in GROUP_MEMBERS.items():
        file_path = os.path.join(save_dir, f"{group}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try: 
                    group_data = json.load(f)
                except Exception as e:
                    logger.error(f"❌ JSON 파싱 오류. 초기화합니다. 에러: {e}")
                    group_data = {}
        else:
            group_data = {}

        logger.info(f"📂 [{group}] 데이터 처리 시작...")

        if "All" not in group_data: group_data["All"] = {}
        for member in members:
            if member not in group_data: group_data[member] = {}

        change_count = 0
        for jp_text, key in INTENTS:
            
            # (A) 그룹 공통
            needs_update = False
            if key not in group_data["All"] or \
               (group_data["All"][key] and isinstance(group_data["All"][key][0], str)) or \
               (group_data["All"][key] and isinstance(group_data["All"][key][0], dict) and "meaning_en" not in group_data["All"][key][0]):
                needs_update = True
            
            if needs_update:
                slangs = generate_slang_list(group, "All", jp_text, key)
                if slangs: 
                    group_data["All"][key] = slangs
                    change_count += 1
                time.sleep(0.1) 

            # (B) 멤버별
            for member in members:
                needs_update_member = False
                if key not in group_data[member] or \
                   (group_data[member][key] and isinstance(group_data[member][key][0], str)) or \
                   (group_data[member][key] and isinstance(group_data[member][key][0], dict) and "meaning_en" not in group_data[member][key][0]):
                    needs_update_member = True
                
                if needs_update_member:
                    slangs = generate_slang_list(group, member, jp_text, key)
                    if slangs: 
                        group_data[member][key] = slangs
                        change_count += 1
                    time.sleep(0.1) 

            # 5번 변경될 때마다 중간 저장
            if change_count > 0 and change_count % 5 == 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(group_data, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 중간 저장 완료 ({group})")

        # 최종 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🎉 [{group}] 처리 완료.")

    logger.info("🏁 모든 작업이 종료되었습니다.")

if __name__ == "__main__":
    main()