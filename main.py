import os
import requests
import google.generativeai as genai

# 환경 변수에서 설정 가져오기
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite') # 무료 티어용 최신 모델

def get_vocabulary():
    prompt = "축구 산업 및 AI 기술과 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."
    response = model.generate_content(prompt)
    return response.text

def send_discord_message(content):
    data = {"content": content}
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    return response.status_code

if __name__ == "__main__":
    try:
        vocas = get_vocabulary()
        status = send_discord_message(vocas)
        if status == 204:
            print("메시지 전송 성공!")
        else:
            print(f"전송 실패: {status}")
    except Exception as e:
        print(f"오류 발생: {e}")
