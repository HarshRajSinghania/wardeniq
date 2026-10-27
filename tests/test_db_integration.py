"""DB integration tests: exercise store.py against a REAL MongoDB, as opposed
to the mocked-Store unit tests elsewhere in tests/.

Requires MONGO_TEST_URI (e.g. mongodb://localhost:27017). If it's unset or the
server is unreachable, every test here is skipped — so a plain `pytest` run on
a laptop without MongoDB running still passes. CI runs these explicitly via
`pytest -m dbintegration` in the "db-integration-tests" job, which brings up a
`mongo` service container (see .github/workflows/ci.yml).

Scope note: this uses a single standalone `mongo` container, which has no
mongot / Atlas Search. `Store.ensure_indexes()` therefore fails partway
through (once it reaches the vector/text search indexes) — expected here, and
tolerated below — so vectorSearch-backed methods (search_features,
search_cases, dedup, ...) are NOT covered by this suite. Those need the full
docker-compose stack (PSMDB + mongot) and are exercised manually / in a real
deployment, per CLAUDE.md's architecture notes.

Each test gets its own throwaway database (dropped at teardown) so runs never
collide or leave data behind.
"""
import os
import time
import uuid

import pytest
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

pytestmark = pytest.mark.dbintegration

MONGO_TEST_URI = os.getenv("MONGO_TEST_URI", "mongodb://localhost:27017")


@pytest.fixture(scope="module", autouse=True)
def _require_mongo():
    """Open a short-lived client only when the module's tests actually run.

    Doing the reachability check at import time (the previous pattern) opened a
    MongoClient — and waited the full serverSelectionTimeout — even when the
    dbintegration marker was deselected, and the client was never closed.
    """
    client = None
    try:
        client = MongoClient(MONGO_TEST_URI, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
    except Exception:  # noqa: BLE001
        pytest.skip(
            f"no MongoDB reachable at {MONGO_TEST_URI!r} (set MONGO_TEST_URI to run "
            "db-integration tests)",
            allow_module_level=False,
        )
    finally:
        if client is not None:
            client.close()

# Import after the reachability check so a module without a live Mongo never
# pays the cost of importing store.py for nothing.
from store import Store  # noqa: E402
