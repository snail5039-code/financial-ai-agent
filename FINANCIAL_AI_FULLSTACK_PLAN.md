# 금융 AI 에이전트 풀스택 전환 계획

> 기준일: 2026-08-27 KST  
> 현재 기준: 정적 HTML 목업 19개 완료, React/Vite `apps/web` 1차 프론트 생성 완료, 최신 완료 커밋 `93d9375 역할 작업 가시성 운영 규칙 강화`  
> 문서 목적: 실제 금융 API를 연결하지 않고, 정적 목업을 프론트엔드와 백엔드가 통신하는 실행 가능한 앱 구조로 옮기기 위한 상위 계획을 정리한다.

## 현재 결정

- 정적 화면 추가는 일단 멈춘다.
- 현재 19개 목업을 제품 흐름 1차 기준으로 본다.
- React/Vite 프론트엔드 `apps/web`는 이미 생성됐고 대시보드, 승인 대기, 승인 전 근거 패킷 화면이 연결됐다.
- `FRONTEND-005`에서 승인 대기 화면의 주문 행 접근성 구조를 정리했다.
- 다음 단계는 **현재 React + Vite 프론트엔드와 아직 생성하지 않은 FastAPI 백엔드**를 연결하는 로컬 MVP 계획이다.
- 백엔드는 아직 만들지 않았으며, 만들 때도 실제 금융 API 대신 고정 fixture 데이터를 제공한다.
- 실제 금융 데이터, 계좌, 주문, 체결, 공시, 시세, 환율, AI 실행, 외부 API, 운영 DB는 연결하지 않는다.

## 추천 방향

현재 추천은 **기존 React + Vite 프론트 유지 + FastAPI fixture API 추가, 메모리 fixture, 대시보드 API 수직 슬라이스부터 시작**이다.

이유:

- 프론트엔드와 백엔드 분리가 명확하다.
- 금융 계산, 검증 로직, fixture 데이터, 나중의 AI 에이전트 실험을 Python 생태계로 이어가기 좋다.
- 실제 API를 붙이지 않아도 현재 프론트 화면 흐름과 로컬 백엔드 계약을 먼저 검증할 수 있다.

## 분할 문서

세부 계획은 아래 문서를 순서대로 참조한다.

1. `docs/fullstack/00-readme.md`: 읽는 순서와 현재 결론
2. `docs/fullstack/01-overview.md`: 현재 판단, 목표, 비목표
3. `docs/fullstack/02-stack-architecture.md`: 기술 스택과 폴더 구조
4. `docs/fullstack/03-data-api-contract.md`: 데이터 원칙과 로컬 API 범위
5. `docs/fullstack/04-frontend-backend-scope.md`: 프론트엔드·백엔드 전환 범위
6. `docs/fullstack/05-safety-validation.md`: 안전장치와 검증 기준
7. `docs/fullstack/06-implementation-roadmap.md`: 구현 단계와 첫 개발 티켓

## 다음 관문

구현을 시작하기 전 관리자가 확정할 항목은 다음이다.

1. FastAPI 패키지 관리를 `uv`로 할지 `pip`/`venv`로 할지
2. 1차 상태 저장을 메모리 fixture로만 할지, SQLite까지 포함할지
3. 첫 백엔드 연결 범위를 대시보드 하나로 할지, 대시보드와 승인 대기를 함께 묶을지
4. 기존 정적 목업을 계속 기준서로 유지할지, 새 앱 구현 뒤 일부를 보관 문서로 옮길지

현재 추천은 `uv`, 메모리 fixture, 대시보드 API 1개 수직 슬라이스, 기존 정적 목업과 `apps/web` 프론트 유지다.
