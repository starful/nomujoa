# scripts/auto_tweet.py
import os
import json
import random
import tweepy
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 1. 환경 변수에서 키 가져오기 (GitHub Secrets에 설정되어 있어야 함)
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# 2. 데이터 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICTS_DIR = os.path.join(BASE_DIR, 'data', 'dicts')

def get_twitter_conn_v2():
    """트위터 API V2 연결 (Client 사용)"""
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    return client

def get_random_slang():
    """dicts 폴더에서 랜덤한 아이돌과 슬랭을 하나 뽑음"""
    if not os.path.exists(DICTS_DIR):
        logger.error(f"❌ 데이터 폴더를 찾을 수 없습니다: {DICTS_DIR}")
        return None

    # JSON 파일 목록 가져오기
    files = [f for f in os.listdir(DICTS_DIR) if f.endswith('.json')]
    if not files:
        logger.error("❌ JSON 파일이 없습니다.")
        return None

    # 1. 랜덤 파일(그룹) 선택
    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    with open(os.path.join(DICTS_DIR, random_file), 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 멤버 또는 All 중에서 랜덤 선택
    # 데이터 구조: {"MemberName": {"Intent": [{"text": "...", "meaning": "..."}, ...]}}
    available_members = list(data.keys())
    if not available_members: return None
    
    random_member = random.choice(available_members)
    member_data = data[random_member]
    
    # 3. 인텐트(표현) 중 랜덤 선택
    intents = list(member_data.keys())
    if not intents: return None
    
    random_intent = random.choice(intents)
    slang_list = member_data[random_intent]
    
    # 4. 최종 슬랭 선택
    if not slang_list: return None
    final_item = random.choice(slang_list)
    
    # 단순 문자열인 경우와 딕셔너리인 경우 처리
    if isinstance(final_item, str):
        slang_text = final_item
        meaning = random_intent # 의미가 없으면 인텐트 키를 사용
    else:
        slang_text = final_item.get('text', '')
        # 영어 의미 우선, 없으면 키값
        meaning = final_item.get('meaning_en', final_item.get('meaning', random_intent))

    return {
        "group": group_name,
        "member": random_member if random_member != "All" else group_name,
        "slang": slang_text,
        "meaning": meaning,
        "intent": random_intent
    }

def main():
    if not API_KEY:
        logger.error("❌ 트위터 API 키가 설정되지 않았습니다.")
        return

    try:
        # 데이터 뽑기
        item = get_random_slang()
        if not item:
            logger.error("❌ 트윗할 데이터를 찾지 못했습니다.")
            return

        # 트윗 텍스트 작성 (해시태그 및 홍보 문구 포함)
        tweet_text = (
            f"📢 Today's K-POP Slang: {item['group']}\n\n"
            f"💬 Word: {item['slang']}\n"
            f"📚 Meaning: {item['meaning']}\n\n"
            f"Create your slogan here! 👇\n"
            f"🔗 https://nomujoa.com\n\n"
            f"#{item['group']} #KPOP #KoreanSlang #Nomujoa"
        )

        # 트위터 전송
        client = get_twitter_conn_v2()
        response = client.create_tweet(text=tweet_text)
        
        logger.info(f"✅ 트윗 전송 성공! ID: {response.data['id']}")
        logger.info(f"내용: {tweet_text}")

    except Exception as e:
        logger.error(f"❌ 트윗 전송 실패: {e}")

if __name__ == "__main__":
    main()