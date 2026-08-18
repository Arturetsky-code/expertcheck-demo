
from pathlib import Path
import tempfile, shutil
from core.workspace_store import WorkspaceStore

def test_user_project_isolation():
    root=Path(tempfile.mkdtemp())
    try:
        store=WorkspaceStore(base_dir=root)
        ok,_,u1=store.register("owner@example.com","Password123","Owner")
        ok2,_,u2=store.register("other@example.com","Password456","Other")
        assert ok and ok2
        pid=store.create_project(u1.id,"Private")
        payload={"project_name":"Private","analysis_time":"2026-08-18T15:00","result":[[],[],[]]}
        store.save_project(u1.id,pid,"Private",payload,app_version="9.0")
        assert store.load_project(u1.id,pid)["name"]=="Private"
        assert store.load_project(u2.id,pid) is None
        try:
            store.save_project(u2.id,pid,"Attack",payload)
            assert False, "foreign write must be blocked"
        except PermissionError:
            pass
        assert len(store.list_projects(u2.id))==0
    finally:
        shutil.rmtree(root,ignore_errors=True)

def test_password_not_stored_plaintext_and_auth_works():
    root=Path(tempfile.mkdtemp())
    try:
        store=WorkspaceStore(base_dir=root)
        ok,_,u=store.register("user@example.com","SecretPass9","User")
        assert ok
        ok,_,logged=store.authenticate("user@example.com","SecretPass9")
        assert ok and logged.id==u.id
        ok,_,_=store.authenticate("user@example.com","wrong")
        assert not ok
        with store._connect() as con:
            row=store._exec(con,"SELECT password_hash FROM users WHERE id=?",(u.id,)).fetchone()
        value=(dict(row)["password_hash"] if not isinstance(row,dict) else row["password_hash"])
        assert value!="SecretPass9"
        assert value.startswith("$argon2")
    finally:
        shutil.rmtree(root,ignore_errors=True)

def test_history_only_once_per_analysis():
    root=Path(tempfile.mkdtemp())
    try:
        store=WorkspaceStore(base_dir=root)
        _,_,u=store.register("history@example.com","Password123","History")
        pid=store.create_project(u.id,"P")
        payload={"analysis_time":"2026-08-18T15:10","result":[[],[],[]]}
        store.save_project(u.id,pid,"P",payload,app_version="9.0")
        payload["object_registry_confirmed"]=True
        store.save_project(u.id,pid,"P",payload,app_version="9.0")
        assert len(store.analysis_history(u.id,pid))==1
    finally:
        shutil.rmtree(root,ignore_errors=True)
