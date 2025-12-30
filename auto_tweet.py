import os
import json
import random
import tweepy
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# ==========================================
# 1. 경로 설정 및 디버깅 (매우 중요)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, 'app', 'data', 'dicts')
FONT_DIR = os.path.join(BASE_DIR, 'app', 'static', 'fonts')

print("-" * 60)
print(f"📍 [DEBUG] 스크립트 실행 위치: {BASE_DIR}")
print(f"📂 [DEBUG] 데이터 폴더 경로: {DICT_DIR}")

# 데이터 폴더 확인
if os.path.exists(DICT_DIR):
    files = os.listdir(DICT_DIR)
    print(f"✅ [DEBUG] 데이터 폴더 발견! 파일 개수: {len(files)}개")
    print(f"📄 [DEBUG] 파일 목록(일부): {files[:5]}...")
else:
    print("❌ [DEBUG] 데이터 폴더가 없습니다!!! (GitHub에 안 올라간 상태)")
    # 상위 폴더 구조 확인
    app_path = os.path.join(BASE_DIR, 'app')
    if os.path.exists(app_path):
        print(f"   👉 'app' 폴더 내용: {os.listdir(app_path)}")
        data_path = os.path.join(app_path, 'data')
        if os.path.exists(data_path):
            print(f"   👉 'app/data' 폴더 내용: {os.listdir(data_path)}")
    else:
        print("   👉 'app' 폴더조차 없습니다.")
print("-" * 60)

# ==========================================
# 2. 트위터 API 키 로드
# ==========================================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def get_random_slang():
    """JSON 파일에서 랜덤하게 단어 하나를 뽑습니다."""
    if not os.path.exists(DICT_DIR):
        print("❌ 데이터 폴더가 없어서 단어를 못 뽑습니다.")
        return None

    files = [f for f in os.listdir(DICT_DIR) if f.endswith('.json')]
    if not files: 
        print("❌ JSON 파일이 하나도 없습니다.")
        return None
    
    random_file = random.choice(files)
    group_name = random_file.replace('.json', '')
    
    try:
        with open(os.path.join(DICT_DIR, random_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 데이터 구조에 따라 랜덤 선택
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
                "korean": slang_item.get('text', ''),
                "meaning": slang_item.get('meaning', 'Love you'),
                "meaning_ja": slang_item.get('meaning_ja', slang_item.get('meaning', ''))
            }
        else:
            return {
                "group": group_name,
                "korean": slang_item,
                "meaning": "K-POP Slang",
                "meaning_ja": "推し活用語"
            }
    except Exception as e:
        print(f"⚠️ 데이터 읽기 실패: {e}")
        return None

def create_image(slang_data):
    """Pillow를 사용해 심플한 이미지를 생성합니다."""
    # 캔버스 생성 (1080x1080)
    colors = [(255, 209, 220), (204, 229, 255), (255, 250, 205), (229, 204, 255)]
    bg_color = random.choice(colors)
    img = Image.new('RGB', (1080, 1080), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 로드 (없으면 기본 폰트 사용 - 한글 깨질 수 있음)
    font_large = None
    font_small = None
    
    # 폰트 파일명 후보 (업로드한 파일명에 맞춰 수정 가능)
    font_candidates = ['NotoSansKR-Bold.otf', 'NotoSansKR-Bold.ttf', 'malgun.ttf']
    
    font_path = None
    if os.path.exists(FONT_DIR):
        for f in font_candidates:
            path = os.path.join(FONT_DIR, f)
            if os.path.exists(path):
                font_path = path
                break
    
    try:
        if font_path:
            print(f"✅ 폰트 로드 성공: {font_path}")
            font_large = ImageFont.truetype(font_path, 100)
            font_small = ImageFont.truetype(font_path, 50)
        else:
            print("⚠️ 폰트 파일을 못 찾았습니다. 기본 폰트를 사용합니다. (한글 깨짐 주의)")
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ 폰트 로딩 에러: {e}")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 텍스트 그리기 (간단 중앙 정렬)
    # W, H = 1080, 1080
    # _, _, w, h = draw.textbbox((0, 0), slang_data['korean'], font=font_large)
    # draw.text(((W-w)/2, (H-h)/2 - 50), slang_data['korean'], font=font_large, fill="black")
    
    # 좌표 직접 지정 (안전빵)
    draw.text((100, 350), f"{slang_data['korean']}", fill=(0,0,0), font=font_large)
    draw.text((100, 550), f"Mean: {slang_data['meaning_ja']}", fill=(80,80,80), font=font_small)
    draw.text((100, 800), "Nomujoa.com", fill=(100,100,100), font=font_small)
    
    img_path = "temp_tweet_img.png"
    img.save(img_path)
    return img_path

def post_to_twitter():
    print("🚀 트위터 봇 시작")
    
    if not API_KEY:
        print("❌ API Key가 환경변수에 없습니다. (GitHub Secrets 확인 필요)")
        return

    slang = get_random_slang()
    if not slang:
        print("❌ 포스팅할 단어를 찾지 못해 종료합니다.")
        return

    # 이미지 생성
    try:
        img_path = create_image(slang)
    except Exception as e:
        print(f"❌ 이미지 생성 중 에러: {e}")
        return
    
    # 트위터 업로드
    try:
        client = tweepy.Client(
            consumer_key=API_KEY, consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
        )
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)

        # 1. 이미지 업로드 (v1.1 API 사용)
        media = api.media_upload(filename=img_path)
        print("✅ 이미지 업로드 완료")
        
        # 2. 텍스트 작성
        text = f"""📚 Today's K-POP Word

🇰🇷 {slang['korean']}
🇯🇵 {slang['meaning_ja']}

AIで推し活ボードを作ろう! (Make your slogan)
👇
🔗 https://nomujoa.com

#KPOP #韓国語 #推し活 #{slang['group']} #Nomujoa"""

        # 3. 게시물 등록 (v2 API 사용)
        client.create_tweet(text=text, media_ids=[media.media_id])
        print(f"🎉 트위터 포스팅 성공! 내용: {slang['korean']}")
        
    except Exception as e:
        print(f"❌ 트위터 전송 실패: {e}")
    finally:
        # 임시 이미지 삭제
        if os.path.exists(img_path):
            os.remove(img_path)

if __name__ == "__main__":
    post_to_twitter()