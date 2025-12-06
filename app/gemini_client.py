import os
import json
import random
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# [개선] 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("Gemini API Key가 설정되지 않았습니다.")

# 1. 데이터 로드
BASE_DIR = os.path.dirname(__file__)
DICT_DIR = os.path.join(BASE_DIR, 'data/dicts')
MAPPING_FILE = os.path.join(BASE_DIR, 'data/phrase_mapping.json')

DICT_CACHE = {}
PHRASE_MAPPINGS = {}

# 매핑 파일 로드
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        PHRASE_MAPPINGS = json.load(f).get("mappings", {})

# 그룹별 JSON 로드
if os.path.exists(DICT_DIR):
    for filename in os.listdir(DICT_DIR):
        if filename.endswith(".json"):
            group_name = filename.replace(".json", "")
            with open(os.path.join(DICT_DIR, filename), 'r', encoding='utf-8') as f:
                DICT_CACHE[group_name] = json.load(f)

def translate_to_kpop_slang(text, group_name, member_name, source_lang='ja', force_refresh=False):
    # 1. 인텐트(Key) 파악
    clean_text = text.split(' (')[0] # 괄호 제거
    intent_key = PHRASE_MAPPINGS.get(clean_text)

    # 2. JSON 데이터 검색 (새로고침 아닐 때)
    if not force_refresh and intent_key and group_name in DICT_CACHE:
        group_data = DICT_CACHE[group_name]
        target_list = []

        if member_name in group_data and intent_key in group_data[member_name]:
            target_list = group_data[member_name][intent_key]
        elif 'All' in group_data and intent_key in group_data['All']:
            target_list = group_data['All'][intent_key]

        if target_list:
            if len(target_list) < 5:
                return target_list * 5
            return random.sample(target_list, 5)

    # 3. AI 호출 (데이터 없거나 새로고침 시)
    return call_gemini_api(text, group_name, member_name, source_lang)

def call_gemini_api(text, group_name, member_name, source_lang):
    if not api_key: 
        logger.error("API Key Missing")
        return ["API Key Error"]

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        target_info = f"group '{group_name}'"
        if member_name and member_name != 'All':
            target_info = f"member '{member_name}' of group '{group_name}'"

        lang_map = {'ja': 'Japanese', 'en': 'English', 'ko': 'Korean', 'zh': 'Chinese'}
        input_lang_name = lang_map.get(source_lang, 'Japanese')

        concepts = ["Trendy Meme", "Emotional", "Powerful", "Cute", "Wit"]
        chosen_concept = random.choice(concepts)

        prompt = f"""
        ROLE: Korean K-POP fan creating a concert slogan.
        TARGET: {target_info}
        INPUT LANGUAGE: {input_lang_name}
        INPUT TEXT: "{text}"
        VIBE: {chosen_concept}

        ✅ RULES:
        1. **KOREAN ONLY**: Output MUST be in Korean (Hangul).
        2. **FANDOM SLANG**: Use specific nicknames and memes.
        3. **NATURAL**: Don't translate directly. Make it sound like a real fan.

        📝 GENERATE 5 OPTIONS:
        1. [Name/Nickname]
        2. [Cute]
        3. [Emotional]
        4. [Powerful]
        5. [Wit]

        OUTPUT FORMAT:
        Option1|Option2|Option3|Option4|Option5
        (Separator '|', No numbering)
        """
        
        generation_config = genai.types.GenerationConfig(temperature=0.9)
        response = model.generate_content(prompt, generation_config=generation_config)
        
        result_text = response.text.strip()
        variations = [v.strip() for v in result_text.split('|')]
        while len(variations) < 5: variations.append(variations[0])
            
        return variations[:5]
    
    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        fallback = member_name if member_name != 'All' else group_name
        return [fallback, f"사랑해 {fallback}", f"우리 {fallback}", f"평생 {fallback}", f"갓{fallback}"]