import csv
import json
import os
import time
import re
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

# 경로 설정
INPUT_CSV = os.path.join(BASE_DIR, "data", "raw", "kpop_combined_terms.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
LOG_DIR = os.path.join(BASE_DIR, "app", "logs")
HISTORY_FILE = os.path.join(LOG_DIR, f"group_wiki_history_{TARGET_LANG}.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 2. 유틸리티 함수
# ==========================================

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def append_history(term):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{term}\n")

def parse_markdown_response(text, term, category, lang):
    # [수정] AI가 응답에 포함시킨 마크다운 강조 기호(**) 등을 제거하는 로직 추가
    text = text.replace("**", "") 

    # 제목 추출
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else term

    # 슬러그 추출 (URL용)
    slug_match = re.search(r"Slug:\s*(.+)", text)
    slug = slug_match.group(1).strip() if slug_match else re.sub(r'[^a-zA-Z0-9-]', '', term.replace(" ", "-")).lower()
    
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
            "category": "Combined", # 카테고리를 'Combined'로 고정해서 저장하면 관리가 훨씬 쉽습니다.
            "tags": tags,
            "summary": summary,
            "date": time.strftime("%Y-%m-%d"),
            "lang": lang
        },
        "body_content": body_content
    }

def get_combined_wiki_info(term, category, lang):
    lang_names = {'ko': 'Korean', 'ja': 'Japanese', 'zh': 'Chinese', 'en': 'English'}
    target_lang_name = lang_names.get(lang, 'Korean')

    # SEO 최적화 프롬프트: '그룹명+단어'에 특화된 상세 가이드 요청
def get_combined_wiki_info(term, category, lang):
    lang_names = {'ko': 'Korean', 'ja': 'Japanese', 'zh': 'Chinese', 'en': 'English'}
    target_lang_name = lang_names.get(lang, 'English')

    prompt = f"""
    You are a world-class K-POP Journalist and SEO Specialist.
    Topic to write: "{term}"
    Target Language: {target_lang_name}
    Category: {category}

    [STRICT RULES for Title and Content]
    1. TITLE: You must translate the Title into natural {target_lang_name}. 
       - Good Example (Target English): The Meaning and Origin of BTS Borahae (I Purple You)
       - NEVER use Korean characters in the Title field for English, Japanese, or Chinese targets.
    
    2. SUMMARY: Write exactly 2 sentences in {target_lang_name}. No markdown bolding (**).
    
    3. SLUG: Create a SEO-friendly English slug. 
       - Example: bts-borahae-meaning-origin
    
    4. BODY: Write a long-form article (over 1500 characters) in {target_lang_name}. Use Markdown headers (##).

    [Response Format]
    Title: [Translated Title in {target_lang_name}]
    Slug: [english-slug]
    Summary: [Summary in {target_lang_name}]
    Tags: tag1, tag2, tag3
    ---BODY START---
    ## 1. Introduction
    (Overview of the topic and its importance in K-POP culture)
    
    ## 2. History and Context
    (Detailed background info about the group and how this term originated or is used specifically by them)
    
    ## 3. Real-world Examples and Fan Culture
    (Explain specific incidents, memes, or how fans use this on social media)
    
    ## 4. Slogan and Cheering Ideas
    (Suggest 3-5 creative slogan phrases for this specific group/term that fans can make on our site)
    
    ## 5. FAQ
    (3 Common questions and answers regarding this topic)
    ---BODY END---

    [Instruction]
    - Content should be at least 1500 characters long for better SEO ranking.
    - Use professional yet engaging tone.
    - Focus on the synergy between the Group and the Term.
    """

    for i in range(3):
        try:
            res = model.generate_content(prompt)
            return parse_markdown_response(res.text, term, category, lang)
        except Exception as e:
            print(f"   ⚠️ API Retry ({i+1}/3)... {e}")
            time.sleep(5)
    return None

def save_to_md(data):
    clean_slug = data['slug']
    filename = f"{clean_slug}_{data['lang']}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    post = frontmatter.Post(data['body_content'], **data['frontmatter'])
    
    try:
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
                term_list.append(row)
            
    print(f"🚀 Combined Wiki Generation Start: {len(term_list)} items pending.")
    
    count = 0
    target_list = term_list[:LIMIT]

    for item in tqdm(target_list):
        data = get_combined_wiki_info(item['term'], item['category'], TARGET_LANG)
        if data:
            filename = save_to_md(data)
            if filename:
                append_history(item['term'])
                count += 1
                time.sleep(1) # API 부하 방지
        else:
            print(f"   ❌ Failed: {item['term']}")

    print(f"🏁 Done! Processed {count} items.")

if __name__ == "__main__":
    main()