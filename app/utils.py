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

# app/utils.py

def load_recent_wiki_posts(count=4, lang='en', category_filter=None):
    """
    category_filter: 문자열 또는 리스트를 받을 수 있게 수정
    """
    posts = []
    if os.path.exists(Config.WIKI_DIR):
        for filename in os.listdir(Config.WIKI_DIR):
            if filename.endswith('.md'):
                basename, _ = os.path.splitext(filename)
                parts = basename.rsplit('_', 1)
                slug = basename
                post_lang = 'en'
                
                if len(parts) == 2 and parts[1] in ['ja', 'ko', 'zh', 'en']:
                    slug = parts[0]
                    post_lang = parts[1]

                if post_lang == lang:
                    try:
                        filepath = os.path.join(Config.WIKI_DIR, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            post = frontmatter.load(f)
                            
                            post_category = post.get('category', 'General')
                            
                            # [수정] 필터가 리스트인 경우와 문자열인 경우 모두 대응
                            if category_filter:
                                if isinstance(category_filter, list):
                                    if post_category not in category_filter:
                                        continue
                                elif post_category != category_filter:
                                    continue

                            posts.append({
                                'title': post.get('title', 'No Title'),
                                'summary': post.get('summary', ''),
                                'slug': slug,
                                'lang': post_lang,
                                'category': post_category,
                                'date': post.get('date', datetime.date.min)
                            })
                    except Exception as e:
                        print(f"Error processing wiki {filename}: {e}")

    posts.sort(key=lambda p: p['date'] if isinstance(p['date'], datetime.date) else datetime.date.min, reverse=True)
    return posts[:count] if count and count > 0 else posts