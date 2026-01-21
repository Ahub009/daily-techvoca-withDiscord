import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드 (로컬 테스트용)
load_dotenv()

# 환경 변수 설정
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# 사용할 모델 후보 목록 (앞에서부터 순차적으로 시도)
MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp"
]

def get_vocabulary():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = "축구 산업 및 AI 기술과 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."

    last_error = None

    # 여러 모델을 순차적으로 시도
    for model_name in MODEL_CANDIDATES:
        print(f"[{model_name}] 모델 시도 중...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            print(f"✅ 성공! ({model_name} 사용됨)")
            return response.text
        except Exception as e:
            print(f"❌ {model_name} 실패: {e}")
            last_error = e
            continue
    
    # 모든 모델이 실패한 경우
    raise RuntimeError(f"모든 모델 시도 실패. 마지막 에러: {last_error}")

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        
    data = {"content": content}
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    return response.status_code

if __name__ == "__main__":
    try:
        vocas = get_vocabulary()
        status = send_discord_message(vocas)
        if status == 200 or status == 204:
            print("메시지 전송 성공!")
        else:
            print(f"전송 실패: {status}")
    except Exception as e:
        print(f"치명적 오류 발생: {e}")
        exit(1)
