import { useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import {
  notificationChannels,
  notificationSafetyCopy,
  notificationSeverityLabel,
  notificationTypes,
  type NotificationChannelId,
  type NotificationSeverity,
  type NotificationType
} from "../fixtures/notificationSettings";
import type { PageKey } from "../types/dashboard";
import "./NotificationSettingsPage.css";

interface NotificationSettingsPageProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function NotificationSettingsPage({ activePage, onNavigate }: NotificationSettingsPageProps) {
  const [selectedChannelId, setSelectedChannelId] = useState<NotificationChannelId>("inapp");
  const [severity, setSeverity] = useState<NotificationSeverity>("높음");
  const [types, setTypes] = useState(notificationTypes);
  const [preview, setPreview] = useState({ title: "대기 중", body: "버튼을 누르면 화면 안에서만 예시 알림을 표시합니다." });

  const selectedChannel = notificationChannels.find((channel) => channel.id === selectedChannelId) ?? notificationChannels[0];
  const activeTypeCount = useMemo(() => types.filter((type) => type.enabled).length, [types]);

  function toggleType(target: NotificationType) {
    setTypes((current) => current.map((type) => (type.id === target.id ? { ...type, enabled: !type.enabled } : type)));
  }

  const main = (
    <section className="notification-main" aria-labelledby="notification-title">
      <header className="notification-summary">
        <div>
          <span className="eyebrow">수신 정책</span>
          <h1 id="notification-title">확인 알림만 화면에서 미리보기</h1>
          <p>리스크 이벤트가 생겼을 때 어떤 채널과 기준으로 보여줄지 정합니다.</p>
        </div>
        <div className="notification-summary-grid" aria-label="알림 설정 요약">
          <div><span>활성 채널</span><strong>{notificationChannels.filter((channel) => channel.enabled).length}개</strong></div>
          <div><span>유형</span><strong>{activeTypeCount}개</strong></div>
          <div><span>심각도</span><strong>{notificationSeverityLabel(severity)}</strong></div>
          <div><span>외부 발송</span><strong>0건</strong></div>
        </div>
      </header>

      <section className="settings-area">
        <div className="setting-block channels-block">
          <div className="setting-block-head"><h2>알림 채널</h2><span>실제 권한 요청 없음</span></div>
          <div className="channel-list" role="listbox" aria-label="알림 채널">
            {notificationChannels.map((channel) => (
              <button
                className={channel.id === selectedChannelId ? "channel-card selected" : "channel-card"}
                data-state={channel.state}
                key={channel.id}
                type="button"
                role="option"
                aria-selected={channel.id === selectedChannelId}
                onClick={() => setSelectedChannelId(channel.id)}
              >
                <strong>{channel.name}</strong>
                <span>{channel.state}</span>
                <small>{channel.summary}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="setting-block type-block">
          <div className="setting-block-head"><h2>알림 유형</h2><span>화면용 토글</span></div>
          <div className="type-list" aria-label="알림 유형">
            {types.map((type) => (
              <button className={type.enabled ? "type-toggle enabled" : "type-toggle"} key={type.id} type="button" aria-pressed={type.enabled} onClick={() => toggleType(type)}>
                <strong>{type.name}</strong>
                <span className="switch" aria-hidden="true" />
                <p>{type.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="setting-block rules-block">
          <div className="setting-block-head"><h2>수신 기준</h2><span>저장되지 않는 화면 상태</span></div>
          <div className="rule-row">
            <span>심각도 기준</span>
            <div className="segments" role="group" aria-label="심각도 기준">
              {[
                ["중대", "중대만"],
                ["높음", "높음 이상"],
                ["보통", "보통 포함"]
              ].map(([value, label]) => (
                <button className={severity === value ? "selected" : ""} key={value} type="button" aria-pressed={severity === value} onClick={() => setSeverity(value as NotificationSeverity)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="quiet-row">
            <span>조용한 시간</span>
            <strong>22:00-08:00</strong>
            <small>이 시간에는 앱 내부 배지만 표시하는 예시입니다.</small>
          </div>
          <button
            className="preview-button"
            type="button"
            onClick={() => setPreview({ title: "화면용 테스트 알림", body: "확인이 필요한 리스크 이벤트가 있습니다. 실제 발송·권한 요청·매수/매도 지시는 없습니다." })}
          >
            화면용 테스트 알림 미리보기
          </button>
        </div>
      </section>
      <footer className="notification-disclaimer">{notificationSafetyCopy}</footer>
    </section>
  );

  const inspector = (
    <aside className="notification-inspector" aria-live="polite" aria-atomic="false">
      <div className="inspector-scroll">
        <header>
          <span className="eyebrow">설정 인스펙터</span>
          <div className="notification-inspector-title">
            <h2>{selectedChannel.name}</h2>
            <span>{selectedChannel.state}</span>
          </div>
          <p>{selectedChannel.summary}</p>
        </header>
        <section>
          <h3>현재 적용 예시</h3>
          <dl>
            <div><dt>채널 상태</dt><dd>{selectedChannel.state}</dd></div>
            <div><dt>활성 여부</dt><dd>{selectedChannel.enabled ? "화면 표시" : "미사용"}</dd></div>
            <div><dt>심각도 기준</dt><dd>{notificationSeverityLabel(severity)}</dd></div>
            <div><dt>활성 유형</dt><dd>{activeTypeCount}개</dd></div>
          </dl>
        </section>
        <section>
          <h3>테스트 미리보기</h3>
          <div className="preview-card"><strong>{preview.title}</strong><p>{preview.body}</p></div>
        </section>
        <section>
          <h3>금지 경계</h3>
          <dl>
            <div><dt>실제 알림 발송</dt><dd>없음</dd></div>
            <div><dt>브라우저 권한 요청</dt><dd>없음</dd></div>
            <div><dt>이메일·메신저 연결</dt><dd>미연결</dd></div>
            <div><dt>매수·매도 지시</dt><dd>금지</dd></div>
          </dl>
        </section>
        <nav className="notification-related-links" aria-label="관련 화면">
          <h3>관련 화면</h3>
          <button type="button" onClick={() => onNavigate("risks")}>리스크 알림 보기<span>›</span></button>
          <button type="button" onClick={() => onNavigate("policy")}>투자 정책 보기<span>›</span></button>
          <button type="button" onClick={() => onNavigate("data")}>데이터 연결 보기<span>›</span></button>
        </nav>
      </div>
      <footer>{notificationSafetyCopy}</footer>
    </aside>
  );

  return <AppShell title="알림 설정" accountLabel="시뮬레이션 계좌" lastSync="화면용" activePage={activePage} onNavigate={onNavigate} main={main} inspector={inspector} />;
}
