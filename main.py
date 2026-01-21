import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

def generate_content_api(model_name):
    """라이브러리 없이 직접 REST API를 호출합니다."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 프롬프트 설정
    prompt_text = "축구 산업 및 AI 기술과 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."
    
    data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    print(f"📡 API 호출 시도: {model_name}")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        print(f"⚠️ {model_name} 호출 실패: {response.status_code} - {response.text}")
        return None

def get_vocabulary():
    # 시도할 모델 목록 (순서대로 시도)
    # 1.5-flash가 안되면 2.0-flash-exp (이건 존재한다는게 로그로 확인됨) 등으로 넘어감
    models = [
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    for model in models:
        result = generate_content_api(model)
        if result:
            print(f"✅ 성공! ({model})")
            return result
        # 429(Too Many Requests)일 경우 잠시 대기 후 다음 모델 시도
        time.sleep(1)
            
    raise Exception("모든 모델 시도 실패. API 키나 할당량을 확인해주세요.")

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("디스코드 웹훅 URL이 없습니다.")
        return
        
    data = {"content": content}
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    
    if response.status_code in [200, 204]:
        print("✅ 디스코드 전송 완료")
    else:
        print(f"❌ 디스코드 전송 실패: {response.status_code}")

if __name__ == "__main__":
    try:
        vocas = get_vocabulary()
        send_discord_message(vocas)
    except Exception as e:
        print(f"⛔ 치명적 오류: {e}")
        exit(1)

