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
