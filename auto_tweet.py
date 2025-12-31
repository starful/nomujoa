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

DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')
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
    
    # [수정] 에러를 숨기지 않고, 정확한 원인을 출력하도록 변경
    try:
        filepath = os.path.join(DICT_DIR, random_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            print(f"   ⚠️ 경고: {random_file} 파일이 비어있습니다.")
            return None

        keys = list(data.keys())
        if not keys:
            print(f"   ⚠️ 경고: {random_file} 파일에 멤버 키가 없습니다.")
            return None
        random_member = random.choice(keys)
        
        if not data[random_member]:
            print(f"   ⚠️ 경고: {random_file} 파일의 '{random_member}' 항목이 비어있습니다.")
            return None

        intent_keys = list(data[random_member].keys())
        if not intent_keys:
             print(f"   ⚠️ 경고: {random_file} 파일의 '{random_member}' 항목에 인텐트가 없습니다.")
             return None
        random_intent = random.choice(intent_keys)
        
        slang_list = data[random_member][random_intent]
        if not slang_list:
             print(f"   ⚠️ 경고: {random_file}의 '{random_member}'-'{random_intent}' 목록이 비어있습니다.")
             return None
        slang_item = random.choice(slang_list)
        
        korean = slang_item.get('text', '') if isinstance(slang_item, dict) else slang_item
        meaning_ja = slang_item.get('meaning_ja', 'K-POP Slang') if isinstance(slang_item, dict) else "K-POP Slang"
        
        if not meaning_ja and isinstance(slang_item, dict):
            meaning_ja = slang_item.get('meaning', 'K-POP Slang')

        return {
            "group": group_name,
            "korean": korean,
            "meaning_ja": meaning_ja
        }
    except Exception as e:
        # [핵심] 어떤 에러가 났는지 출력!
        print(f"❌ 단어 추출 중 심각한 에러 발생: {e}")
        print(f"   (파일: {random_file})")
        return None

def post_to_twitter():
    print("🚀 텍스트 전용 봇 실행")
    slang = get_random_slang()
    if not slang:
        print("❌ 포스팅할 단어 없음")
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