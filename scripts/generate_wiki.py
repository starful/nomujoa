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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in .env file.")
    exit()

# 🎯 [설정] 생성할 언어 및 개수
TARGET_LANG = "en"  # 생성할 언어: 'ja', 'zh', 'en', 'ko' 중 선택
LIMIT = 30          # 한 번 실행 시 생성할 개수

# 경로 설정
INPUT_CSV = os.path.join(BASE_DIR, "data", "raw", "kpop_terms.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
LOG_DIR = os.path.join(BASE_DIR, "app", "logs")
# 기록 파일명에 언어를 포함하여 중복 체크 (예: wiki_history_ja.txt)
HISTORY_FILE = os.path.join(LOG_DIR, f"wiki_history_{TARGET_LANG}.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest') # 최신 모델 사용

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

def parse_markdown_response(text, term, category, lang):
    """
    AI 응답에서 정보를 추출하고 다국어 규칙을 적용합니다.
    """
    # 1. 제목 추출 (Title: ...)
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else f"{term}"

    # 2. 슬러그 추출 (Slug: ...)
    slug_match = re.search(r"Slug:\s*(.+)", text)
    slug = slug_match.group(1).strip() if slug_match else term.replace(" ", "-").lower()
    # 슬러그에서 혹시 모를 언어 접미사 제거 (스크립트에서 나중에 붙임)
    slug = re.sub(r'(_ja|_zh|_en|_ko)$', '', slug)
    
    # 3. 요약 추출 (Summary: ...)
    summary_match = re.search(r"Summary:\s*(.+)", text)
    summary = summary_match.group(1).strip() if summary_match else ""

    # 4. 태그 추출 (Tags: ...)
    tags_match = re.search(r"Tags:\s*(.+)", text)
    tags = [t.strip() for t in tags_match.group(1).split(',')] if tags_match else ["K-POP", category]

    # 5. 본문 추출
    body_parts = text.split("---BODY START---")
    body_content = body_parts[1].strip() if len(body_parts) > 1 else text
    body_content = body_content.replace("---BODY END---", "").replace("```markdown", "").replace("```", "").strip()

    return {
        "slug": slug,
        "lang": lang,
        "frontmatter": {
            "layout": "wiki",
            "title": title,
            "category": category,
            "tags": tags,
            "summary": summary,
            "date": time.strftime("%Y-%m-%d"),
            "lang": lang # Frontmatter에 lang 추가
        },
        "body_content": body_content
    }

def get_kpop_term_info(term, category, lang):
    """AI에게 특정 언어로 콘텐츠 생성을 요청"""
    
    # 언어 코드별 이름 매핑
    lang_names = {'ja': 'Japanese', 'zh': 'Chinese', 'en': 'English', 'ko': 'Korean'}
    target_lang_name = lang_names.get(lang, 'English')

    print(f"🎤 AI Generating Wiki [{target_lang_name}]: {term}")
    
    prompt = f"""
    You are a professional K-POP Culture Historian.
    Write an **Extremely Detailed Wiki Entry** for: "{term}" (Category: {category}).
    Target Audience: Global fans.
    Language: Write the entire response (Title, Summary, Body) in **{target_lang_name}**.
    
    [Format Requirement - STRICTLY FOLLOW THIS]
    Title: [Title in {target_lang_name}] (Keep Korean original term in parenthesis if applicable)
    Slug: [english-url-slug-only]
    Summary: [A short summary in {target_lang_name} - 2 sentences]
    Tags: keyword1, keyword2, keyword3
    ---BODY START---
    ## 1. Introduction
    (Write detailed content in {target_lang_name}... 5000+ characters aim)
    ...
    
    [Content Requirements]
    - Explain history, nuance, and cultural context deeply.
    - Structure: 1. Intro, 2. Etymology, 3. Usage, 4. Examples, 5. Cultural Impact.
    - Formatting: Use Markdown (Bold, Headers, Lists).
    """

    for i in range(3):
        try:
            res = model.generate_content(prompt)
            return parse_markdown_response(res.text, term, category, lang)
        except Exception as e:
            print(f"   ⚠️ Retry ({i+1}/3)... Error: {e}")
            time.sleep(5)
    return None

def save_to_md(data):
    slug = data['slug']
    lang = data['lang']
    
    # 파일명 규칙: slug_lang.md
    clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', slug)
    filename = f"{clean_slug}_{lang}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Frontmatter와 본문 결합
    import frontmatter
    from frontmatter.default_handlers import YAMLHandler
    
    post = frontmatter.Post(data['body_content'], **data['frontmatter'])
    
    try:
        # 파일 저장 (UTF-8)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        return filename
    except Exception as e:
        print(f"   ❌ Save Error: {e}")
        return None

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
            term = row['term'].strip()
            if term and (term not in processed_list):
                row['term'] = term
                term_list.append(row)
            
    print(f"🚀 Total pending for [{TARGET_LANG}]: {len(term_list)} / LIMIT: {LIMIT}")
    
    count = 0
    target_list = term_list[:LIMIT]

    for item in tqdm(target_list):
        data = get_kpop_term_info(item['term'], item['category'], TARGET_LANG)
        
        if data:
            filename = save_to_md(data)
            if filename:
                append_history(item['term'])
                print(f"   ✅ Saved: {filename} (Size: {len(data['body_content'])} chars)")
                count += 1
                time.sleep(2) 
        else:
            print(f"   ❌ Failed: {item['term']}")

    print(f"🏁 Done! Processed {count} items in {TARGET_LANG}.")

if __name__ == "__main__":
    main()