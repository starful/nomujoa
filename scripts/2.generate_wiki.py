import csv
import json
import os
import time
import re
from concurrent.futures import ThreadPoolExecutor # 멀티스레딩 추가
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai
import frontmatter

# ==========================================
# 1. 환경변수 및 설정 로드
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found.")
    exit()

TARGET_LANG = "en"  
LIMIT = 30          
MAX_WORKERS = 5     # [핵심] 동시에 실행할 작업 수 (무료계정 3~5, 유료 10~20 추천)

INPUT_CSV = os.path.join(BASE_DIR, "data", "raw", "kpop_terms.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
LOG_DIR = os.path.join(BASE_DIR, "app", "logs")
HISTORY_FILE = os.path.join(LOG_DIR, f"wiki_history_{TARGET_LANG}.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)

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
    text = text.replace("**", "") # 제목 등에 불필요한 강조 제거
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else f"{term}"

    slug_match = re.search(r"Slug:\s*(.+)", text)
    slug = slug_match.group(1).strip() if slug_match else term.replace(" ", "-").lower()
    slug = re.sub(r'(_ja|_zh|_en|_ko)$', '', slug)
    
    summary_match = re.search(r"Summary:\s*(.+)", text)
    summary = summary_match.group(1).strip() if summary_match else ""

    tags_match = re.search(r"Tags:\s*(.+)", text)
    tags = [t.strip() for t in tags_match.group(1).split(',')] if tags_match else ["K-POP", category]

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
            "lang": lang 
        },
        "body_content": body_content
    }

def process_single_term(item):
    """개별 단어를 처리하는 핵심 로직 (스레드에서 실행됨)"""
    term = item['term']
    category = item['category']
    lang = TARGET_LANG
    
    model = genai.GenerativeModel('gemini-2.0-flash') # 스레드마다 모델 생성(안정적)
    
    lang_names = {'ja': 'Japanese', 'zh': 'Chinese', 'en': 'English', 'ko': 'Korean'}
    target_lang_name = lang_names.get(lang, 'English')

    prompt = f"""
    You are a professional K-POP Culture Historian. SEO Expert.
    Write an **Extremely Detailed Wiki Entry** in {target_lang_name} for: "{term}" (Category: {category}).
    
    [Format Requirement]
    Title: [Title in {target_lang_name}]
    Slug: [english-url-slug-only]
    Summary: [2 sentences in {target_lang_name}]
    Tags: keyword1, keyword2, keyword3
    ---BODY START---
    ## 1. Introduction
    ...
    """

    for i in range(2): # 재시도 횟수 축소
        try:
            res = model.generate_content(prompt)
            data = parse_markdown_response(res.text, term, category, lang)
            
            # 저장 로직
            clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', data['slug'])
            filename = f"{clean_slug}_{data['lang']}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            post = frontmatter.Post(data['body_content'], **data['frontmatter'])
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            append_history(term)
            return True
        except Exception as e:
            time.sleep(2)
    return False

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
            
    target_list = term_list[:LIMIT]
    print(f"🚀 Parallel Processing Start: {len(target_list)} items with {MAX_WORKERS} workers.")

    # [핵심] ThreadPoolExecutor로 병렬 실행
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_single_term, target_list), total=len(target_list)))

    success_count = sum(1 for r in results if r)
    print(f"🏁 Done! Success: {success_count} / Total: {len(target_list)}")

if __name__ == "__main__":
    main()