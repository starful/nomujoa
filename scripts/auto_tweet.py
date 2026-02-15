# scripts/auto_tweet.py
import os
import json
import random
import tweepy
import logging
import google.generativeai as genai

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 1. 환경 변수 로드
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICTS_DIR = os.path.join(BASE_DIR, 'data', 'dicts')

# 3. AI 설정
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_twitter_conn_v2():
    """트위터 API V2 연결"""
    return tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )

def get_random_slang_data():
    """JSON 파일에서 랜덤 데이터 추출"""
    if not os.path.exists(DICTS_DIR): return None
    files = [f for f in os.listdir(DICTS_DIR) if f.endswith('.json')]
    if not files: return None

    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    with open(os.path.join(DICTS_DIR, random_file), 'r', encoding='utf-8') as f:
        data = json.load(f)

    available_members = list(data.keys())
    if not available_members: return None
    
    random_member = random.choice(available_members)
    member_data = data[random_member]
    intents = list(member_data.keys())
    if not intents: return None
    
    random_intent = random.choice(intents)
    slang_list = member_data[random_intent]
    if not slang_list: return None
    
    final_item = random.choice(slang_list)
    
    if isinstance(final_item, str):
        slang_text = final_item
        # 일본어 의미가 없으면 인텐트 키를 사용
        meaning = random_intent
    else:
        slang_text = final_item.get('text', '')
        # meaning_ja(일본어 뜻) 우선 사용, 없으면 영어 뜻, 없으면 키값
        meaning = final_item.get('meaning_ja', final_item.get('meaning_en', random_intent))

    return {
        "group": group_name,
        "member": random_member if random_member != "All" else group_name,
        "slang": slang_text,
        "meaning": meaning
    }

def generate_premium_tweet(item):
    """Gemini를 사용하여 일본어 트윗 생성"""
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key missing")
        return None

    model = genai.GenerativeModel('gemini-2.0-flash')

    # [수정됨] 일본어 타겟 프롬프트
    prompt = f"""
    You are a popular K-POP influencer on Japanese Twitter (X).
    Write an engaging, detailed post introducing a Korean fandom slang term to Japanese fans.
    
    [Input Data]
    - Group: {item['group']}
    - Member: {item['member']}
    - Slang (Korean): "{item['slang']}"
    - Meaning: "{item['meaning']}"

    [Requirements]
    1. **Language**: Write ONLY in **Japanese**. (Use natural tone like '〜だよ', '〜しか勝たん', '尊い').
    2. **Structure**:
       - **Headline**: Catchy title with emojis (e.g., 📢 今日の韓国語!).
       - **Explanation**: Explain the meaning and nuance deeply. Why is this phrase used? Is it funny? Emotional?
       - **Pronunciation**: Add Katakana reading (e.g., 読み方：サランヘ).
       - **Usage**: A short conversation example (Fan A vs Fan B).
       - **CTA**: Encourage them to make a slogan board at 'nomujoa.com' for concerts (イルコン/本国コン).
    3. **Tags**: #KPOP #{item['group']} #韓国語勉強 #推し活 #Nomujoa
    
    Output the tweet text directly.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI Generation Failed: {e}")
        return None

def main():
    if not API_KEY or not GEMINI_API_KEY:
        logger.error("❌ 필수 키(Twitter/Gemini)가 누락되었습니다.")
        return

    # 1. 데이터 가져오기
    item = get_random_slang_data()
    if not item:
        logger.error("❌ 데이터 추출 실패")
        return

    logger.info(f"Target Item: {item['group']} - {item['slang']}")

    # 2. AI로 트윗 내용 작성
    rich_text = generate_premium_tweet(item)
    
    # [수정됨] AI 실패 시 기본 문구도 일본어로 변경
    if not rich_text:
        rich_text = (
            f"📢 今日のK-POP韓国語: {item['group']}\n\n"
            f"✨ {item['slang']}\n"
            f"意味: {item['meaning']}\n\n"
            f"👇 自分だけのスローガンを作ろう！\n"
            f"🔗 nomujoa.com\n\n"
            f"#{item['group']} #KPOP #韓国語 #推し活"
        )

    # 3. 트윗 전송
    try:
        client = get_twitter_conn_v2()
        response = client.create_tweet(text=rich_text)
        logger.info(f"✅ Premium Tweet Sent! ID: {response.data['id']}")
        print(rich_text) # 로그 확인용
    except Exception as e:
        logger.error(f"❌ Tweet Failed: {e}")

if __name__ == "__main__":
    main()