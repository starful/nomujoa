from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_compress import Compress
from app.gemini_client import translate_to_kpop_slang
import os

app = Flask(__name__)

# [추가] Gzip 압축 활성화 (JS, CSS, HTML 용량을 70% 줄여줌)
Compress(app)

@app.route('/')
def index():
    return render_template('index.html')

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