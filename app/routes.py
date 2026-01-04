# app/routes.py
from flask import Blueprint, render_template, request, jsonify, send_from_directory, Response
from app.gemini_client import translate_to_kpop_slang
from app.utils import load_groups, load_translations, load_available_groups, load_recent_wiki_posts
from config import Config
import markdown
import os
import frontmatter
import datetime

# Blueprint 정의
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    lang = request.args.get('lang', 'ja')
    
    # 유틸 함수 사용하여 데이터 로드
    all_groups = load_groups() 
    translations = load_translations()
    available_groups = load_available_groups(all_groups)
    recent_wiki = load_recent_wiki_posts(8)

    # 통계 계산
    group_count = len(available_groups) - 1
    if group_count < 0: group_count = 0
    last_update = datetime.date.today().strftime("%Y.%m.%d")

    return render_template(
        'index.html', 
        group_data=available_groups,
        translations=translations, 
        current_lang=lang,
        recent_wiki=recent_wiki,
        group_count=group_count,
        last_update=last_update
    )

@main_bp.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    user_text = data.get('text', '')
    
    if not user_text:
        return jsonify({'result': []})

    variations = translate_to_kpop_slang(
        user_text, 
        data.get('group', 'General'), 
        data.get('member', 'All'), 
        data.get('src_lang', 'ja'), 
        force_refresh=data.get('is_refresh', False)
    )
    return jsonify({'result': variations})

@main_bp.route('/wiki')
def wiki_list():
    posts = load_recent_wiki_posts(None) # 전체 로드
    return render_template('wiki_list.html', posts=posts)

@main_bp.route('/wiki/<slug>')
def wiki_detail(slug):
    filepath = os.path.join(Config.WIKI_DIR, f'{slug}.md')
    if not os.path.exists(filepath):
        return "Page not found", 404
    
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
        content_html = markdown.markdown(post.content)
        
    return render_template('wiki_detail.html', post=post, content=content_html)

@main_bp.route('/guide')
def guide():
    translations = load_translations()
    return render_template('guide.html', translations=translations)

@main_bp.route('/privacy')
def privacy():
    translations = load_translations()
    return render_template('privacy.html', translations=translations)

@main_bp.route('/robots.txt')
def robots():
    # static 폴더 경로를 Config나 current_app에서 가져오는 방식 권장
    return send_from_directory(os.path.join(Config.APP_DIR, 'static'), 'robots.txt')

@main_bp.route('/sitemap.xml')
def sitemap():
    base_url = "https://nomujoa.com"
    pages = [
        {'loc': base_url + '/', 'priority': '1.0'},
        {'loc': base_url + '/guide', 'priority': '0.8'},
        {'loc': base_url + '/privacy', 'priority': '0.5'},
        {'loc': base_url + '/wiki', 'priority': '0.9'}
    ]
    
    # Wiki 파일 목록 순회
    if os.path.exists(Config.WIKI_DIR):
        for filename in os.listdir(Config.WIKI_DIR):
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