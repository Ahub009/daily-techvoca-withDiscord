import os
import requests
import time
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
HISTORY_FILE = "history.json"

def get_usable_model_name():
    """API에 직접 물어봐서 진짜로 사용 가능한 모델 이름을 가져옵니다."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"⚠️ 모델 목록 조회 실패: {response.text}")
            return None
            
        data = response.json()
        if 'models' not in data:
            print("⚠️ 모델 목록이 비어있습니다.")
            return None

        # 사용 가능한 모델 찾기
        candidates = []
        for model in data['models']:
            name = model['name'].replace('models/', '')
            methods = model.get('supportedGenerationMethods', [])
            
            if 'generateContent' in methods:
                candidates.append(name)
        
        print(f"📋 내 키로 접근 가능한 모델들: {candidates}")
        
        preferred = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro',
            'gemini-1.0-pro',
            'gemini-pro'
        ]
        
        for p in preferred:
            if p in candidates:
                return p
                
        for c in candidates:
            if 'gemini' in c and 'vision' not in c:
                return c
                
        if candidates:
            return candidates[0]
            
        return None

    except Exception as e:
        print(f"⚠️ 모델 검색 중 오류: {e}")
        return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(new_words):
    history = load_history()
    # 중복 제거 후 추가
    current_set = set(history)
    for word in new_words:
        if word not in current_set:
            history.append(word)
    
    # 최근 1000개만 유지
    if len(history) > 1000:
        history = history[-1000:]
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_content(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    used_words = load_history()
    used_words_str = ", ".join(used_words) if used_words else "없음"
    
    prompt = f"""
    다음 주제에 맞춰 영단어 5개를 선정해줘:
    1. AI 기술 및 컴퓨터 산업 관련: 2개
    2. 개발자 실무 관련: 2개
    3. 스포츠 산업 관련: 1개
    
    조건:
    1. 이전에 사용한 단어는 절대 다시 추천하지 마: [{used_words_str}]
    2. 결과는 반드시 순수한 JSON 배열(Array) 형식이어야 해.
    3. 각 배열의 요소는 다음 키를 가져야 해:
       - 'word': 영어 단어
       - 'meaning': 한국어 요약어 (예: 리팩토링, API 등)
       - 'description': 해당 기술 용어에 대한 간단하고 명확한 한국어 해설 (1~2문장)
       - 'example_en': 해당 단어가 포함된 세련된 영어 비즈니스 예문
       - 'example_kr': 위 영어 예문의 자연스러운 한국어 해석
    4. **(볼드) 같은 마크다운 문법은 값(value)에 절대 포함하지 마. 그냥 텍스트만 넣어.
    5. 마지막에 '궁금한 점이 있다면...' 같은 불필요한 멘트는 절대 넣지 마.
    6. 코드 블록(```json) 없이 JSON 데이터만 출력해.
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    print(f"🚀 [{model_name}]에게 요청 보냄...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
        # 혹시 모를 마크다운 제거
        clean_text = re.sub(r"```json|```", "", text).strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # 대괄호 찾기 시도
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            print(f"JSON 파싱 실패. 원본: {text}")
            return []
            
    elif response.status_code == 429:
        print("⏳ 사용량 초과(429). 5초 대기 후 재시도...")
        time.sleep(5)
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
            clean_text = re.sub(r"```json|```", "", text).strip()
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError:
                 # 대괄호 찾기 시도
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        pass
                return []
            
    print(f"❌ 요청 실패: {response.text}")
    print(f"Status Code: {response.status_code}") # 디버깅용
    raise Exception(f"API 호출 실패: {response.status_code}")

def send_discord_message(vocab_list):
    if not DISCORD_WEBHOOK_URL:
        print("디스코드 웹훅 URL 누락")
        return

    # 임베드 구축
    fields = []
    new_words_for_history = []
    
    for item in vocab_list:
        word = item.get("word")
        meaning = item.get("meaning")
        description = item.get("description", "설명 없음")
        example_en = item.get("example_en")
        example_kr = item.get("example_kr")
        
        if word:
            new_words_for_history.append(word)
            fields.append({
                "name": f"⚽ {word}",
                "value": f"📖 **뜻**: {meaning}\n💡 **해설**: {description}\n🇺🇸 **예문**: {example_en}\n🇰🇷 **해석**: {example_kr}",
                "inline": False
            })

    embed = {
        "title": "Today's Tech & Soccer Vocabulary",
        "description": "오늘의 비즈니스 영단어가 도착했습니다.",
        "color": 0x5865F2, # Discord Blurple
        "fields": fields,
        "footer": {
            "text": "Daily Tech Voca powered by Gemini",
            "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    }

    payload = {
        "embeds": [embed]
    }
    
    result = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if result.status_code in [200, 204]:
        print("✅ 디스코드 전송 완료")
        return new_words_for_history
    else:
        print(f"❌ 디스코드 전송 실패: {result.status_code} - {result.text}")
        return []

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ API 키가 없습니다.")
        exit(1)
        
    model_name = get_usable_model_name()
    
    if not model_name:
        print("⚠️ 감지된 모델이 없어 기본값(gemini-1.5-flash)으로 강제 시도합니다.")
        model_name = 'gemini-1.5-flash'
    
    print(f"✨ 선택된 모델: {model_name}")
    
    try:
        vocab_data = generate_content(model_name)
        if vocab_data:
            # 리스트인지 확인
            if isinstance(vocab_data, list):
                sended_words = send_discord_message(vocab_data)
                if sended_words:
                    save_history(sended_words)
                    print(f"💾 히스토리 저장 완료: {len(sended_words)}개 단어")
            else:
                print("형식 오류: JSON이 리스트가 아닙니다.")
        else:
            print("생성된 내용이 없습니다.")
            
    except Exception as e:
        print(f"⛔ 실패: {e}")
        exit(1)
