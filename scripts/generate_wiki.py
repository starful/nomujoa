import csv
import json
import os
import time
import re
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai

# ==========================================
# 1. 환경변수 및 설정 로드
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # nomujoa/
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in .env file.")
    exit()

# 🎯 한 번에 생성할 개수 제한 (5개)
LIMIT = 5

# 경로 설정
INPUT_CSV = os.path.join(BASE_DIR, "scripts", "file", "kpop_terms.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
LOG_DIR = os.path.join(BASE_DIR, "app", "logs")
HISTORY_FILE = os.path.join(LOG_DIR, "wiki_processed_history.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 2. 함수 정의
# ==========================================

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def append_history(term):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{term}\n")

def parse_markdown_response(text, term, category):
    """
    AI가 준 텍스트에서 Frontmatter와 본문을 분리합니다.
    """
    # 1. 제목 추출 (Title: ...)
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else f"{term} (K-POP Term)"

    # 2. 슬러그 추출 (Slug: ...)
    slug_match = re.search(r"Slug:\s*(.+)", text)
    slug = slug_match.group(1).strip() if slug_match else term.replace(" ", "-").lower()
    
    # 3. 요약 추출 (Summary: ...)
    summary_match = re.search(r"Summary:\s*(.+)", text)
    summary = summary_match.group(1).strip() if summary_match else f"Detailed explanation of {term}."

    # 4. 태그 추출 (Tags: ...)
    tags_match = re.search(r"Tags:\s*(.+)", text)
    tags = [t.strip() for t in tags_match.group(1).split(',')] if tags_match else ["K-POP", category]

    # 5. 본문 추출 및 청소 (여기가 수정됨!)
    body_parts = text.split("---BODY START---")
    body_content = body_parts[1].strip() if len(body_parts) > 1 else text
    
    # [수정] 불필요한 꼬리표 제거
    body_content = body_content.replace("---BODY END---", "").replace("```", "").strip()

    return {
        "slug": slug,
        "frontmatter": {
            "layout": "wiki",
            "title": title,
            "category": category,
            "tags": tags,
            "summary": summary,
            "date": time.strftime("%Y-%m-%d")
        },
        "body_content": body_content
    }

def get_kpop_term_info(term, category):
    """AI에게 텍스트 형식으로 요청"""
    print(f"🎤 AI Generating Wiki (Deep Mode): {term}")
    
    prompt = f"""
    You are a professional K-POP Culture Historian.
    Write an **Extremely Detailed Wiki Entry** for: "{term}" (Category: {category}).
    Target Audience: Global fans. Language: English.
    
    [Format Requirement - STRICTLY FOLLOW THIS]
    You must output in this exact plain text format (No JSON):

    Title: English Title (Korean)
    Slug: english-url-slug-lowercase
    Summary: A short summary (2 sentences).
    Tags: keyword1, keyword2, keyword3
    ---BODY START---
    ## 1. Introduction
    (Write detailed content here... 7000+ characters aim)
    ...
    
    [Content Requirements]
    - Detail: Extremely detailed. Explain history, nuance, and cultural context deeply.
    - Structure: 1. Intro, 2. Etymology, 3. Usage, 4. Examples, 5. Cultural Impact.
    - Formatting: Use Markdown (Bold, Headers, Lists).
    """

    for i in range(3):
        try:
            # JSON 모드 끄고 일반 텍스트 모드로 호출
            res = model.generate_content(prompt)
            return parse_markdown_response(res.text, term, category)
        except Exception as e:
            print(f"   ⚠️ Retry ({i+1}/3)... Error: {e}")
            time.sleep(3)
    return None

def save_to_md(data):
    slug = data['slug']
    # 파일명 특수문자 제거
    slug = re.sub(r'[^a-zA-Z0-9-]', '', slug)
    filename = f"{slug}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # [핵심] 저장하기 전에 본문 내용 청소 (Clean up)
    clean_body = data['body_content']
    clean_body = clean_body.replace("---BODY END---", "")
    clean_body = clean_body.replace("```markdown", "")
    clean_body = clean_body.replace("```", "")
    clean_body = clean_body.strip()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write(json.dumps(data['frontmatter'], ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(clean_body)  # 청소된 본문 저장
    
    return filename


# ==========================================
# 3. 메인 실행
# ==========================================
def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        return

    processed_list = load_history()
    
    term_list = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['term'] not in processed_list:
                term_list.append(row)
            
    print(f"🚀 Total: {len(term_list) + len(processed_list)} / Target: {LIMIT}")
    
    count = 0
    target_list = term_list[:LIMIT] if LIMIT > 0 else term_list

    for item in tqdm(target_list):
        data = get_kpop_term_info(item['term'], item['category'])
        
        if data:
            filename = save_to_md(data)
            append_history(item['term'])
            print(f"   ✅ Saved: {filename} (Size: {len(data['body_content'])} chars)")
            count += 1
            time.sleep(2) 
        else:
            print(f"   ❌ Failed: {item['term']}")

    print(f"🏁 Done! Processed {count} items.")

if __name__ == "__main__":
    main()