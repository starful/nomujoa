import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# 1. 그룹 및 멤버 명단 (핵심 6개 그룹)
GROUP_MEMBERS = {
    "BTS": ["RM", "Jin", "Suga", "J-Hope", "Jimin", "V", "Jungkook"],
    "SEVENTEEN": ["S.COUPS", "Jeonghan", "Joshua", "Jun", "Hoshi", "Wonwoo", "Woozi", "The8", "Mingyu", "DK", "Seungkwan", "Vernon", "Dino"],
    "TWICE": ["Nayeon", "Jeongyeon", "Momo", "Sana", "Jihyo", "Mina", "Dahyun", "Chaeyoung", "Tzuyu"],
    "Stray Kids": ["Bang Chan", "Lee Know", "Changbin", "Hyunjin", "Han", "Felix", "Seungmin", "I.N"],
    "IVE": ["Yujin", "Gaeul", "Rei", "Wonyoung", "Liz", "Leeseo"],
    "NewJeans": ["Minji", "Hanni", "Danielle", "Haerin", "Hyein"]
}

# 2. 매핑 파일 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(BASE_DIR, 'data', 'phrase_mapping.json')

with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
    MAPPINGS = json.load(f).get("mappings", {})

INTENTS = [(jp, key) for jp, key in MAPPINGS.items()]

def generate_slang_list(group_name, member_name, intent_jp, intent_key):
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 로그에 멤버 이름 표시
    target_print = f"[{group_name}]"
    if member_name != "All":
        target_print += f"-[{member_name}]"
    
    print(f"   {target_print} {intent_key}...", end=" ", flush=True)

    # 프롬프트 타겟 설정
    target_desc = f"group '{group_name}'"
    if member_name != "All":
        target_desc = f"member '{member_name}' of group '{group_name}'"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            prompt = f"""
            ROLE: You are a die-hard Korean fan of K-POP {target_desc}.
            TASK: Create 5 Korean cheering slogans/memes for the intent: "{intent_jp}" (Key: {intent_key}).
            
            CRITICAL RULES:
            1. **KOREAN ONLY**: Use Hangul. No English names.
            2. **MEMES & SLANG**: Use specific fandom slang/nicknames for {member_name if member_name != 'All' else group_name}.
            3. **VARIETY**: Mix cute, powerful, and emotional tones.
            4. **LENGTH**: Short (under 15 chars).

            OUTPUT FORMAT:
            Phrase1|Phrase2|Phrase3|Phrase4|Phrase5
            (Text only, separated by pipes)
            """
            
            response = model.generate_content(
                prompt, 
                generation_config=genai.types.GenerationConfig(temperature=1.0)
            )
            
            raw_text = response.text.strip()
            lines = [line.strip() for line in raw_text.split('|') if line.strip()]
            
            if len(lines) < 3:
                time.sleep(1)
                continue 
            
            print("✅")
            return lines[:5]

        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                print("⏳(대기)", end="")
                time.sleep(10) # 429 뜨면 좀 쉼
            else:
                print(f"❌ {e}")
                time.sleep(1)
    
    return []

def main():
    save_dir = os.path.join(BASE_DIR, 'data', 'dicts')
    os.makedirs(save_dir, exist_ok=True)

    print(f"🚀 데이터 생성 시작 (멤버 포함 풀버전)")
    print(f"📂 저장 위치: {save_dir}\n")

    for group, members in GROUP_MEMBERS.items():
        file_path = os.path.join(save_dir, f"{group}.json")
        
        # 기존 데이터 로드 (이어하기)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    group_data = json.load(f)
                except:
                    group_data = {}
        else:
            group_data = {}

        print(f"\n📂 [{group}] 데이터 처리 중...")

        # 1. 'All' 데이터 확인 및 생성
        if "All" not in group_data:
            group_data["All"] = {}
        
        # 2. 멤버 데이터 구조 초기화
        for member in members:
            if member not in group_data:
                group_data[member] = {}

        # 3. 모든 문구(Intent)에 대해 루프
        for jp_text, key in INTENTS:
            
            # (A) 그룹 공통(All) 생성
            if key not in group_data["All"]:
                slangs = generate_slang_list(group, "All", jp_text, key)
                if slangs:
                    group_data["All"][key] = slangs
                time.sleep(1.5) # 안전 딜레이

            # (B) 멤버별 생성 [이게 추가된 핵심!]
            for member in members:
                if key not in group_data[member]:
                    slangs = generate_slang_list(group, member, jp_text, key)
                    if slangs:
                        group_data[member][key] = slangs
                    # 멤버별 생성은 1초 딜레이 (너무 빠르면 에러남)
                    time.sleep(1) 

        # 그룹 하나 끝날 때마다 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 {group}.json 저장 완료 (멤버 데이터 포함)")

if __name__ == "__main__":
    main()