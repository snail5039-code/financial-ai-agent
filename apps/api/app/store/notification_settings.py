import sqlite3
import threading

from app.clock import now_kst_iso
from app.schemas.notification_settings import NotificationApplyRequest

TYPE_KEYS = ("policy", "source", "approval", "data", "volatility", "cost")


class NotificationSettingsStore:
    """Persists the one thing the notification settings screen lets a user
    actually change and save: which event types are enabled and the default
    severity threshold. Channels have no editable control on the screen (see
    `NotificationApplyRequest`), so there's nothing to persist for them.

    Same `db_path=":memory:"` default/real-file-in-`main.py` split as
    `ApprovalStore`/`PolicySettingsStore`.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        columns_sql = ", ".join(f"type_{key} INTEGER NOT NULL" for key in TYPE_KEYS)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS notification_settings_applied ("
            f"id INTEGER PRIMARY KEY CHECK (id = 1), {columns_sql}, "
            f"default_severity TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        self._conn.commit()

    def get_applied(self) -> tuple[NotificationApplyRequest, str] | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {', '.join(f'type_{key}' for key in TYPE_KEYS)}, default_severity, applied_at "
                "FROM notification_settings_applied WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        types = {key: bool(value) for key, value in zip(TYPE_KEYS, row[: len(TYPE_KEYS)])}
        default_severity, applied_at = row[len(TYPE_KEYS) :]
        return NotificationApplyRequest(types=types, defaultSeverity=default_severity), applied_at

    def apply(self, payload: NotificationApplyRequest) -> str:
        applied_at = now_kst_iso()
        columns = [f"type_{key}" for key in TYPE_KEYS]
        values = [int(payload.types[key]) for key in TYPE_KEYS]
        values += [payload.defaultSeverity, applied_at]
        columns_sql = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)
        update_sql = ", ".join(f"{col} = excluded.{col}" for col in columns)
        with self._lock:
            self._conn.execute(
                f"INSERT INTO notification_settings_applied (id, {columns_sql}, default_severity, applied_at) "
                f"VALUES (1, {placeholders}, ?, ?) "
                f"ON CONFLICT(id) DO UPDATE SET {update_sql}, default_severity = excluded.default_severity, "
                "applied_at = excluded.applied_at",
                values,
            )
            self._conn.commit()
        return applied_at
