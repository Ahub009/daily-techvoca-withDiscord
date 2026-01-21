import requests
import os
import openai

# Use environment variables for security
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT = """
AI 기술과 산업, 축구 산업과 관련된 영어 단어 5개를 만들어줘.
각 단어는 영어 + 한국어 뜻을 포함하고 간단한 설명(어떤 상황에서 쓰는지 등)도 덧붙여줘
"""

def main():
    if not WEBHOOK_URL or not openai.api_key:
        print("Error: Environment variables DISCORD_WEBHOOK_URL or OPENAI_API_KEY are not set.")
        return

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=500
        )
        text = res.choices[0].message.content

        response = requests.post(WEBHOOK_URL, json={"content": text})
        if response.status_code == 204 or response.status_code == 200:
            print("Successfully sent vocabulary to Discord.")
        else:
            print(f"Failed to send to Discord. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
