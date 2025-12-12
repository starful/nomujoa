import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# 1. 그룹 및 멤버 명단
GROUP_MEMBERS = {
   "BTS": ["RM", "Jin", "Suga", "J-Hope", "Jimin", "V", "Jungkook"]
}

# 2. 매핑 파일 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(BASE_DIR, 'data', 'phrase_mapping.json')

with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
    MAPPINGS = json.load(f).get("mappings", {})

# 인텐트 리스트
INTENTS = [(jp, key) for jp, key in MAPPINGS.items()]

def generate_slang_list(group_name, member_name, intent_jp, intent_key):
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    target_print = f"[{group_name}]"
    if member_name != "All":
        target_print += f"-[{member_name}]"
    
    print(f"   {target_print} {intent_key}...", end=" ", flush=True)

    target_desc = f"group '{group_name}'"
    if member_name != "All":
        target_desc = f"member '{member_name}' of group '{group_name}'"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # [수정] 프롬프트: 한 | 일 | 영 3단 구조 요청
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
            
            # [수정] 파싱 로직: text, meaning_ja, meaning_en 저장
            result_list = []
            for line in lines:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    result_list.append({
                        "text": parts[0],
                        "meaning_ja": parts[1],
                        "meaning_en": parts[2]
                    })
                elif len(parts) == 2: # 혹시 영어가 누락된 경우
                    result_list.append({
                        "text": parts[0],
                        "meaning_ja": parts[1],
                        "meaning_en": parts[1] # 영어 대신 일본어라도 채움
                    })

            if len(result_list) < 3:
                time.sleep(1)
                continue 
            
            print("✅")
            return result_list[:5]

        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                print("⏳", end="")
                time.sleep(10)
            else:
                print(f"❌ {e}")
                time.sleep(1)
    
    return []

def main():
    save_dir = os.path.join(BASE_DIR, 'data', 'dicts')
    os.makedirs(save_dir, exist_ok=True)

    print(f"🚀 데이터 생성 시작 (한|일|영 3개 국어 버전)")
    print(f"📂 저장 위치: {save_dir}\n")

    for group, members in GROUP_MEMBERS.items():
        file_path = os.path.join(save_dir, f"{group}.json")
        
        # 기존 데이터 로드 (이어하기)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try: group_data = json.load(f)
                except: group_data = {}
        else:
            group_data = {}

        print(f"\n📂 [{group}] 데이터 처리 중...")

        if "All" not in group_data: group_data["All"] = {}
        for member in members:
            if member not in group_data: group_data[member] = {}

        for jp_text, key in INTENTS:
            # (A) 그룹 공통 - 데이터가 없거나, 구버전(문자열)이거나, 영어 뜻이 없는 경우 갱신
            if key not in group_data["All"] or \
               (group_data["All"][key] and isinstance(group_data["All"][key][0], str)) or \
               (group_data["All"][key] and "meaning_en" not in group_data["All"][key][0]):
                
                slangs = generate_slang_list(group, "All", jp_text, key)
                if slangs: group_data["All"][key] = slangs
                time.sleep(1.5)

            # (B) 멤버별
            for member in members:
                if key not in group_data[member] or \
                   (group_data[member][key] and isinstance(group_data[member][key][0], str)) or \
                   (group_data[member][key] and "meaning_en" not in group_data[member][key][0]):
                   
                    slangs = generate_slang_list(group, member, jp_text, key)
                    if slangs: group_data[member][key] = slangs
                    time.sleep(1) 

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 {group}.json 저장 완료")

if __name__ == "__main__":
    main()