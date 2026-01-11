# app/routes.py
from flask import Blueprint, render_template, request, jsonify, send_from_directory, Response
from app.gemini_client import translate_to_kpop_slang
from app.utils import load_groups, load_translations, load_available_groups, load_recent_wiki_posts
from config import Config
import markdown
import os
import frontmatter
import datetime
import re # 정규식을 위해 re 모듈을 import 합니다.

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

# =================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼ 이 함수가 수정되었습니다 ▼▼▼▼▼▼▼▼▼▼▼▼▼
# =================================================================
@main_bp.route('/wiki/<slug>')
def wiki_detail(slug):
    filepath = os.path.join(Config.WIKI_DIR, f'{slug}.md')
    if not os.path.exists(filepath):
        return "Page not found", 404
    
    # 1. 현재 페이지의 마크다운 파일 로드
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
        
    # 2. 링크로 사용할 모든 위키 페이지 목록 가져오기
    all_posts = load_recent_wiki_posts(None)
    
    # 3. 본문(마크다운 원본)에 다른 위키 페이지 링크 자동 추가
    linked_content = post.content
    
    # 링크 키워드 리스트 생성 (긴 단어가 먼저 교체되도록 정렬)
    keywords = []
    for other_post in all_posts:
        if other_post['slug'] != slug: # 자기 자신을 링크하지 않도록 함
            # "Title (Korean)" 형식의 제목에서 키워드 추출
            # 예: "All Concerts (올콘)" -> ["All Concerts (올콘)", "All Concerts", "올콘"]
            title = other_post['title']
            slug_to_link = other_post['slug']
            
            keywords.append((title, slug_to_link)) # 전체 제목
            
            parts = re.findall(r'[\w\s]+', title) # 괄호 안팎의 단어 추출
            for part in parts:
                part = part.strip()
                if len(part) > 1: # 한 글자 단어는 제외 (오류 방지)
                    keywords.append((part, slug_to_link))

    # 키워드를 길이순으로 내림차순 정렬 (매우 중요!)
    # "All Concerts"가 "Concerts"보다 먼저 링크로 변환되도록 보장
    keywords.sort(key=lambda x: len(x[0]), reverse=True)
    
    # 중복 제거 (성능 향상)
    processed_keywords = []
    seen_keywords = set()
    for keyword, link_slug in keywords:
        if keyword.lower() not in seen_keywords:
            processed_keywords.append((keyword, link_slug))
            seen_keywords.add(keyword.lower())

    for keyword, link_slug in processed_keywords:
        # 정규식을 사용하여 단어 경계가 일치하는 경우에만 링크로 변환
        # 이렇게 하면 이미 링크가 걸린 단어 내부를 또 바꾸지 않습니다.
        pattern = re.compile(r'\b({})\b'.format(re.escape(keyword)), re.IGNORECASE)
        # 마크다운 링크 형식으로 교체: [단어](/wiki/슬러그)
        replacement = r'[\1](/wiki/{})'.format(link_slug)
        
        # 이미 마크다운 링크 형식인 경우는 제외하는 로직 추가
        temp_content = ""
        last_pos = 0
        for match in pattern.finditer(linked_content):
            start, end = match.span()
            # 매칭된 단어 앞뒤에 링크 문법([, ], (, ))이 있는지 확인
            pre_char = linked_content[max(0, start-1)]
            post_char = linked_content[min(len(linked_content)-1, end)]
            if pre_char not in "[]()" and post_char not in "[]()":
                temp_content += linked_content[last_pos:start]
                temp_content += replacement.replace(r'\1', match.group(1))
            else:
                temp_content += linked_content[last_pos:end]
            last_pos = end
        temp_content += linked_content[last_pos:]
        linked_content = temp_content

    # 4. 링크가 추가된 마크다운을 최종적으로 HTML로 변환
    content_html = markdown.markdown(linked_content)
        
    return render_template('wiki_detail.html', post=post, content=content_html)
# =================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲ 수정된 부분 끝 ▲▲▲▲▲▲▲▲▲▲▲▲▲
# =================================================================

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