import os
import json
import random
import tweepy
from dotenv import load_dotenv

# ==========================================
# 1. 설정 (경로 계산 로직 수정!)
# ==========================================
# 이 스크립트 파일(auto_tweet.py)이 있는 폴더가 바로 프로젝트 루트입니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 정확한 데이터 폴더 경로
DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')

# 트위터 API 키
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ==========================================
# 2. 함수 정의 (디버깅 강화)
# ==========================================
def get_random_slang():
    # [수정] 모든 실패 경로에 print문 추가
    if not os.path.exists(DICT_DIR):
        print(f"❌ [DEBUG] 데이터 폴더를 찾을 수 없습니다! 경로: {DICT_DIR}")
        return None
        
    files = [f for f in os.listdir(DICT_DIR) if f.endswith('.json')]
    if not files:
        print(f"✅ [DEBUG] 폴더는 찾았지만, 안에 JSON 파일이 없습니다. 경로: {DICT_DIR}")
        return None
    
    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    try:
        filepath = os.path.join(DICT_DIR, random_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            print(f"   ⚠️ 경고: {random_file} 파일이 비어있습니다.")
            return None

        keys = list(data.keys())
        if not keys: return None
        random_member = random.choice(keys)
        
        if not data[random_member]: return None
        intent_keys = list(data[random_member].keys())
        if not intent_keys: return None
        random_intent = random.choice(intent_keys)
        
        slang_list = data[random_member][random_intent]
        if not slang_list: return None
        slang_item = random.choice(slang_list)
        
        korean = slang_item.get('text', '') if isinstance(slang_item, dict) else slang_item
        meaning_ja = slang_item.get('meaning_ja', 'K-POP Slang') if isinstance(slang_item, dict) else "K-POP Slang"
        
        if not meaning_ja and isinstance(slang_item, dict):
            meaning_ja = slang_item.get('meaning', 'K-POP Slang')

        return { "group": group_name, "korean": korean, "meaning_ja": meaning_ja }
    except Exception as e:
        print(f"❌ 단어 추출 중 에러: {e} (파일: {random_file})")
        return None

def post_to_twitter():
    print("🚀 텍스트 전용 봇 실행")
    slang = get_random_slang()
    if not slang or not slang.get('korean'): # 단어가 비어있는 경우도 체크
        print("❌ 포스팅할 단어를 찾지 못했습니다. (get_random_slang 반환값 확인 필요)")
        return

    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        
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