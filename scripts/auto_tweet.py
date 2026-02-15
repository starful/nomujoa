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
    """JSON 파일에서 랜덤 데이터 추출 (기존 로직 동일)"""
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
        meaning = random_intent
    else:
        slang_text = final_item.get('text', '')
        meaning = final_item.get('meaning_en', final_item.get('meaning', random_intent))

    return {
        "group": group_name,
        "member": random_member if random_member != "All" else group_name,
        "slang": slang_text,
        "meaning": meaning
    }

def generate_premium_tweet(item):
    """Gemini를 사용하여 X 프리미엄용 고품질 트윗 생성"""
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key missing")
        return None

    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are a professional K-POP culture explainer on X (Twitter).
    Write an engaging, detailed post about this K-POP slang term.
    Target Audience: International K-POP fans (English speakers).
    
    [Input Data]
    - Group: {item['group']}
    - Member: {item['member']}
    - Slang/Phrase: "{item['slang']}"
    - Basic Meaning: "{item['meaning']}"

    [Requirements for the Post]
    1. **Hook**: Start with a catchy headline using emojis.
    2. **Deep Dive**: Explain the nuance. Why do fans use this? Is it cute, funny, or emotional?
    3. **Pronunciation**: Add a "How to say it" section (Romanization).
    4. **Usage Example**: Create a short, fun dialogue (Fan vs. Idol or Fan vs. Fan) showing how to use it.
    5. **Call to Action**: Encourage them to make a slogan at 'nomujoa.com'.
    6. **Format**: Use bullet points and spacing. It can be long (up to 500-1000 characters).
    7. **Tags**: Relevant hashtags.
    
    DO NOT start with "Here is a tweet". Just output the tweet content directly.
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
    
    # AI 실패 시 기본 텍스트로 폴백
    if not rich_text:
        rich_text = (
            f"📢 K-POP Slang of the Day: {item['group']}\n\n"
            f"✨ {item['slang']}\n"
            f"Meaning: {item['meaning']}\n\n"
            f"Create your slogan here! 👉 nomujoa.com\n"
            f"#{item['group']} #KPOP"
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