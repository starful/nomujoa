import os
import time
import frontmatter
import google.generativeai as genai
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# 1. 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found.")
    exit()

WIKI_DIR = os.path.join(BASE_DIR, "app", "content", "wiki")
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.0-flash'

def translate_via_ai(title, summary, tags, content):
    """Gemini를 사용하여 제목, 요약, 태그, 본문을 중국어(간체)로 번역"""
    model = genai.GenerativeModel(MODEL_NAME)
    tags_str = ", ".join(tags)

    prompt = f"""
    You are an expert K-POP translator and a native Simplified Chinese speaker.
    Translate the following K-POP Wiki entry from English to Simplified Chinese (简体中文).
    
    [Requirements]
    1. Tone: Professional, informative, and engaging (Wiki style).
    2. Terminology: Use authentic Chinese K-POP fandom slang (饭圈用语). 
       - e.g., use '本命' or '推' for bias, '应援' for support/cheering, '打榜/刷音源' for streaming.
    3. Formatting: Keep all Markdown headers (##), bold text (**), and lists (-) exactly as they are.
    4. Tags: Translate the tags into natural Chinese keywords used on platforms like Weibo or Xiaohongshu.

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
        
        new_tags = [t.strip() for t in new_tags_raw.split(',') if t.strip()]
        
        return new_title, new_summary, new_tags, new_body
    except Exception:
        return None, None, None, None

def process_file(filename):
    """개별 파일을 처리하는 함수 (스레드에서 실행됨)"""
    basename = filename.replace("_en.md", "").replace(".md", "")
    zh_filename = f"{basename}_zh.md"
    zh_filepath = os.path.join(WIKI_DIR, zh_filename)

    # 이미 중국어 파일이 존재하면 건너뜀
    if os.path.exists(zh_filepath):
        return f"⚪ Skip: {filename}"

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
            # 새로운 중국어 포스트 객체 생성
            zh_post = frontmatter.Post(new_body)
            zh_post.metadata = post.metadata.copy()
            zh_post.metadata.update({
                'title': new_title,
                'summary': new_summary,
                'tags': new_tags,
                'lang': 'zh',
                'date': time.strftime("%Y-%m-%d")
            })

            # 저장
            with open(zh_filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(zh_post))
            return f"✅ Done: {zh_filename}"
        else:
            return f"❌ Fail: {filename}"

    except Exception as e:
        return f"❌ Error: {filename} ({str(e)})"

def process_translation():
    print(f"🚀 Starting Parallel English to Chinese Translation using {MODEL_NAME}...")
    
    if not os.path.isdir(WIKI_DIR):
        print(f"❌ Directory not found: {WIKI_DIR}")
        return

    # 영어 파일들 스캔 (파일명에 _ja, _zh, _ko가 없는 것)
    files = [f for f in os.listdir(WIKI_DIR) if f.endswith(".md") and not any(lang in f for lang in ["_ja", "_zh", "_ko"])]
    
    if not files:
        print("번역할 대상 파일이 없습니다.")
        return

    print(f"Found {len(files)} English files to translate.")

    # 병렬 처리 설정 (MAX_WORKERS 조절 가능)
    MAX_WORKERS = 5
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 진행 상황 표시
        results = list(tqdm(executor.map(process_file, files), total=len(files)))

    print("\n🏁 Chinese translation process finished!")

if __name__ == "__main__":
    process_translation()