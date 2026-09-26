import asyncio
import json
import sqlite3
import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from ..config import DB_PATH
from ..models.schema import AgentEvent, AuditEvent, AgentEventType, PaymentLifecycleState

class DatabaseManager:
    """
    SQLite Persistence & Live Event Dispatcher for OpsPilot.
    """

    def __init__(self, db_file: str = str(DB_PATH)):
        self.db_file = db_file
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        try:
            self.init_db()
        except Exception as e:
            # If default db_file fails due to readonly filesystem or missing permissions, fallback to /tmp
            if self.db_file != "/tmp/opspilot.db":
                self.db_file = "/tmp/opspilot.db"
                self.init_db()
            else:
                raise e

    def _get_connection(self) -> sqlite3.Connection:
        import os
        db_dir = os.path.dirname(os.path.abspath(self.db_file))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    user_request TEXT NOT NULL,
                    scenario_id TEXT,
                    status TEXT NOT NULL,
                    payment_state TEXT NOT NULL,
                    customer TEXT,
                    vendor TEXT,
                    invoice TEXT,
                    amount REAL,
                    currency TEXT,
                    decision_summary TEXT,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    step_name TEXT,
                    provider TEXT,
                    canonical_tool_id TEXT,
                    status TEXT,
                    duration_ms INTEGER,
                    input_summary TEXT,
                    output_summary TEXT,
                    decision_effect TEXT,
                    payload_json TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    reference_ids_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
                """
            )
            conn.commit()

    def save_run_state(self, state: Dict[str, Any]):
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run_id = state["run_id"]
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, user_request, scenario_id, status, payment_state,
                    customer, vendor, invoice, amount, currency, decision_summary,
                    state_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    status=excluded.status,
                    payment_state=excluded.payment_state,
                    customer=excluded.customer,
                    vendor=excluded.vendor,
                    invoice=excluded.invoice,
                    amount=excluded.amount,
                    currency=excluded.currency,
                    decision_summary=excluded.decision_summary,
                    state_json=excluded.state_json,
                    updated_at=excluded.updated_at
                """,
                (
                    run_id,
                    state.get("user_request", ""),
                    state.get("scenario_id", ""),
                    state.get("status", "RUNNING"),
                    state.get("payment_state", PaymentLifecycleState.REQUESTED.value),
                    state.get("customer", "Thoughtworks"),
                    state.get("vendor", ""),
                    state.get("invoice", ""),
                    state.get("amount", 0.0),
                    state.get("currency", "INR"),
                    state.get("decision_summary", ""),
                    json.dumps(state),
                    state.get("timestamps", {}).get("started_at", now_iso),
                    now_iso,
                ),
            )
            conn.commit()

    def get_run_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT state_json FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["state_json"])
        return None

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT run_id, user_request, scenario_id, status, payment_state,
                       customer, vendor, invoice, amount, currency, decision_summary,
                       created_at, updated_at
                FROM runs ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def log_event(self, event: AgentEvent):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, run_id, event_type, step_name, provider, canonical_tool_id,
                    status, duration_ms, input_summary, output_summary, decision_effect,
                    payload_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                    event.step_name,
                    event.provider,
                    event.canonical_tool_id,
                    event.status,
                    event.duration_ms,
                    event.input_summary,
                    event.output_summary,
                    event.decision_effect,
                    json.dumps(event.payload) if event.payload else None,
                    event.timestamp,
                ),
            )
            conn.commit()

        # Dispatch event asynchronously to live SSE subscribers
        self._notify_subscribers(event.run_id, event)

    def log_audit(self, audit: AuditEvent, run_id: str):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    id, run_id, actor, event_type, details_json, reference_ids_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.id,
                    run_id,
                    audit.actor.value if hasattr(audit.actor, "value") else str(audit.actor),
                    audit.event_type,
                    json.dumps(audit.details),
                    json.dumps(audit.reference_ids),
                    audit.timestamp,
                ),
            )
            conn.commit()

    def get_events_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM events WHERE run_id = ? ORDER BY timestamp ASC", (run_id,)
            )
            rows = cursor.fetchall()
            events = []
            for r in rows:
                d = dict(r)
                if d.get("payload_json"):
                    d["payload"] = json.loads(d["payload_json"])
                events.append(d)
            return events

    def get_audit_logs_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_logs WHERE run_id = ? ORDER BY timestamp ASC", (run_id,)
            )
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                d = dict(r)
                d["details"] = json.loads(d["details_json"])
                d["reference_ids"] = json.loads(d["reference_ids_json"])
                logs.append(d)
            return logs

    # SSE Event Streaming Helpers
    def subscribe(self, run_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue):
        if run_id in self._subscribers and queue in self._subscribers[run_id]:
            self._subscribers[run_id].remove(queue)
            if not self._subscribers[run_id]:
                del self._subscribers[run_id]

    def _notify_subscribers(self, run_id: str, event: AgentEvent):
        if run_id in self._subscribers:
            event_dict = event.model_dump()
            for q in list(self._subscribers[run_id]):
                try:
                    q.put_nowait(event_dict)
                except Exception:
                    pass

db = DatabaseManager()
