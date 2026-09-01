"""Local-only settings loaded from environment variables / `apps/api/.env`.

`.env` is git-ignored (see root `.gitignore`) — copy `.env.example` to `.env`
and fill in real values there, never commit a key.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Get a free personal key at https://opendart.fss.or.kr (회원가입 > 인증키
# 신청/관리). Company Detail's filings fall back to a clearly-labeled fixture
# placeholder whenever this is unset — see app/routers/company_detail.py.
OPENDART_API_KEY = os.environ.get("OPENDART_API_KEY", "").strip() or None
