import type { FixtureEnvelope } from "../types/dashboard";

/**
 * Minimal client for the local fixture backend.
 *
 * Only same-origin paths under `/api/` are reachable. The Vite dev server
 * proxies them to the local FastAPI app, so no request ever leaves the machine
 * and no external host can be addressed through this module.
 */

const LOCAL_API_PREFIX = "/api/";
const REQUEST_TIMEOUT_MS = 8000;

export class ApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function getJson<TResponse>(path: string): Promise<TResponse> {
  if (!path.startsWith(LOCAL_API_PREFIX)) {
    throw new ApiError(`로컬 백엔드 경로가 아닙니다: ${path}`);
  }

  let response: Response;
  try {
    response = await fetch(path, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS)
    });
  } catch {
    throw new ApiError("로컬 백엔드에 연결하지 못했습니다. FastAPI 서버가 실행 중인지 확인하세요.");
  }

  if (!response.ok) {
    // The dev server turns a refused connection to the backend into a 5xx of its
    // own, so a server-side status usually means the backend is not running.
    const reason =
      response.status >= 500
        ? "로컬 백엔드가 응답하지 못했습니다. FastAPI 서버가 실행 중인지 확인하세요."
        : "로컬 백엔드가 요청을 처리하지 못했습니다.";
    throw new ApiError(`${reason} (HTTP ${response.status})`, response.status);
  }

  try {
    return (await response.json()) as TResponse;
  } catch {
    throw new ApiError("로컬 백엔드 응답을 JSON으로 해석하지 못했습니다.");
  }
}

/**
 * Refuses any payload that does not declare itself as a mock, paper-only,
 * unexecuted, zero-connection fixture. A response that fails this check is not
 * rendered at all, so a screen can never present non-mock data as if it were
 * part of the mockup.
 */
function assertFixtureEnvelope<TData>(payload: FixtureEnvelope<TData>): FixtureEnvelope<TData> {
  const isSafeFixture =
    payload?.isMock === true &&
    payload?.paperOnly === true &&
    payload?.executed === false &&
    payload?.externalConnections === 0;

  if (!isSafeFixture) {
    throw new ApiError("응답의 모의 데이터 안전 표시가 확인되지 않아 화면에 사용하지 않습니다.");
  }

  return payload;
}

export async function getFixture<TData>(path: string): Promise<FixtureEnvelope<TData>> {
  return assertFixtureEnvelope(await getJson<FixtureEnvelope<TData>>(path));
}
