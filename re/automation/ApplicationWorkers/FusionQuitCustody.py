import json
import os
import re
import stat

from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    directory,
    encoded,
    file_bytes,
    require,
    sha256,
)
from AuditFusionPhases import StoreSnapshot, phase_row, validate_queue
from StoreRead import read_store


class FusionQuitCustody:
    def __init__(
        self,
        root,
        installation,
        installation_bytes,
        store,
        queue,
        lifecycle,
        readiness,
        *,
        handoff_id=None,
    ):
        self.root = root
        self.installation = installation
        self.queue_path = queue
        self.lifecycle = lifecycle
        self.installation_bytes = installation_bytes
        self.queue_bytes = file_bytes(queue)
        self.lifecycle_bytes = file_bytes(lifecycle)
        retained = file_bytes(root / "fence.json") if handoff_id is None else None
        if handoff_id is None:
            handoff_id = json.loads(retained)["job_id"]
        require(
            re.fullmatch("[0-9a-f]{32}", handoff_id),
            "invalid retained Fusion restart ID",
        )
        self.handoff_id = handoff_id
        self.intent_path = root / f"restart-intent-{handoff_id}.json"
        self.intent_bytes = file_bytes(self.intent_path)
        self.intent = json.loads(self.intent_bytes)
        self.fence_bytes = encoded(self.intent["restart_handoff"])
        self.store = directory(store)
        self.database = self.store / "ledger.sqlite3"
        self.queue = validate_queue(json.loads(self.queue_bytes))
        self.fence_sha256 = sha256(self.fence_bytes)
        require(
            sha256(self.intent_bytes) == readiness["intent_sha256"]
            and self.intent["installation_sha256"]
            == readiness["installation_sha256"]
            == sha256(installation_bytes)
            and sha256(self.queue_bytes) == self.intent["queue_receipt_sha256"]
            and sha256(self.lifecycle_bytes) == readiness["lifecycle_sha256"]
            and self.fence_sha256 == self.intent["fence_sha256"]
            and self.intent["restart_handoff"]["job_id"] == handoff_id
            and (retained is None or retained == self.fence_bytes)
            and sha256(os.fsencode(self.store)) == self.intent["store_path_sha256"],
            "Fusion exit observer inputs differ from the accepted restart intent",
        )

    def verify_files(self, retained):
        require(
            file_bytes(self.installation) == self.installation_bytes
            and file_bytes(self.queue_path) == self.queue_bytes
            and file_bytes(self.lifecycle) == self.lifecycle_bytes
            and file_bytes(self.intent_path) == self.intent_bytes,
            "Fusion restart custody differs from the accepted owner inputs",
        )
        if retained:
            require(
                file_bytes(self.root / "fence.json") == self.fence_bytes
                and not os.path.lexists(self.root / ACKNOWLEDGEMENT)
                and not any(directory(self.root / "jobs").iterdir()),
                "Fusion restart custody lost the original acknowledged fence",
            )

    def verify(self, *, retained=True):
        self.verify_files(retained)
        database = self.database.lstat()
        require(
            stat.S_ISREG(database.st_mode) and database.st_nlink == 1,
            "Fusion exit watch requires the original private A03 store",
        )
        with read_store(self.database, None, (4,)) as connection:
            owner = StoreSnapshot(connection, self.store)
            row = phase_row(owner, self.queue, "a")
            expected = {
                "id": self.intent["controller_job"],
                "state": "completed",
                "attempts": self.intent["attempt"],
                "generation": self.intent["generation"],
                "fingerprint": self.intent["fingerprint"],
                "receipt": self.intent["receipt_sha256"],
                "result": self.intent["result_sha256"],
            }
            require(
                all(row[key] == value for key, value in expected.items())
                and (
                    not retained
                    or phase_row(owner, self.queue, "b")["state"] != "completed"
                ),
                "Fusion exit watch lost the accepted Phase A attempt",
            )
        self.verify_files(retained)
