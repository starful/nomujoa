import csv
import json
import os
import time
import re
from concurrent.futures import ThreadPoolExecutor # 병렬 처리 라이브러리
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

# [설정] 생성할 언어 및 개수
TARGET_LANG = "en"  # ko, ja, en, zh 중 선택
LIMIT = 50          # 한 번 실행 시 생성할 개수
MAX_WORKERS = 5     # 동시에 생성할 개수 (무료계정 3~5, 유료 10~15 추천)

# 경로 설정
INPUT_CSV = os.path.join(BASE_DIR, "data", "raw", "kpop_combined_terms.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
LOG_DIR = os.path.join(BASE_DIR, "app", "logs")
HISTORY_FILE = os.path.join(LOG_DIR, f"group_wiki_history_{TARGET_LANG}.txt")

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
    # AI 응답 클리닝
    text = text.replace("**", "") 

    # 제목 추출
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else term

    # 슬러그 추출
    slug_match = re.search(r"Slug:\s*(.+)", text)
    raw_slug = slug_match.group(1).strip() if slug_match else term
    slug = re.sub(r'[^a-zA-Z0-9-]', '', raw_slug.replace(" ", "-")).lower()
    
    # 요약 추출
    summary_match = re.search(r"Summary:\s*(.+)", text)
    summary = summary_match.group(1).strip() if summary_match else ""

    # 태그 추출
    tags_match = re.search(r"Tags:\s*(.+)", text)
    tags = [t.strip() for t in tags_match.group(1).split(',')] if tags_match else ["K-POP", category]

    # 본문 추출
    body_parts = text.split("---BODY START---")
    body_content = body_parts[1].strip() if len(body_parts) > 1 else text
    body_content = body_content.replace("---BODY END---", "").strip()

    return {
        "slug": slug,
        "lang": lang,
        "frontmatter": {
            "title": title,
            "category": "Combined",
            "tags": tags,
            "summary": summary,
            "date": time.strftime("%Y-%m-%d"),
            "lang": lang
        },
        "body_content": body_content
    }

def process_item(item):
    """개별 아이템을 처리하는 워커 함수"""
    term = item['term']
    category = item['category']
    lang = TARGET_LANG
    
    # 스레드별 모델 독립 선언
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    lang_names = {'ko': 'Korean', 'ja': 'Japanese', 'zh': 'Chinese', 'en': 'English'}
    target_lang_name = lang_names.get(lang, 'English')

    prompt = f"""
    You are a world-class K-POP Journalist and SEO Specialist.
    Topic to write: "{term}"
    Target Language: {target_lang_name}
    Category: {category}

    [STRICT RULES for Title and Content]
    1. TITLE: You must translate the Title into natural {target_lang_name}. 
       - NEVER use Korean characters in the Title field.
    
    2. SUMMARY: Write exactly 2 sentences in {target_lang_name}. No markdown bolding (**).
    
    3. SLUG: Create a SEO-friendly English slug. 
    
    4. BODY: Write a long-form article (over 1500 characters) in {target_lang_name}. Use Markdown headers (##).

    [Response Format]
    Title: [Translated Title]
    Slug: [english-slug]
    Summary: [Summary]
    Tags: tag1, tag2, tag3
    ---BODY START---
    ## 1. Introduction
    ...
    ## 2. History and Context
    ...
    ## 3. Real-world Examples and Fan Culture
    ...
    ## 4. Slogan and Cheering Ideas
    ...
    ## 5. FAQ
    ---BODY END---
    """

    for i in range(2): # 재시도 2회
        try:
            res = model.generate_content(prompt)
            data = parse_markdown_response(res.text, term, category, lang)
            
            # 파일 저장
            filename = f"{data['slug']}_{data['lang']}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            post = frontmatter.Post(data['body_content'], **data['frontmatter'])
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            append_history(term)
            return True
        except Exception as e:
            time.sleep(5)
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
                term_list.append(row)
            
    target_list = term_list[:LIMIT]
    print(f"🚀 Combined Wiki Parallel Generation: {len(target_list)} items, {MAX_WORKERS} workers.")
    
    # [핵심] 병렬 처리 실행
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_item, target_list), total=len(target_list)))

    success_count = sum(1 for r in results if r)
    print(f"🏁 Done! Success: {success_count} / Total: {len(target_list)}")

if __name__ == "__main__":
    main()