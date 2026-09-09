import os
import sys
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbtest")


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._conn["rollback_called"] = True
        return False

    def execute(self, sql, params=None):
        self._conn["executed_sql"] = sql
        self._conn["executed_params"] = params
        sql_lower = sql.lower().strip()
        if sql_lower.startswith("select"):
            self._conn["fetchall_calls"] += 1
        elif sql_lower.startswith("delete"):
            self.rowcount = 1 if self._conn["should_delete"] else 0
        elif sql_lower.startswith("insert"):
            self._conn["inserted"] = True

    def fetchall(self):
        return self._conn["next_fetchall_result"]


class _FakeConn:
    def __init__(self, state):
        self._state = state

    def cursor(self):
        return _FakeCursor(self._state)

    def commit(self):
        self._state["committed"] = True

    def rollback(self):
        self._state["rollback_called"] = True

    def close(self):
        self._state["closed"] = True


@pytest.fixture
def fake_db():
    state = {
        "committed": False,
        "rollback_called": False,
        "closed": False,
        "should_delete": True,
        "next_fetchall_result": [],
        "fetchall_calls": 0,
        "inserted": False,
        "executed_sql": None,
        "executed_params": None,
    }

    def _fake_connect(*args, **kwargs):
        return _FakeConn(state)

    with patch("app.psycopg2.connect", side_effect=_fake_connect), \
         patch("app.conectar_db", side_effect=_fake_connect):
        yield state


@pytest.fixture
def app_module(fake_db):
    import importlib
    import app as app_module
    importlib.reload(app_module)
    yield app_module
    importlib.reload(app_module)


@pytest.fixture
def client(app_module):
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
