
from __future__ import annotations
import os, io, json, gzip, hashlib, sqlite3, uuid, re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except Exception:
    PasswordHasher = None
    class VerifyMismatchError(Exception): pass

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PH = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2) if PasswordHasher else None

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _json_bytes(value: Any) -> bytes:
    """Serialize directly into gzip without materialising a full JSON copy.

    A project result can contain tens of megabytes of evidence.  The previous
    json.dumps(...).encode(...) + gzip.compress(...) path held several complete
    copies at once and could push the Streamlit worker over its memory limit.
    """
    buffer=io.BytesIO()
    encoder=json.JSONEncoder(ensure_ascii=False,default=str,separators=(",",":"))
    with gzip.GzipFile(fileobj=buffer,mode="wb",compresslevel=5) as compressed:
        for chunk in encoder.iterencode(value):
            compressed.write(chunk.encode("utf-8"))
    return buffer.getvalue()

def _from_json_bytes(value: Any) -> Any:
    if value in (None,b"",""): return None
    data=bytes(value) if not isinstance(value,bytes) else value
    with gzip.GzipFile(fileobj=io.BytesIO(data),mode="rb") as compressed:
        with io.TextIOWrapper(compressed,encoding="utf-8") as text:
            return json.load(text)

def _session_payload(session_state) -> dict[str,Any]:
    keys=(
        "project_name","analysis_time","result","object_registry_confirmed","object_assembly_rows",
        "completeness_user_confirmed","completeness_decisions","checklist_run","checklist_user_results",
        "risk_user_decisions","object_learning_examples"
    )
    out={}
    for k in keys:
        out[k]=session_state.get(k)
    return out


