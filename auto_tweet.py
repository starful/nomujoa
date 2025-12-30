import os
import json
import random
import tweepy
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 1. 설정 및 데이터 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')
FONT_PATH = os.path.join(BASE_DIR, 'app', 'static', 'fonts', 'NotoSansKR-Bold.otf') # 폰트 경로 확인 필요!

# X API 인증 정보 (환경변수에서 가져옴)
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def get_random_slang():
    """JSON 파일에서 랜덤하게 단어 하나를 뽑습니다."""
    files = [f for f in os.listdir(DICT_DIR) if f.endswith('.json')]
    if not files: return None
    
    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    with open(os.path.join(DICT_DIR, random_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 데이터 구조에 따라 랜덤 선택 (All 또는 멤버)
    keys = list(data.keys()) # All, MemberNames...
    random_member = random.choice(keys)
    
    intent_keys = list(data[random_member].keys())
    if not intent_keys: return None
    random_intent = random.choice(intent_keys)
    
    slang_list = data[random_member][random_intent]
    if not slang_list: return None
    
    slang_item = random.choice(slang_list)
    
    # dict 형태인지 str 형태인지 확인
    if isinstance(slang_item, dict):
        return {
            "group": group_name,
            "korean": slang_item['text'],
            "meaning": slang_item.get('meaning', 'Love you'),
            "meaning_ja": slang_item.get('meaning_ja', '')
        }
    else:
        return {
            "group": group_name,
            "korean": slang_item,
            "meaning": "K-POP Slang",
            "meaning_ja": "推し活用語"
        }

def create_image(slang_data):
    """Pillow를 사용해 심플한 이미지를 생성합니다."""
    # 캔버스 생성 (인스타/트위터용 1080x1080)
    # 배경색 랜덤 (파스텔톤)
    colors = [(255, 209, 220), (204, 229, 255), (255, 250, 205), (229, 204, 255)]
    bg_color = random.choice(colors)
    img = Image.new('RGB', (1080, 1080), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 로드 (서버에 폰트 파일이 없으면 기본 폰트로 대체될 수 있음)
    try:
        # 폰트 파일이 없으면 에러가 나므로, 프로젝트에 폰트 파일을 포함시키거나 경로를 맞춰야 함
        # 여기서는 예시로 기본값 처리
        font_large = ImageFont.truetype(FONT_PATH, 100) 
        font_small = ImageFont.truetype(FONT_PATH, 50)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 텍스트 그리기 (중앙 정렬 계산은 생략하고 단순 배치)
    draw.text((100, 400), slang_data['korean'], fill=(0,0,0), font=font_large)
    draw.text((100, 600), f"Meaning: {slang_data['meaning_ja']}", fill=(80,80,80), font=font_small)
    draw.text((100, 800), "Nomujoa.com", fill=(100,100,100), font=font_small)
    
    img_path = "temp_tweet_img.png"
    img.save(img_path)
    return img_path

def post_to_twitter():
    if not API_KEY:
        print("❌ API Key가 없습니다.")
        return

    slang = get_random_slang()
    if not slang:
        print("❌ 단어를 찾지 못했습니다.")
        return

    # 이미지 생성
    img_path = create_image(slang)
    
    # 트위터 업로드
    client = tweepy.Client(
        consumer_key=API_KEY, consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
    )
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth)

    # 1. 이미지 업로드
    media = api.media_upload(filename=img_path)
    
    # 2. 텍스트 작성
    text = f"""📚 Today's K-POP Word

🇰🇷 {slang['korean']}
🇯🇵 {slang['meaning_ja']}

AIで推し活ボードを作ろう! (Make your slogan)
👇
🔗 https://nomujoa.com

#KPOP #韓国語 #推し活 #{slang['group']} #Nomujoa"""

    # 3. 게시물 등록
    client.create_tweet(text=text, media_ids=[media.media_id])
    print(f"✅ 포스팅 성공: {slang['korean']}")
    
    # 임시 이미지 삭제
    os.remove(img_path)

if __name__ == "__main__":
    post_to_twitter()