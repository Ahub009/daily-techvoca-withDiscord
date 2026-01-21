import os
import requests
from google import genai
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (로컬 테스트용, GitHub Actions에서는 불필요)
load_dotenv()

# 환경 변수에서 설정 가져오기 (로컬: .env 파일, GitHub Actions: Secrets)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Gemini 설정 
client = genai.Client(api_key=GEMINI_API_KEY)

def get_vocabulary():
    prompt = "축구 산업 및 AI 기술과 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."
    # Gemini 1.5 Flash 모델 사용 (구체적인 버전 명시)
    response = client.models.generate_content(
        model='gemini-1.5-flash-001',
        contents=prompt
    )
    return response.text

def send_discord_message(content):
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
        print(f"오류 발생: {e}")
