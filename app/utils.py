# app/utils.py
import json
import os
import datetime
import frontmatter
from config import Config
import re

def load_translations():
    """번역 파일 로드"""
    try:
        with open(Config.TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def load_groups():
    """그룹 정보 로드"""
    if os.path.exists(Config.GROUPS_FILE):
        try:
            with open(Config.GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading groups: {e}")
            return {}
    return {}

def load_available_groups(all_groups):
    """dicts 폴더에 데이터가 있는 그룹만 필터링"""
    available = {}
    if os.path.exists(Config.DICTS_DIR):
        for group_name, group_info in all_groups.items():
            dict_file = f"{group_name}.json"
            if os.path.exists(os.path.join(Config.DICTS_DIR, dict_file)):
                available[group_name] = group_info
    return available

def load_recent_wiki_posts(count=4, lang='en'):
    """
    [수정됨] 특정 언어의 Wiki 포스트를 로드합니다.
    파일명 규칙: slug_lang.md (예: olkon_ja.md). 언어 접미사가 없으면 'en'으로 간주합니다.
    """
    posts = []
    if os.path.exists(Config.WIKI_DIR):
        for filename in os.listdir(Config.WIKI_DIR):
            if filename.endswith('.md'):
                basename, _ = os.path.splitext(filename) # olkon_ja
                
                parts = basename.rsplit('_', 1)
                slug = basename
                post_lang = 'en' # 기본 언어
                
                # 파일명에 언어 코드가 있는지 확인 (예: _ja, _zh)
                if len(parts) == 2 and parts[1] in ['ja', 'ko', 'zh', 'en']:
                    slug = parts[0]
                    post_lang = parts[1]

                # 요청된 언어와 일치하는 파일만 처리
                if post_lang == lang:
                    try:
                        filepath = os.path.join(Config.WIKI_DIR, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            post = frontmatter.load(f)
                            
                            post_date = post.get('date', datetime.date.min)
                            if isinstance(post_date, str):
                                post_date = datetime.datetime.strptime(post_date, '%Y-%m-%d').date()

                            posts.append({
                                'title': post.get('title', 'No Title'),
                                'summary': post.get('summary', ''),
                                'slug': slug, # 언어 코드가 제거된 순수 slug
                                'lang': post_lang,
                                'category': post.get('category', 'General'),
                                'date': post_date,
                                'tags': post.get('tags', [])
                            })
                    except Exception as e:
                        print(f"Error processing wiki {filename}: {e}")

    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts[:count] if count and count > 0 else posts