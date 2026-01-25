import os
import sys
import time
import frontmatter
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found.")
    exit()

WIKI_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def translate_via_ai(title, summary, tags, content):
    """Gemini를 사용하여 제목, 요약, 태그, 본문을 일본어로 번역"""
    
    # 태그 리스트를 문자열로 변환
    tags_str = ", ".join(tags)

    prompt = f"""
    You are an expert K-POP translator. 
    Translate the following K-POP Wiki entry from English to Japanese.
    
    [Requirements]
    1. Tone: Friendly, informative, and professional (like a specialized wiki).
    2. Terminology: Use authentic Japanese K-POP fandom slang (e.g., '推し', 'オタ活', 'スミン').
    3. Formatting: Keep all Markdown headers (##), bold text (**), and lists (-) exactly as they are.
    4. Tags: Translate the tags into natural Japanese keywords used in K-POP social media.

    ---
    TITLE (to translate): {title}
    SUMMARY (to translate): {summary}
    TAGS (to translate): {tags_str}
    CONTENT (to translate): 
    {content}
    ---

    [Output Format]
    Return ONLY the translated content in this format:
    TITLE_START: [Translated Title] (Korean Term)
    SUMMARY_START: [Translated Summary]
    TAGS_START: [Comma separated translated tags]
    BODY_START:
    [Translated Markdown Body]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 결과 파싱
        new_title = text.split("TITLE_START:")[1].split("SUMMARY_START:")[0].strip()
        new_summary = text.split("SUMMARY_START:")[1].split("TAGS_START:")[0].strip()
        new_tags_raw = text.split("TAGS_START:")[1].split("BODY_START:")[0].strip()
        new_body = text.split("BODY_START:")[1].strip()
        
        # 태그를 다시 리스트로 변환
        new_tags = [t.strip() for t in new_tags_raw.split(',') if t.strip()]
        
        return new_title, new_summary, new_tags, new_body
    except Exception as e:
        print(f"   ⚠️ Translation error: {e}")
        return None, None, None, None

def process_translation():
    print("🚀 Starting English to Japanese Wiki Translation (including Tags)...")
    
    if not os.path.isdir(WIKI_DIR):
        print(f"❌ Directory not found: {WIKI_DIR}")
        return

    # 영어 파일들 스캔
    files = [f for f in os.listdir(WIKI_DIR) if f.endswith(".md") and "_ja" not in f and "_zh" not in f]
    
    print(f"Found {len(files)} English files to translate.\n")

    for filename in files:
        basename = filename.replace("_en.md", "").replace(".md", "")
        ja_filename = f"{basename}_ja.md"
        ja_filepath = os.path.join(WIKI_DIR, ja_filename)

        if os.path.exists(ja_filepath):
            print(f"⚪ Skipping '{filename}' (Japanese version already exists).")
            continue

        print(f"▶️ Translating: {filename}...")
        
        try:
            # 영어 파일 로드
            en_path = os.path.join(WIKI_DIR, filename)
            post = frontmatter.load(en_path, encoding='utf-8')

            # AI 번역 실행
            new_title, new_summary, new_tags, new_body = translate_via_ai(
                post.metadata.get('title', ''),
                post.metadata.get('summary', ''),
                post.metadata.get('tags', []),
                post.content
            )

            if new_title and new_body:
                # 새로운 일본어 포스트 객체 생성
                ja_post = frontmatter.Post(new_body)
                ja_post.metadata = post.metadata.copy()
                ja_post.metadata.update({
                    'title': new_title,
                    'summary': new_summary,
                    'tags': new_tags,  # 번역된 태그 적용
                    'lang': 'ja',
                    'date': time.strftime("%Y-%m-%d")
                })

                # 저장
                with open(ja_filepath, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(ja_post))
                
                print(f"✅ Created: {ja_filename} with translated tags.")
                time.sleep(2) 
            else:
                print(f"❌ Failed to translate: {filename}")

        except Exception as e:
            print(f"❌ Error processing '{filename}': {e}")

    print("\n🏁 Translation process finished!")

if __name__ == "__main__":
    process_translation()