def snapshot_signature(payload: dict[str,Any]) -> str:
    """Return a cheap rerun signature without serialising the analysis result.

    The signature only decides whether the current Streamlit rerun must be
    persisted.  Evidence itself is still stored by ``save_project``.  Mutable
    user decisions are represented explicitly, while the immutable analysis is
    identified by object identity and small structural markers.
    """
    result=payload.get("result")
    result_parts=list(result) if isinstance(result,(list,tuple)) else []
    counts=[len(part) if isinstance(part,(list,tuple)) else 0 for part in result_parts[:3]]
    first_document={}
    if result_parts and isinstance(result_parts[0],list) and result_parts[0]:
        candidate=result_parts[0][0]
        if isinstance(candidate,dict):
            first_document=candidate
    object_decisions=[]
    for row in payload.get("object_assembly_rows") or []:
        if not isinstance(row,dict):
            continue
        object_decisions.append({
            "key":row.get("Ключ"),
            "include":bool(row.get("Включить")),
            "decision":row.get("Решение пользователя"),
            "comment":row.get("Комментарий пользователя"),
        })
    marker={
        "project_name":payload.get("project_name"),
        "analysis_time":payload.get("analysis_time"),
        "result_identity":id(result),
        "result_counts":counts,
        "core_version":first_document.get("core_version"),
        "quality_gate":(first_document.get("report_quality_gate") or {}).get("status") if isinstance(first_document.get("report_quality_gate"),dict) else None,
        "object_registry_confirmed":bool(payload.get("object_registry_confirmed")),
        "object_decisions":object_decisions,
        "completeness_user_confirmed":bool(payload.get("completeness_user_confirmed")),
        "completeness_decisions":payload.get("completeness_decisions") or {},
        "checklist_run_identity":id(payload.get("checklist_run")),
        "checklist_user_results":payload.get("checklist_user_results") or {},
        "risk_user_decisions":payload.get("risk_user_decisions") or {},
        "object_learning_examples":payload.get("object_learning_examples") or [],
    }
    raw=json.dumps(marker,ensure_ascii=False,default=str,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

@dataclass
class User:
    id: str
    email: str
    display_name: str
    created_at: str
    status: str="active"

class WorkspaceStore:
    """Private multi-user project store.

    SQLite is a development fallback. PostgreSQL is used when DATABASE_URL starts
    with postgres:// or postgresql://. Every project query is owner-scoped.
    """
    def __init__(self, database_url: str|None=None, base_dir: str|Path|None=None):
        self.database_url=(database_url or os.getenv("DATABASE_URL") or "").strip()
        self.base_dir=Path(base_dir or os.getenv("EXPERTCHECK_DATA_DIR") or ".expertcheck_data").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backend="postgres" if self.database_url.startswith(("postgres://","postgresql://")) else "sqlite"
        self.sqlite_path=self.base_dir/"workspace.sqlite3"
        self._init_schema()

    @property
    def persistent_mode(self) -> bool:
        return self.backend=="postgres"

    def _connect(self):
        if self.backend=="postgres":
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(self.database_url, row_factory=dict_row)
        con=sqlite3.connect(self.sqlite_path, timeout=30)
        con.row_factory=sqlite3.Row
        return con

    def _exec(self, con, sql: str, params=()):
        if self.backend=="postgres":
            sql=sql.replace("?","%s")
        return con.execute(sql,params)

    def _init_schema(self):
        with self._connect() as con:
            self._exec(con, """CREATE TABLE IF NOT EXISTS users(
                id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active'
            )""")
            self._exec(con, """CREATE TABLE IF NOT EXISTS projects(
                id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, name TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_analysis_at TEXT,
                status TEXT NOT NULL DEFAULT 'draft', payload BYTEA,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )""".replace("BYTEA","BLOB") if self.backend=="sqlite" else """CREATE TABLE IF NOT EXISTS projects(
                id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, name TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_analysis_at TEXT,
                status TEXT NOT NULL DEFAULT 'draft', payload BYTEA,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )""")
            self._exec(con, """CREATE INDEX IF NOT EXISTS idx_projects_owner_updated ON projects(owner_id, updated_at)""")
            self._exec(con, """CREATE TABLE IF NOT EXISTS analysis_runs(
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, owner_id TEXT NOT NULL,
                created_at TEXT NOT NULL, app_version TEXT, summary TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )""")
            con.commit()

    def register(self,email:str,password:str,display_name:str="") -> tuple[bool,str,User|None]:
        email=email.strip().lower()
        display_name=(display_name or email.split("@")[0]).strip()[:120]
        if not _EMAIL_RE.match(email): return False,"Укажите корректный email.",None
        if len(password)<8: return False,"Пароль должен содержать не менее 8 символов.",None
        if _PH is None: return False,"Модуль безопасного хеширования паролей не установлен.",None
        user_id=str(uuid.uuid4())
        pw=_PH.hash(password)
        try:
            with self._connect() as con:
                self._exec(con,"INSERT INTO users(id,email,display_name,password_hash,created_at,status) VALUES(?,?,?,?,?,?)",
                           (user_id,email,display_name,pw,_now(),"active"))
                con.commit()
            return True,"Регистрация завершена.",User(user_id,email,display_name,_now())
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                return False,"Пользователь с таким email уже зарегистрирован.",None
            return False,f"Не удалось создать пользователя: {type(exc).__name__}",None

    def authenticate(self,email:str,password:str) -> tuple[bool,str,User|None]:
        email=email.strip().lower()
        with self._connect() as con:
            row=self._exec(con,"SELECT id,email,display_name,password_hash,created_at,status FROM users WHERE email=?",(email,)).fetchone()
        if not row: return False,"Неверный email или пароль.",None
        data=dict(row) if not isinstance(row,dict) else row
        if data.get("status")!="active": return False,"Учётная запись отключена.",None
        try:
            if _PH is None or not _PH.verify(data["password_hash"],password):
                return False,"Неверный email или пароль.",None
        except Exception:
            return False,"Неверный email или пароль.",None
        return True,"Вход выполнен.",User(data["id"],data["email"],data["display_name"],data["created_at"],data["status"])

    def create_project(self,owner_id:str,name:str) -> str:
        pid=str(uuid.uuid4()); now=_now()
        with self._connect() as con:
            self._exec(con,"INSERT INTO projects(id,owner_id,name,created_at,updated_at,status) VALUES(?,?,?,?,?,?)",
                       (pid,owner_id,(name or "Новый проект").strip()[:250],now,now,"draft"))
            con.commit()
        return pid

    def list_projects(self,owner_id:str) -> list[dict[str,Any]]:
        with self._connect() as con:
            rows=self._exec(con,"SELECT id,name,created_at,updated_at,last_analysis_at,status FROM projects WHERE owner_id=? ORDER BY updated_at DESC",(owner_id,)).fetchall()
        return [dict(r) for r in rows]

    def load_project(self,owner_id:str,project_id:str) -> dict[str,Any]|None:
        with self._connect() as con:
            row=self._exec(con,"SELECT id,name,created_at,updated_at,last_analysis_at,status,payload FROM projects WHERE id=? AND owner_id=?",(project_id,owner_id)).fetchone()
        if not row: return None
        data=dict(row)
        data["payload"]=_from_json_bytes(data.get("payload")) or {}
        return data

    def save_project(self,owner_id:str,project_id:str,name:str,payload:dict[str,Any],status:str="analyzed",app_version:str=""):
        # Owner condition is part of UPDATE: a foreign project id cannot be overwritten.
        now=_now()
        blob=_json_bytes(payload)
        with self._connect() as con:
            cur=self._exec(con,"UPDATE projects SET name=?,updated_at=?,last_analysis_at=?,status=?,payload=? WHERE id=? AND owner_id=?",
                           ((name or "Проект").strip()[:250],now,now,status,blob,project_id,owner_id))
            if getattr(cur,"rowcount",0)!=1:
                raise PermissionError("Проект не найден или не принадлежит текущему пользователю.")
            # Store one immutable history row per actual analysis run, not per UI rerun.
            analysis_time=str(payload.get("analysis_time") or "")
            latest=self._exec(con,"SELECT summary FROM analysis_runs WHERE project_id=? AND owner_id=? ORDER BY created_at DESC LIMIT 1",
                              (project_id,owner_id)).fetchone()
            latest_summary={}
            if latest:
                raw=(dict(latest).get("summary") if not isinstance(latest,dict) else latest.get("summary")) or "{}"
                try: latest_summary=json.loads(raw)
                except Exception: latest_summary={}
            if analysis_time and latest_summary.get("analysis_time") != analysis_time:
                self._exec(con,"INSERT INTO analysis_runs(id,project_id,owner_id,created_at,app_version,summary) VALUES(?,?,?,?,?,?)",
                           (str(uuid.uuid4()),project_id,owner_id,now,app_version,json.dumps({
                               "analysis_time":analysis_time,
                               "object_registry_confirmed":payload.get("object_registry_confirmed",False)
                           },ensure_ascii=False)))
            con.commit()

    def delete_project(self,owner_id:str,project_id:str) -> bool:
        with self._connect() as con:
            self._exec(con,"DELETE FROM analysis_runs WHERE project_id=? AND owner_id=?",(project_id,owner_id))
            cur=self._exec(con,"DELETE FROM projects WHERE id=? AND owner_id=?",(project_id,owner_id))
            con.commit()
        return getattr(cur,"rowcount",0)==1

    def analysis_history(self,owner_id:str,project_id:str,limit:int=20) -> list[dict[str,Any]]:
        with self._connect() as con:
            rows=self._exec(con,"SELECT id,created_at,app_version,summary FROM analysis_runs WHERE project_id=? AND owner_id=? ORDER BY created_at DESC LIMIT ?",
                            (project_id,owner_id,int(limit))).fetchall()
        return [dict(r) for r in rows]

def get_store(secrets=None, base_dir: str|Path|None=None) -> WorkspaceStore:
    db=""
    try:
        db=str((secrets or {}).get("DATABASE_URL") or "")
    except Exception:
        pass
    return WorkspaceStore(db or None, base_dir=base_dir)

def session_snapshot(session_state) -> dict[str,Any]:
    return _session_payload(session_state)
