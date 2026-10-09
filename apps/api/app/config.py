"""환경변수 설정. 값은 `apps/api/.env`(git 제외)에 둔다.

서버는 증권사 키·계좌번호를 받지 않는다 (AGENTS.md 1장). 여기에 추가하지 않는다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
# OpenDART 공시 API 키 (4단계에서 사용)
OPENDART_API_KEY = os.environ.get("OPENDART_API_KEY", "").strip() or None

# Gemini (3단계부터). 모델은 .env에서 바꿀 수 있다
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or None
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.6-flash"
GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "").strip() or "gemini-embedding-2"

# 공공데이터포털 금융위원회_주식시세정보 (4단계): 일별 종가와 시가총액
DATA_GO_KR_API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "").strip() or None

# 서버가 매일 이 시각(KST)에 분석용 데이터를 자동 수집한다. 시세는 영업일 다음 날 오후에 갱신된다.
# 비우면 15시, "off"면 끈다
AUTO_COLLECT_HOUR = os.environ.get("AUTO_COLLECT_HOUR", "").strip() or "15"
# 아침 브리핑 자동 실행 시각 (예: "08:30"). 비우면 안 함: 사용자마다 Gemini 호출이 생긴다
MORNING_BRIEF_TIME = os.environ.get("MORNING_BRIEF_TIME", "").strip() or None
# 장 마감 요약 시각. LLM이 없어 비용이 없으므로 기본으로 켠다. "off"면 안 함
CLOSE_SUMMARY_TIME = os.environ.get("CLOSE_SUMMARY_TIME", "").strip() or "15:40"
# 장 마감 AI 회고·내일 계획 시각 (예: "15:50", 장 마감 요약 뒤). Gemini 비용이 생겨 비어 있으면 끈다
CLOSE_REVIEW_TIME = os.environ.get("CLOSE_REVIEW_TIME", "").strip() or None

# 분석할 때 Google 뉴스 RSS에서 종목 뉴스(제목·링크)를 받는다. 무료, 키 없음. "off"면 저장된 뉴스만 쓴다
NEWS_FETCH = os.environ.get("NEWS_FETCH", "").strip().lower() != "off"

# 폰 푸시 알림 (2-1): Firebase 서비스 계정 JSON 파일 경로. 비우면 알림을 쌓기만 하고 보내지 않는다 (앱 알림 목록에는 보임)
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "").strip() or None

# 개발용: 장 운영 시간 검사를 이 시각(KST, 예: "10:00")으로 한다. 비우면 실제 시계. 운영 서버에서는 비운다
MARKET_CLOCK = os.environ.get("MARKET_CLOCK", "").strip() or None

# 웹(Flutter Web) 개발 서버 주소. 쉼표로 여러 개. 비우면 다른 주소의 브라우저 요청을 받지 않는다
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
