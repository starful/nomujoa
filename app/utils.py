# app/utils.py
import json
import os
import datetime
import frontmatter
from config import Config

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

def load_recent_wiki_posts(count=4):
    """Wiki 포스트 로드 (app/content/wiki 경로 사용)"""
    posts = []
    if os.path.exists(Config.WIKI_DIR):
        for filename in os.listdir(Config.WIKI_DIR):
            if filename.endswith('.md'):
                try:
                    filepath = os.path.join(Config.WIKI_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)
                        
                        # 날짜 처리
                        post_date = post.get('date', datetime.date.min)
                        if isinstance(post_date, str):
                            post_date = datetime.datetime.strptime(post_date, '%Y-%m-%d').date()

                        posts.append({
                            'title': post.get('title', 'No Title'),
                            'summary': post.get('summary', ''),
                            'slug': filename.replace('.md', ''),
                            'category': post.get('category', 'General'),
                            'date': post_date,
                            'tags': post.get('tags', [])
                        })
                except Exception as e:
                    print(f"Error processing wiki {filename}: {e}")

    # 날짜순 정렬
    posts.sort(key=lambda p: p['date'], reverse=True)
    
    # count가 None이면 전체 반환, 숫자면 슬라이싱
    return posts[:count] if count else posts