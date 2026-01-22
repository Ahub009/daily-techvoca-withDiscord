import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

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
            # 'models/gemini-1.5-flash' -> 'gemini-1.5-flash'
            name = model['name'].replace('models/', '')
            methods = model.get('supportedGenerationMethods', [])
            
            if 'generateContent' in methods:
                candidates.append(name)
        
        print(f"📋 내 키로 접근 가능한 모델들: {candidates}")
        
        # 우선순위 로직
        preferred = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro',
            'gemini-1.0-pro',
            'gemini-pro'
        ]
        
        # 1순위: 선호하는 모델 중 있는 것 선택
        for p in preferred:
            if p in candidates:
                return p
                
        # 2순위: 'gemini'가 들어간 아무 모델이나 선택 (vision 제외)
        for c in candidates:
            if 'gemini' in c and 'vision' not in c:
                return c
                
        # 3순위: 그냥 아무거나
        if candidates:
            return candidates[0]
            
        return None

    except Exception as e:
        print(f"⚠️ 모델 검색 중 오류: {e}")
        return None

def generate_content(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = "AI 기술과 축구 산업에 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    print(f"🚀 [{model_name}]에게 요청 보냄...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '내용 없음')
    elif response.status_code == 429:
        print("⏳ 사용량 초과(429). 5초 대기 후 재시도...")
        time.sleep(5)
        # 한 번만 더 재시도
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '내용 없음')
            
    print(f"❌ 요청 실패: {response.text}")
    raise Exception(f"API 호출 실패: {response.status_code}")

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("디스코드 웹훅 URL 누락")
        return
    requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ API 키가 없습니다.")
        exit(1)
        
    # 1. 쓸 수 있는 모델 찾기
    model_name = get_usable_model_name()
    
    # 2. 없으면 강제로 기본값 설정
    if not model_name:
        print("⚠️ 감지된 모델이 없어 기본값(gemini-1.5-flash)으로 강제 시도합니다.")
        model_name = 'gemini-1.5-flash'
    
    print(f"✨ 선택된 모델: {model_name}")
    
    try:
        # 3. 콘텐츠 생성
        text = generate_content(model_name)
        if text:
            # 4. 디스코드 전송
            send_discord_message(text)
            print("✅ 모든 작업 완료!")
    except Exception as e:
        print(f"⛔ 실패: {e}")
        exit(1)

