import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 설정
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# 대상 파일 (필요하면 다른 그룹으로 변경 가능)
TARGET_FILE = 'app/data/dicts/SEVENTEEN.json'

def translate_batch(phrases):
    """5개 묶음으로 한 번에 번역 요청 (속도 최적화)"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 프롬프트 구성
    input_text = "\n".join([f"- {p}" for p in phrases])
    
    prompt = f"""
    You are a K-POP Translator. Translate these {len(phrases)} Korean phrases into Japanese and English meanings.
    
    INPUT:
    {input_text}
    
    OUTPUT FORMAT (JSON List ONLY):
    [
      {{"text": "Korean Phrase 1", "meaning_ja": "Japanese Meaning", "meaning_en": "English Meaning"}},
      ...
    ]
    
    CRITICAL: 
    1. Keep the exact original Korean text in "text".
    2. "meaning_ja" should be natural Japanese.
    3. "meaning_en" should be natural English.
    4. Output strictly valid JSON.
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"   ⚠️ API 호출 실패 (재시도 필요): {e}")
        return None

def main():
    if not os.path.exists(TARGET_FILE):
        print("❌ 파일이 없습니다.")
        return

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"🚀 {TARGET_FILE} 업그레이드 시작...")

    total_updated = 0

    for category, intent_data in data.items():
        print(f"\n📂 [{category}] 처리 중...")
        
        for intent, phrases in intent_data.items():
            # 이미 변환된 데이터(객체)인지 확인
            if phrases and isinstance(phrases[0], dict) and 'meaning_en' in phrases[0]:
                print(f"   ✅ {intent} (이미 완료됨)")
                continue
            
            # 문자열 리스트인 경우 변환 시작
            print(f"   🔄 {intent} 변환 중...", end="", flush=True)
            
            new_phrases = []
            
            # 5개씩 끊어서 처리 (API 효율성)
            chunk_size = 5
            for i in range(0, len(phrases), chunk_size):
                chunk = phrases[i:i+chunk_size]
                
                # 문자열만 골라내기 (혹시 섞여있을까봐)
                chunk_strs = [p for p in chunk if isinstance(p, str)]
                if not chunk_strs: continue

                translated_chunk = translate_batch(chunk_strs)
                
                if translated_chunk:
                    new_phrases.extend(translated_chunk)
                else:
                    # 실패 시 원본 유지 (나중에 다시 시도 가능하게)
                    new_phrases.extend([{'text': p, 'meaning_ja': p, 'meaning_en': p} for p in chunk_strs])
                
                time.sleep(1) # API 속도 조절 (유료면 줄여도 됨)

            # 데이터 업데이트
            data[category][intent] = new_phrases
            total_updated += 1
            print(" 완료!")

            # [중요] 하나 끝날 때마다 중간 저장 (데이터 보호)
            with open(TARGET_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 모든 작업 완료! 총 {total_updated}개 항목 업데이트됨.")

if __name__ == "__main__":
    main()