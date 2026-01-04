import json
import os
import random
import logging
import google.generativeai as genai
from config import Config  # [중요] Config에서 경로와 키를 가져옵니다.

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. API 키 설정
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)
else:
    logger.error("❌ Gemini API Key is MISSING! Check .env or Config.")

# 2. 데이터 로드 (캐싱)
DICT_CACHE = {}
PHRASE_MAPPINGS = {}

# [수정] 경로를 Config 객체에서 가져옴 (하드코딩 제거)
try:
    if os.path.exists(Config.MAPPING_FILE):
        with open(Config.MAPPING_FILE, 'r', encoding='utf-8') as f:
            content = json.load(f)
            PHRASE_MAPPINGS = content.get("mappings", {})
            logger.info(f"✅ Loaded Phrase Mappings: {len(PHRASE_MAPPINGS)} items")
    else:
        logger.warning(f"⚠️ Mapping file not found at: {Config.MAPPING_FILE}")

    if os.path.exists(Config.DICTS_DIR):
        json_files = [f for f in os.listdir(Config.DICTS_DIR) if f.endswith(".json")]
        for filename in json_files:
            group_name = filename.replace(".json", "")
            file_path = os.path.join(Config.DICTS_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    DICT_CACHE[group_name] = json.load(f)
            except Exception as e:
                logger.error(f"❌ Error loading dict {filename}: {e}")
        logger.info(f"✅ Loaded Dictionaries: {len(DICT_CACHE)} groups")
    else:
        logger.warning(f"⚠️ Dicts directory not found at: {Config.DICTS_DIR}")

except Exception as e:
    logger.error(f"❌ Critical Error during initialization: {e}")

# 3. 메인 번역 함수
def translate_to_kpop_slang(text, group_name, member_name, source_lang='ja', force_refresh=False):
    """
    [수정된 로직]
    1. force_refresh(재시도) 여부와 상관없이, JSON 데이터가 있으면 우선 사용합니다.
       (이유: AI API 오류 방지 및 속도 향상)
    2. JSON 데이터가 아예 없는 경우에만 AI(Gemini)를 호출합니다.
    """
    try:
        # 입력 텍스트 정리
        clean_text = text.split(' (')[0].strip()
        intent_key = PHRASE_MAPPINGS.get(clean_text)

        # 1. JSON 캐시 우선 검색 (force_refresh 체크 제거함)
        if intent_key and group_name in DICT_CACHE:
            group_data = DICT_CACHE[group_name]
            target_list = []

            if member_name in group_data and intent_key in group_data[member_name]:
                target_list = group_data[member_name][intent_key]
            elif 'All' in group_data and intent_key in group_data['All']:
                target_list = group_data['All'][intent_key]

            if target_list:
                # 목록에서 랜덤으로 5개 추출 (순서를 섞어서 보여줌)
                # 데이터가 5개보다 많으면 매번 다른게 나오고, 5개면 순서만 바뀜
                selected = random.sample(target_list, min(len(target_list), 5))
                
                # 개수가 5개 미만이면 채우기
                if len(selected) < 5:
                    # 리스트를 반복해서 채움
                    selected = (selected * 5)[:5]
                
                results = []
                for item in selected:
                    if isinstance(item, dict):
                        slang_text = item.get('text', '')
                        if source_lang == 'ja':
                            meaning = item.get('meaning_ja', item.get('meaning', text))
                        else:
                            meaning = item.get('meaning_en', item.get('meaning', text))
                        
                        results.append({'text': slang_text, 'meaning': meaning})
                    else:
                        results.append({'text': item, 'meaning': text})
                
                return results

        # 2. 캐시 데이터가 없을 때만 AI 호출
        return call_gemini_api(text, group_name, member_name, source_lang)

    except Exception as e:
        logger.error(f"❌ Error in translate_to_kpop_slang: {e}")
        return [{'text': text, 'meaning': 'Translation Error'}]

def call_gemini_api(text, group_name, member_name, source_lang):
    if not Config.GEMINI_API_KEY:
        return [{'text': "API Key Error", 'meaning': "Check Server Config"}]

    try:
        # 모델 선택 (gemini-2.0-flash가 안 될 경우 1.5로 자동 폴백하는 로직은 없으므로 안정적인 모델명 사용 권장)
        # 만약 2.0 에러가 계속나면 'gemini-1.5-flash' 로 변경해보세요.
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        target_info = f"group '{group_name}'"
        if member_name and member_name != 'All':
            target_info = f"member '{member_name}' of group '{group_name}'"

        lang_map = {'ja': 'Japanese', 'en': 'English', 'ko': 'Korean', 'zh': 'Chinese'}
        input_lang_name = lang_map.get(source_lang, 'English')
        
        prompt = f"""
        ROLE: K-POP fan creating a cheering slogan.
        TARGET: {target_info}
        INPUT PHRASE: "{text}" (Language: {input_lang_name})
        
        TASK: Generate 5 creative Korean slang phrases (Ju-jeop comments) for this input.
        REQUIREMENT: Provide the meaning back in {input_lang_name}.
        
        FORMAT: Korean Phrase | Meaning in {input_lang_name}
        
        OUTPUT EXAMPLES:
        호랑해 | I tiger you (I love you)
        존잘남신 | Handsome God
        """
        
        response = model.generate_content(prompt)
        
        # 응답 파싱
        lines = [line.strip() for line in response.text.split('\n') if '|' in line]
        
        results = []
        for line in lines[:5]:
            parts = line.split('|')
            if len(parts) >= 2:
                results.append({'text': parts[0].strip(), 'meaning': parts[1].strip()})
            else:
                results.append({'text': line, 'meaning': text})
        
        # 결과가 너무 적을 경우 채우기
        while len(results) < 5:
             fallback = member_name if member_name != 'All' else group_name
             results.append({'text': fallback, 'meaning': text})
                
        return results[:5]
    
    except Exception as e:
        logger.error(f"❌ Gemini API Error: {e}")
        # 실패 시 에러 메시지를 결과로 반환하여 프론트에서 확인 가능하게 함
        return [{'text': "AI Error", 'meaning': "Please try again later"}]