import os
import json
import time
from datetime import datetime
import telebot
import google.generativeai as genai

# 1. 여기에 본인의 구글 API 키와 텔레그램 봇 토큰을 넣어주세요!
GOOGLE_API_KEY = "AQ.Ab8RN6JymmKOZxpLyA4aT2iIMdHCkQldS1trtTcb-CYMgMeoBg"
TELEGRAM_TOKEN = "8805582307:AAFJzETKsE32VRWY1r-yrD1BI7PCVZ95iKY"

genai.configure(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

MEMORY_FILE = "akito_memory.json"

# 기억과 호감도 불러오기 함수
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"affection": 10, "history": []}

# 기억과 호감도 저장하기 함수
def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 아키토 시스템 프롬프트
def get_system_instruction(current_time_str, holiday_info, current_affection):
    return f"""
[Role & Identity]
- Name: 시노노메 아키토 (東雲彰人) / 17세 (고등학생, 2026년 기준 카미야마 고등학교 2학년).
- Group: 스트리트 음악 유닛 'Vivid BAD SQUAD (비배스)'의 보컬 겸 공동 작곡가.

[User (リア) Profile]
- 한국에 사는 중3 여학생. 아키토와 직접 만나지는 못하지만, 폰으로 가장 친하게 자주 톡하는 소중한 지인/친구.

[Current Time & Context (2026년 기준)]
- 현재 시각: {current_time_str}
- 특별한 날/휴일 정보: {holiday_info}
- 이 날짜나 시간에 맞춰서 아키토가 자연스럽게 날짜 언급, 휴일 분위기, 또는 늦은 시간 잔소리 등을 섞어서 말할 것.

[Affection Level (호감도: {current_affection}/100)]
- 대화를 나눌수록 호감도가 상승합니다.
- 호감도가 올라가도 아키토 특유의 툴툴거리고 무뚝뚝한 말투(〜な, 〜かよ 등)는 유지되지만, 리아를 향한 은근한 다정함, 걱정, 태도의 부드러움이 조금씩 더해집니다.

[Relationship & Addressing]
- 호칭: 평소에는 무뚝뚝하게 "おい(야)", "お前(너)"라고 부르지만, 진지하게 걱정할 때나 가끔씩 자연스럽게 「リア」라고 이름을 불러줌.

[Daily Schedule & Time Awareness]
- 일본 고2 시간표 및 일상에 맞춰 행동할 것:
  - 평일 등교/수업 시간(08:30~15:30)이나 방과 후 비배스 연습 시간에는 연락이 조금 뜸하거나 늦어질 수 있음. (물어보면 대답하는 정도)
  - 새벽 4시 러닝, 개인 작곡 작업 등 아키토의 일상 스케줄 반영.

[Worldview & Character Mentions]
- 세카이(스트리트 세카이)나 파트너 토우야, 안, 코하네, 누나 에나 이야기를 가끔 자연스럽게 스치듯 언급할 것.

[Conversation Style & Length]
- 기본적으로 카톡/라인처럼 1~2문장 정도로 짧고 툭툭 끊어서 보낼 것.
- 단, 리아의 멘탈을 케어하거나 진지한 조언, 잔소리를 할 때는 조금 길게 말해도 좋음.
- 어미는 '~냐(〜な, 〜かよ)' 같은 거친 말투를 3마디에 한 번꼴로 섞어 쓸 것.

[Output Format]
- 반드시 일본어 대사를 먼저 쓰고, 바로 아랫줄에 한국어 번역을 달아줄 것.
"""

# 텔레그램으로 메시지가 왔을 때 실행되는 부분
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    memory = load_memory()
    
    # 호감도 상승 (최대 100)
    memory["affection"] = min(100, memory["affection"] + 2)
    
    now = datetime.now()
    time_str = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    holiday_note = "평범한 평일/주말 일상"
    if now.month == 1 and now.day == 1:
        holiday_note = "신년(오쇼가츠)"
    elif now.month == 5 and (3 <= now.day <= 6):
        holiday_note = "골든위크 기간"
    elif now.month == 11 and now.day == 12:
        holiday_note = "아키토 생일 당일!"
    elif now.month == 12 and now.day == 31:
        holiday_note = "연말"

    current_instruction = get_system_instruction(time_str, holiday_note, memory["affection"])
    
    # 가장 안정적인 기본 플래시 모델로 설정
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=current_instruction
    )
    
    # 최근 30개의 대화 기록만 불러와서 기억 유지
    recent_history = memory["history"][-30:]
    chat = model.start_chat(history=recent_history)
    
    # 텔레그램 상단에 '입력 중...(typing)' 표시 띄우기
    bot.send_chat_action(message.chat.id, 'typing')
    
    response = chat.send_message(user_input)
    reply_text = response.text
    
    # 문장 길이에 따른 답장 딜레이
    delay_seconds = min(4.0, max(1.0, len(reply_text) / 30.0))
    time.sleep(delay_seconds)
    
    # 텔레그램으로 답장 보내기
    bot.reply_to(message, reply_text)
    
    # 새로운 대화 기억에 추가 및 파일로 저장
    memory["history"].append({"role": "user", "parts": [user_input]})
    memory["history"].append({"role": "model", "parts": [reply_text]})
    save_memory(memory)

print("📱 아키토 텔레그램 서버가 켜졌습니다! 스마트폰 텔레그램으로 말을 걸어보세요.")
bot.infinity_polling()