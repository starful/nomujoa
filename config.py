import os
from dotenv import load_dotenv

# 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    # 환경 변수 (트위터 키 제거됨)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    PORT = os.getenv('PORT', 8080)

    # 데이터 경로
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    APP_DIR = os.path.join(BASE_DIR, 'app')
    
    # 세부 경로
    DICTS_DIR = os.path.join(DATA_DIR, 'dicts')
    RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
    WIKI_DIR = os.path.join(APP_DIR, 'content', 'wiki') # 구조 변경에 따라 유동적
    
    GROUPS_FILE = os.path.join(DATA_DIR, 'groups.json')
    TRANSLATIONS_FILE = os.path.join(DATA_DIR, 'translations.json')
    MAPPING_FILE = os.path.join(DATA_DIR, 'phrase_mapping.json')