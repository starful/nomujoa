import os
import json
import random
import tweepy
from dotenv import load_dotenv

# ==========================================
# 1. 설정
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # nomujoa/
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # 이제 이건 안 쓰지만 남겨둡니다.
DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')

# 트위터 API 키
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ==========================================
# 2. 함수 정의
# ==========================================
def get_random_slang():
    if not os.path.exists(DICT_DIR): return None
    files = [f for f in os.listdir(DICT_DIR) if f.endswith('.json')]
    if not files: return None
    
    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    try:
        with open(os.path.join(DICT_DIR, random_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        keys = list(data.keys())
        random_member = random.choice(keys)
        intent_keys = list(data[random_member].keys())
        if not intent_keys: return None
        random_intent = random.choice(intent_keys)
        slang_list = data[random_member][random_intent]
        if not slang_list: return None
        slang_item = random.choice(slang_list)
        
        korean = slang_item.get('text', '') if isinstance(slang_item, dict) else slang_item
        meaning_ja = slang_item.get('meaning_ja', '') if isinstance(slang_item, dict) else "K-POP Slang"
        
        if not meaning_ja:
            meaning_ja = slang_item.get('meaning', 'K-POP Slang') if isinstance(slang_item, dict) else "K-POP Slang"

        return {
            "group": group_name,
            "korean": korean,
            "meaning_ja": meaning_ja
        }
    except: return None

def post_to_twitter():
    print("🚀 텍스트 전용 봇 실행")
    slang = get_random_slang()
    if not slang:
        print("❌ 포스팅할 단어 없음")
        return

    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        
        # [수정] 텍스트만으로 구성 (이모지로 가독성 높이기)
        tweet_text = (
            f"📚 Today's K-POP Word 📚\n\n"
            f"🇰🇷 오늘의 단어: {slang['korean']}\n"
            f"🇯🇵 意味(의미): {slang['meaning_ja']}\n\n"
            f"👇 이 단어로 나만의 응원 슬로건을 만들어보세요!\n"
            f"(Create your own cheering slogan with this word!)\n\n"
            f"🔗 https://nomujoa.com\n\n"
            f"#KPOP #韓国語 #推し活 #{slang['group']} #Nomujoa"
        )
        
        client.create_tweet(text=tweet_text)
        print(f"🎉 텍스트 포스팅 성공! 내용: {slang['korean']}")
        
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    post_to_twitter()