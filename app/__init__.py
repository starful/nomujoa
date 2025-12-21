from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_compress import Compress
from app.gemini_client import translate_to_kpop_slang
import os
import json # [중요] json 모듈 추가

app = Flask(__name__)

# [추가] Gzip 압축 활성화
Compress(app)


# [추가] 번역 데이터 로드 함수
def load_translations():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'data', 'translations.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

# ==========================================
# [중요] 그룹 데이터 로드 함수 (groups.json 읽기)
# ==========================================
def load_groups():
    # 1. 현재 파일(__init__.py)의 위치 확인
    current_file_path = os.path.abspath(__file__)
    app_dir = os.path.dirname(current_file_path) # .../app
    
    # 2. 목표로 하는 json 파일 경로
    json_path = os.path.join(app_dir, 'data', 'groups.json')
    
    print("-" * 50)
    print(f"🕵️‍♀️ [디버깅] 현재 파일 위치: {current_file_path}")
    print(f"📂 [디버깅] JSON 파일 찾는 곳: {json_path}")
    
    # 3. 파일 존재 여부 확인
    if os.path.exists(json_path):
        print("✅ [디버깅] 파일이 존재합니다!")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📊 [디버깅] 로드된 그룹 개수: {len(data)}개")
                print(f"👀 [디버깅] 데이터 미리보기: {list(data.keys())[:3]}...")
                return data
        except Exception as e:
            print(f"❌ [디버깅] 파일은 있는데 읽기 실패 (JSON 문법 오류 등): {e}")
            return {}
    else:
        print("❌ [디버깅] 파일이 없습니다!!! 경로를 다시 확인하세요.")
        # 혹시 파일이 엉뚱한데 있는지 확인하기 위해 현재 폴더 목록 출력
        print(f"❓ [디버깅] '{os.path.join(app_dir, 'data')}' 폴더 안의 파일들: ")
        try:
            print(os.listdir(os.path.join(app_dir, 'data')))
        except:
            print("   (data 폴더 자체가 없는 것 같습니다)")
        return {}
    print("-" * 50)

# ==========================================
# 라우트 설정
# ==========================================

@app.route('/')
def index():
    # 1. URL 파라미터에서 언어 가져오기 (기본값: ja)
    lang = request.args.get('lang', 'ja')
    
    group_data = load_groups()
    translations = load_translations()
    
    # 2. current_lang 변수를 추가해서 HTML로 전달
    return render_template(
        'index.html', 
        group_data=group_data, 
        translations=translations, 
        current_lang=lang  # <--- 이 부분이 추가되어야 합니다!
    )

@app.route('/guide')
def guide():
    translations = load_translations() # [추가]
    return render_template('guide.html', translations=translations)

@app.route('/privacy')
def privacy():
    translations = load_translations() # [추가]
    return render_template('privacy.html', translations=translations)

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    user_text = data.get('text', '')
    group_name = data.get('group', 'General')
    member_name = data.get('member', 'All')
    source_lang = data.get('src_lang', 'ja')
    is_refresh = data.get('is_refresh', False)
    
    if not user_text:
        return jsonify({'result': []})

    variations = translate_to_kpop_slang(
        user_text, group_name, member_name, source_lang, force_refresh=is_refresh
    )
    
    return jsonify({'result': variations})

@app.after_request
def add_header(response):
    # 정적 파일(이미지, CSS, JS)은 1일(86400초) 동안 캐시
    if request.path.startswith('/static'):
        response.cache_control.max_age = 86400
        response.cache_control.public = True
    return response