import os
import time
import frontmatter
import google.generativeai as genai
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor # 병렬 처리를 위한 라이브러리
from tqdm import tqdm # 진행 상황을 보기 위한 라이브러리

# 1. 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found.")
    exit()

WIKI_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
genai.configure(api_key=GEMINI_API_KEY)

# 멀티스레드 환경에서는 모델 객체를 함수 안에서 생성하거나 설정을 공유합니다.
MODEL_NAME = 'gemini-2.0-flash'

def translate_via_ai(title, summary, tags, content):
    """Gemini를 사용하여 번역 수행"""
    model = genai.GenerativeModel(MODEL_NAME)
    tags_str = ", ".join(tags)

    prompt = f"""
    You are an expert K-POP translator. 
    Translate the following K-POP Wiki entry from English to Japanese.
    
    [Requirements]
    1. Tone: Friendly, informative, and professional.
    2. Terminology: Use authentic Japanese K-POP fandom slang (e.g., '推し', 'オتا活', '스민').
    3. Formatting: Keep all Markdown headers (##), bold text (**), and lists (-) as they are.
    4. Tags: Translate the tags into natural Japanese keywords.

    ---
    TITLE: {title}
    SUMMARY: {summary}
    TAGS: {tags_str}
    CONTENT: 
    {content}
    ---

    [Output Format]
    TITLE_START: [Translated Title] (Korean Term)
    SUMMARY_START: [Translated Summary]
    TAGS_START: [Comma separated tags]
    BODY_START:
    [Translated Markdown Body]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        new_title = text.split("TITLE_START:")[1].split("SUMMARY_START:")[0].strip()
        new_summary = text.split("SUMMARY_START:")[1].split("TAGS_START:")[0].strip()
        new_tags_raw = text.split("TAGS_START:")[1].split("BODY_START:")[0].strip()
        new_body = text.split("BODY_START:")[1].strip()
        new_tags = [t.strip() for t in new_tags_raw.split(',') if t.strip()]
        
        return new_title, new_summary, new_tags, new_body
    except Exception as e:
        return None, None, None, None

def process_file(filename):
    """개별 파일을 처리하는 함수 (스레드에서 실행됨)"""
    basename = filename.replace("_en.md", "").replace(".md", "")
    ja_filename = f"{basename}_ja.md"
    ja_filepath = os.path.join(WIKI_DIR, ja_filename)

    if os.path.exists(ja_filepath):
        return f"⚪ Skip: {filename}"

    try:
        en_path = os.path.join(WIKI_DIR, filename)
        post = frontmatter.load(en_path, encoding='utf-8')

        new_title, new_summary, new_tags, new_body = translate_via_ai(
            post.metadata.get('title', ''),
            post.metadata.get('summary', ''),
            post.metadata.get('tags', []),
            post.content
        )

        if new_title and new_body:
            ja_post = frontmatter.Post(new_body)
            ja_post.metadata = post.metadata.copy()
            ja_post.metadata.update({
                'title': new_title,
                'summary': new_summary,
                'tags': new_tags,
                'lang': 'ja',
                'date': time.strftime("%Y-%m-%d")
            })

            with open(ja_filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(ja_post))
            
            return f"✅ Done: {ja_filename}"
        else:
            return f"❌ Fail: {filename}"

    except Exception as e:
        return f"❌ Error: {filename} ({str(e)})"

def process_translation():
    print(f"🚀 Starting Parallel Translation using {MODEL_NAME}...")
    
    if not os.path.isdir(WIKI_DIR):
        print(f"❌ Directory not found: {WIKI_DIR}")
        return

    # 대상 파일 리스트업
    files = [f for f in os.listdir(WIKI_DIR) if f.endswith(".md") and "_ja" not in f and "_zh" not in f and "_ko" not in f]
    
    if not files:
        print("모든 파일이 이미 번역되었거나 대상 파일이 없습니다.")
        return

    print(f"Found {len(files)} files to translate.")

    # [핵심] ThreadPoolExecutor를 사용하여 병렬 처리
    # max_workers: 동시에 돌릴 작업 수 (Gemini 유료 계정이면 10-20, 무료면 5 정도 추천)
    MAX_WORKERS = 5 
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 진행 상황을 tqdm으로 표시
        results = list(tqdm(executor.map(process_file, files), total=len(files)))

    # 결과 요약 출력 (선택 사항)
    # for res in results:
    #     print(res)

    print("\n🏁 All translation processes finished!")

if __name__ == "__main__":
    # tqdm 설치 필요: pip install tqdm
    process_translation()