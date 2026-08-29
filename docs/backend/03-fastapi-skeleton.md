# FastAPI 골격

기준일: 2026-08-29 KST

## 현재 상태

`apps/web` React/Vite 프론트엔드는 이미 존재한다. `apps/api` FastAPI 백엔드는 아직 생성하지 않았다. 이 문서는 다음 구현 작업에서 만들 예상 구조를 정리하며, 지금 단계에서는 코드나 폴더를 생성하지 않는다.

## 예상 폴더 구조

```text
apps/api/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ routers/
│  │  ├─ __init__.py
│  │  └─ health.py
│  ├─ schemas/
│  │  ├─ __init__.py
│  │  └─ common.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  └─ fixture_store.py
│  └─ fixtures/
│     ├─ __init__.py
│     └─ dashboard.py
├─ tests/
│  ├─ __init__.py
│  └─ test_health.py
└─ pyproject.toml
```

## 책임 분리

- `main.py`: FastAPI 앱 생성, 라우터 등록, 로컬 CORS 설정
- `routers/`: HTTP 엔드포인트
- `schemas/`: 공통 응답 래퍼와 화면별 응답 타입
- `services/`: fixture 읽기, 메모리 상태 관리
- `fixtures/`: 화면 검토용 고정 데이터
- `tests/`: 안전 플래그와 응답 구조 검증

## 명명 원칙

- 실제 주문처럼 보이는 서비스명은 피한다.
- 승인 처리는 이후 단계에서도 `MockApprovalService`, `paperOnly`, `executed: false`처럼 모의 상태가 드러나는 이름을 사용한다.
- 증권사, 계좌, 주문, 체결, 공시, 시세, 환율 연결을 암시하는 모듈명은 만들지 않는다.

## 다음 구현 전 확인

- 패키지 관리 도구를 `uv`로 할지 `pip`/`venv`로 할지 관리자 승인이 필요하다.
- 첫 백엔드 연결 화면을 대시보드 하나로 할지 승인 대기까지 묶을지 관리자 판단이 필요하다.
- `BACKEND-001` 구현 지시가 `/api/health`만 요구하는지, 화면별 fixture API 파일 위치까지 요구하는지 다시 확인한다.
