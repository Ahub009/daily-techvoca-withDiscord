import os
import requests
from google import genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 설정
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

def get_available_model(client):
    """현재 API 키로 사용 가능한 모델 중 생성(generateContent)을 지원하는 최적의 모델을 찾습니다."""
    print("🔍 사용 가능한 모델 검색 중...")
    try:
        available_models = []
        for model in client.models.list():
            if 'generateContent' in model.supported_generation_methods:
                # 모델 이름 앞에 'models/'가 붙어있으면 제거 (SDK 버전에 따라 처리)
                name = model.name.replace('models/', '')
                available_models.append(name)
        
        print(f"📋 발견된 모델 목록: {available_models}")
        
        # 우선순위: Flash > Pro > 1.5 > 1.0
        preferred_order = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-001',
            'gemini-1.5-flash-002',
            'gemini-1.5-pro',
            'gemini-1.5-pro-001',
            'gemini-1.0-pro',
            'gemini-pro'
        ]
        
        # 1. 우선순위 목록에 있는 모델이 실제로 존재하는지 확인
        for preferred in preferred_order:
            if preferred in available_models:
                print(f"✨ 최적 모델 선정: {preferred}")
                return preferred
                
        # 2. 우선순위에 없더라도 'gemini'가 포함된 모델 선택
        for model in available_models:
            if 'gemini' in model and 'vision' not in model: # 비전 전용 제외
                print(f"⚠️ 대체 모델 선택: {model}")
                return model
                
        # 3. 정 없으면 그냥 첫 번째 모델 반환
        if available_models:
            return available_models[0]
            
    except Exception as e:
        print(f"⚠️ 모델 목록 조회 실패: {e}")
        
    # 검색 실패 시 기본값 반환 (최후의 수단)
    return 'gemini-1.5-flash'

def get_vocabulary():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 동적으로 모델 선택
    model_name = get_available_model(client)
    
    prompt = "축구 산업 및 AI 기술과 관련된 영단어 5개를 선정해서 뜻과 예문을 한국어로 알려줘. 양식은 디스코드에 보기 좋게 구성해줘."
    
    print(f"🚀 [{model_name}] 모델로 생성 시작...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"❌ 1차 시도 실패 ({model_name}): {e}")
        
        # 실패 시 'gemini-pro' (구관이 명관)로 한 번만 더 재시도
        fallback_model = 'gemini-pro'
        if model_name != fallback_model:
            print(f"🔄 [{fallback_model}] 모델로 재시도...")
            try:
                response = client.models.generate_content(
                    model=fallback_model,
                    contents=prompt
                )
                return response.text
            except Exception as e2:
                raise RuntimeError(f"재시도도 실패했습니다: {e2}")
        raise e

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
            print("✅ 메시지 전송 성공!")
        else:
            print(f"⚠️ 전송 실패: {status}")
    except Exception as e:
        print(f"⛔ 프로그램 실행 중 오류: {e}")
        exit(1)
