-- 폰의 매매 규칙이 새 매수를 막아 주문까지 못 간 제안에 막힌 이유를 남긴다 (2026-11-04).
-- 폰이 올린다 (막는 판단은 폰이 한다). 기록 화면이 "규칙에 막힘 · 이유"로 보여준다
ALTER TABLE proposals ADD COLUMN blocked_reason text CHECK (blocked_reason IN ('bear', 'early', 'exposure', 'small'));
