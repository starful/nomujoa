import os
import json
import random
import tweepy
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 1. 설정 및 디버깅
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')
FONT_DIR = os.path.join(BASE_DIR, 'app', 'static', 'fonts')

# 트위터 API 키 로드
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

print("-" * 60)
print(f"📍 [DEBUG] 실행 위치: {BASE_DIR}")
print(f"📂 [DEBUG] 데이터 경로: {DICT_DIR}")
print(f"🎨 [DEBUG] 폰트 경로: {FONT_DIR}")
print("-" * 60)

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
    except Exception as e:
        print(f"❌ 데이터 로드 에러: {e}")
        return None

def create_image(slang_data):
    colors = [(255, 228, 225), (240, 248, 255), (255, 250, 205), (230, 230, 250), (224, 255, 255)]
    bg_color = random.choice(colors)
    img = Image.new('RGB', (1080, 1080), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # ----------------------------------------------------
    # [수정된 폰트 로직] 한국어(KR) 폰트를 1순위로!
    # ----------------------------------------------------
    font_candidates = ['NotoSansKR-Bold.otf', 'NotoSansKR-Bold.ttf', 'NotoSansJP-Bold.ttf']
    font_path = None
    
    if os.path.exists(FONT_DIR):
        for f in font_candidates:
            path = os.path.join(FONT_DIR, f)
            if os.path.exists(path):
                font_path = path
                print(f"✅ 폰트 선택됨: {f}")
                break
    
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, 100)
            desc_font = ImageFont.truetype(font_path, 50)
            footer_font = ImageFont.truetype(font_path, 40)
        else:
            print("⚠️ 폰트 파일을 찾지 못했습니다.")
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ 폰트 로드 중 에러: {e}")
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    W, H = 1080, 1080
    
    text_kr = slang_data['korean']
    _, _, w_kr, h_kr = draw.textbbox((0, 0), text_kr, font=title_font)
    draw.text(((W-w_kr)/2, H/2 - 150), text_kr, fill=(30,30,30), font=title_font)
    
    text_ja = f"{slang_data['meaning_ja']}"
    _, _, w_ja, h_ja = draw.textbbox((0, 0), text_ja, font=desc_font)
    draw.text(((W-w_ja)/2, H/2 + 20), text_ja, fill=(100,100,100), font=desc_font)
    
    text_footer = "Nomujoa.com"
    _, _, w_f, h_f = draw.textbbox((0, 0), text_footer, font=footer_font)
    draw.text(((W-w_f)/2, H - 150), text_footer, fill=(150,150,150), font=footer_font)
    
    img_path = "temp_tweet_img.png"
    img.save(img_path)
    return img_path

def post_to_twitter():
    print("🚀 트위터 봇 실행 시작")
    slang = get_random_slang()
    if not slang:
        print("❌ 포스팅할 단어를 찾지 못했습니다.")
        return
    img_path = create_image(slang)
    
    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)
        media = api.media_upload(filename=img_path)
        print("✅ 이미지 업로드 완료")
        
        tweet_text = (
            f"📚 Today's K-POP Word\n\n"
            f"🇰🇷 {slang['korean']}\n"
            f"🇯🇵 {slang['meaning_ja']}\n\n"
            f"AIで推し活ボードを作ろう! (Make your slogan)\n"
            f"👇\n"
            f"🔗 https://nomujoa.com\n\n"
            f"#KPOP #韓国語 #推し活 #{slang['group']} #Nomujoa"
        )
        
        client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        print(f"🎉 포스팅 성공! 내용: {slang['korean']}")
        
    except Exception as e:
        print(f"❌ 전송 실패: {e}")
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

if __name__ == "__main__":
    post_to_twitter()