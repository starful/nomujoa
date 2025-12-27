import os
import json
import random
import logging
import google.generativeai as genai
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("Gemini API Key Missing")

BASE_DIR = os.path.dirname(__file__)
DICT_DIR = os.path.join(BASE_DIR, 'data/dicts')
MAPPING_FILE = os.path.join(BASE_DIR, 'data/phrase_mapping.json')

DICT_CACHE = {}
PHRASE_MAPPINGS = {}

if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        PHRASE_MAPPINGS = json.load(f).get("mappings", {})

if os.path.exists(DICT_DIR):
    for filename in os.listdir(DICT_DIR):
        if filename.endswith(".json"):
            group_name = filename.replace(".json", "")
            with open(os.path.join(DICT_DIR, filename), 'r', encoding='utf-8') as f:
                DICT_CACHE[group_name] = json.load(f)

def translate_to_kpop_slang(text, group_name, member_name, source_lang='ja', force_refresh=False):
    clean_text = text.split(' (')[0]
    intent_key = PHRASE_MAPPINGS.get(clean_text)

    # 1. JSON 데이터 활용 (API 비용 0)
    if not force_refresh and intent_key and group_name in DICT_CACHE:
        group_data = DICT_CACHE[group_name]
        target_list = []

        if member_name in group_data and intent_key in group_data[member_name]:
            target_list = group_data[member_name][intent_key]
        elif 'All' in group_data and intent_key in group_data['All']:
            target_list = group_data['All'][intent_key]

        if target_list:
            selected = random.sample(target_list, min(len(target_list), 5))
            if len(selected) < 5:
                selected = selected * (5 // len(selected) + 1)
                selected = selected[:5]
            
            results = []
            for item in selected:
                if isinstance(item, dict):
                    # [핵심 로직] 언어에 맞는 뜻 선택
                    slang_text = item.get('text', '')
                    if source_lang == 'ja':
                        # 일본어 선택 시 -> meaning_ja (없으면 text)
                        meaning = item.get('meaning_ja', item.get('meaning', text))
                    else:
                        # 그 외(영어 등) -> meaning_en (없으면 text)
                        meaning = item.get('meaning_en', item.get('meaning', text))
                    
                    results.append({'text': slang_text, 'meaning': meaning})
                else:
                    # 구버전 데이터 (문자열)
                    results.append({'text': item, 'meaning': text})
            
            return results

    # 2. AI 호출 (새로운 멘트 생성 - API 비용 발생)
    return call_gemini_api(text, group_name, member_name, source_lang)

def call_gemini_api(text, group_name, member_name, source_lang):
    if not api_key: return [{'text': "API Key Error", 'meaning': "Error"}]

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        target_info = f"group '{group_name}'"
        if member_name and member_name != 'All':
            target_info = f"member '{member_name}' of group '{group_name}'"

        lang_map = {'ja': 'Japanese', 'en': 'English', 'ko': 'Korean', 'zh': 'Chinese'}
        input_lang_name = lang_map.get(source_lang, 'English') # 기본값 영어로 변경
        
        # 실시간 생성 시 프롬프트
        prompt = f"""
        ROLE: K-POP fan creating a slogan.
        TARGET: {target_info}
        INPUT: "{text}" (Language: {input_lang_name})
        
        TASK: Generate 5 Korean slang phrases.
        CRITICAL: Provide the meaning in {input_lang_name}.
        
        FORMAT: Korean Phrase | Meaning in {input_lang_name}
        
        OUTPUT:
        Option1 | Meaning1
        Option2 | Meaning2
        ...
        """
        
        response = model.generate_content(prompt)
        lines = [line.strip() for line in response.text.split('\n') if '|' in line]
        
        results = []
        for line in lines[:5]:
            parts = line.split('|')
            if len(parts) >= 2:
                results.append({'text': parts[0].strip(), 'meaning': parts[1].strip()})
            else:
                results.append({'text': line, 'meaning': text})
        
        # 5개 채우기
        while len(results) < 5:
             fallback = member_name if member_name != 'All' else group_name
             results.append({'text': fallback, 'meaning': text})
                
        return results[:5]
    
    except Exception as e:
        logger.error(f"API Error: {e}")
        return [{'text': "Error", 'meaning': "Try again"}]