# app/routes.py
from flask import Blueprint, render_template, request, jsonify, send_from_directory, Response
from app.gemini_client import translate_to_kpop_slang
from app.utils import load_groups, load_translations, load_available_groups, load_recent_wiki_posts
from config import Config
import markdown
import os
import frontmatter
import datetime
import re

main_bp = Blueprint('main', __name__)

# [참고] lang 파라미터가 없는 기본 접속은 'ja'로 리디렉션 할 수 있습니다. (선택사항)
# @main_bp.route('/')
# def root():
#     return redirect('/ja')

@main_bp.route('/')
def index():
    # URL 파라미터 또는 쿠키에서 언어 설정을 가져옵니다.
    lang = request.args.get('lang', 'ja') 
    all_groups = load_groups() 
    translations = load_translations()
    available_groups = load_available_groups(all_groups)
    
    # [수정] 메인 페이지의 트렌딩 용어도 언어에 맞게 표시
    recent_wiki = load_recent_wiki_posts(count=8, lang=lang)

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
    # ... (이하 로직 동일)
    user_text = data.get('text', '')
    if not user_text:
        return jsonify({'result': []})
    variations = translate_to_kpop_slang(
        user_text, data.get('group', 'General'), data.get('member', 'All'), 
        data.get('src_lang', 'ja'), force_refresh=data.get('is_refresh', False)
    )
    return jsonify({'result': variations})

# [수정됨] 언어 코드(lang)를 URL에 포함
@main_bp.route('/<lang>/wiki')
def wiki_list(lang):
    posts = load_recent_wiki_posts(count=None, lang=lang) # 전체 로드
    return render_template('wiki_list.html', posts=posts, lang=lang)

# [수정됨] 언어 코드(lang)를 URL에 포함하고, 파일 로직 변경
@main_bp.route('/<lang>/wiki/<slug>')
def wiki_detail(lang, slug):
    # 1. 올바른 언어의 파일명 조합
    filename = f'{slug}_{lang}.md'
    filepath = os.path.join(Config.WIKI_DIR, filename)

    # 2. _en.md 또는 .md 형태의 기본 영어 파일 fallback 로직
    if not os.path.exists(filepath):
        # _en.md 파일 시도
        en_filepath_suffix = os.path.join(Config.WIKI_DIR, f'{slug}_en.md')
        # 접미사 없는 .md 파일 시도
        en_filepath_nosuffix = os.path.join(Config.WIKI_DIR, f'{slug}.md')
        if os.path.exists(en_filepath_suffix):
             filepath = en_filepath_suffix
        elif os.path.exists(en_filepath_nosuffix):
             filepath = en_filepath_nosuffix
        else:
            return "Page not found", 404
            
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
        
    # 3. hreflang 태그를 위한 다른 언어 버전 찾기
    available_langs = []
    for fn in os.listdir(Config.WIKI_DIR):
        if fn.startswith(f'{slug}.md') or fn.startswith(f'{slug}_'):
            base, _ = os.path.splitext(fn)
            parts = base.rsplit('_', 1)
            if len(parts) == 2 and parts[0] == slug:
                available_langs.append(parts[1])
            elif base == slug:
                available_langs.append('en')

    # 4. 자동 내부 링크 로직 (URL에 lang 포함하도록 수정)
    all_posts_in_lang = load_recent_wiki_posts(count=None, lang=lang)
    linked_content = post.content
    
    keywords = []
    for other_post in all_posts_in_lang:
        if other_post['slug'] != slug:
            title = other_post['title']
            slug_to_link = other_post['slug']
            keywords.append((title, slug_to_link))
            parts = re.findall(r'[\w\s]+', title)
            for part in parts:
                part = part.strip()
                if len(part) > 1:
                    keywords.append((part, slug_to_link))

    keywords.sort(key=lambda x: len(x[0]), reverse=True)
    
    processed_keywords = list(dict.fromkeys(keywords))

    for keyword, link_slug in processed_keywords:
        pattern = re.compile(r'\b({})\b'.format(re.escape(keyword)), re.IGNORECASE)
        # URL에 현재 언어 코드를 포함하여 링크 생성
        replacement = r'[\1](/{}/wiki/{})'.format(lang, link_slug)
        # ... (이하 링크 생성 로직은 이전과 유사하게 유지)
        temp_content = ""
        last_pos = 0
        for match in pattern.finditer(linked_content):
            start, end = match.span()
            pre_char = linked_content[max(0, start-2):start]
            if '[' in pre_char or ']' in pre_char: # 이미 링크의 일부인지 간단히 확인
                temp_content += linked_content[last_pos:end]
            else:
                temp_content += linked_content[last_pos:start]
                temp_content += replacement.replace(r'\1', match.group(1))
            last_pos = end
        temp_content += linked_content[last_pos:]
        linked_content = temp_content
        
    content_html = markdown.markdown(linked_content)
        
    return render_template('wiki_detail.html', post=post, content=content_html, lang=lang, available_langs=available_langs)

# ... (guide, privacy, robots, sitemap 등 이하 라우트는 동일)
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
    pages = [{'loc': base_url + '/', 'priority': '1.0'}] 
    # ...
    # [수정] 사이트맵도 다국어 URL을 포함하도록 개선
    for lang_code in ['en', 'ja', 'ko', 'zh']:
        pages.append({'loc': f"{base_url}/{lang_code}/wiki", 'priority': '0.9'})
        if os.path.exists(Config.WIKI_DIR):
            for filename in os.listdir(Config.WIKI_DIR):
                if filename.endswith(f'_{lang_code}.md') or (lang_code == 'en' and '_' not in filename and filename.endswith('.md')):
                    slug = os.path.splitext(filename)[0].replace(f'_{lang_code}', '')
                    pages.append({'loc': f"{base_url}/{lang_code}/wiki/{slug}",'priority': '0.7'})

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