# app/__init__.py

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_compress import Compress
from flask import Response
from app.gemini_client import translate_to_kpop_slang
import os
import json
import frontmatter
import markdown
import datetime 

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

# [중요] 그룹 데이터 로드 함수
def load_groups():
    current_file_path = os.path.abspath(__file__)
    app_dir = os.path.dirname(current_file_path)
    json_path = os.path.join(app_dir, 'data', 'groups.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ [디버깅] JSON 읽기 실패: {e}")
            return {}
    else:
        return {}

# [수정] 최근 위키 포스트 로드 함수 (기본값 파라미터는 유지하되 호출부에서 변경)
def load_recent_wiki_posts(count=4):
    wiki_dir = os.path.join(app.root_path, 'content', 'wiki')
    posts = []
    if os.path.exists(wiki_dir):
        for filename in os.listdir(wiki_dir):
            if filename.endswith('.md'):
                try:
                    filepath = os.path.join(wiki_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)
                        post_date = post.get('date', datetime.date.min)
                        if isinstance(post_date, str):
                            post_date = datetime.datetime.strptime(post_date, '%Y-%m-%d').date()

                        posts.append({
                            'title': post.get('title', 'No Title'),
                            'summary': post.get('summary', ''),
                            'slug': filename.replace('.md', ''),
                            'category': post.get('category', 'General'),
                            'date': post_date
                        })
                except Exception as e:
                    print(f"Error processing wiki file {filename}: {e}")

    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts[:count]


# ==========================================
# 라우트 설정
# ==========================================

@app.route('/')
def index():
    lang = request.args.get('lang', 'ja')
    
    all_groups = load_groups() 
    translations = load_translations()
    
    dicts_dir = os.path.join(app.root_path, 'data', 'dicts')
    available_groups = {}
    
    if os.path.exists(dicts_dir):
        for group_name, group_info in all_groups.items():
            dict_file = f"{group_name}.json"
            if os.path.exists(os.path.join(dicts_dir, dict_file)):
                available_groups[group_name] = group_info
    
    # 1. [수정] 위키 포스트 8개 로드
    recent_wiki = load_recent_wiki_posts(8)

    # 2. [추가] 통계 데이터 계산
    group_count = len(available_groups) - 1 # 'General' 제외하려면 -1, 포함하려면 그대로
    if group_count < 0: group_count = 0
    
    # 날짜: 오늘 날짜 혹은 특정 날짜 지정 (여기서는 오늘 날짜로 자동 설정)
    last_update = datetime.date.today().strftime("%Y.%m.%d")

    return render_template(
        'index.html', 
        group_data=available_groups,
        translations=translations, 
        current_lang=lang,
        recent_wiki=recent_wiki,
        group_count=group_count,   # 템플릿 전달
        last_update=last_update    # 템플릿 전달
    )

# ... (나머지 라우트 코드는 기존과 동일하게 유지) ...
@app.route('/guide')
def guide():
    translations = load_translations()
    return render_template('guide.html', translations=translations)

@app.route('/privacy')
def privacy():
    translations = load_translations()
    return render_template('privacy.html', translations=translations)

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    base_url = "https://nomujoa.com"
    pages = [
        {'loc': base_url + '/', 'priority': '1.0'},
        {'loc': base_url + '/guide', 'priority': '0.8'},
        {'loc': base_url + '/privacy', 'priority': '0.5'},
        {'loc': base_url + '/wiki', 'priority': '0.9'}
    ]
    
    wiki_dir = os.path.join(app.root_path, 'content', 'wiki')
    if os.path.exists(wiki_dir):
        for filename in os.listdir(wiki_dir):
            if filename.endswith('.md'):
                slug = filename.replace('.md', '')
                pages.append({
                    'loc': f"{base_url}/wiki/{slug}",
                    'priority': '0.7'
                })

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml += '  <url>\n'
        xml += f'    <loc>{page["loc"]}</loc>\n'
        xml += '    <changefreq>daily</changefreq>\n'
        xml += f'    <priority>{page["priority"]}</priority>\n'
        xml += '  </url>\n'
    xml += '</urlset>'
    
    return Response(xml, mimetype='application/xml')

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
    if request.path.startswith('/static'):
        response.cache_control.max_age = 86400
        response.cache_control.public = True
    return response

@app.route('/wiki')
def wiki_list():
    wiki_dir = os.path.join(app.root_path, 'content', 'wiki')
    posts = []
    
    if os.path.exists(wiki_dir):
        for filename in os.listdir(wiki_dir):
            if filename.endswith('.md'):
                with open(os.path.join(wiki_dir, filename), 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    posts.append({
                        'title': post['title'],
                        'summary': post['summary'],
                        'slug': filename.replace('.md', ''),
                        'tags': post.get('tags', [])
                    })
    
    posts.sort(key=lambda p: p.get('date', datetime.date.min), reverse=True)
    return render_template('wiki_list.html', posts=posts)

@app.route('/wiki/<slug>')
def wiki_detail(slug):
    filepath = os.path.join(app.root_path, 'content', 'wiki', f'{slug}.md')
    if not os.path.exists(filepath):
        return "Page not found", 404
        
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
        content_html = markdown.markdown(post.content)
        
    return render_template('wiki_detail.html', post=post, content=content_html)