import shutil
import time
from pathlib import Path

from GroupClaims import read_group
from OutputManifest import MAX_OUTPUT_BYTES
from Sessions import Session, write_private


def release_group(supervisor, name, claim_path, receipt, reason, directory):
    claims = read_group(claim_path)
    directory = Path(directory)
    directory.mkdir(mode=0o700, exist_ok=True)
    (directory / "jobs").mkdir(mode=0o700, exist_ok=True)
    for index, claim in enumerate(claims):
        member = directory / "jobs" / f"{index:02d}"
        member.mkdir(mode=0o700, exist_ok=True)
        write_private(member / "finish.json", {"session_version": 1, "receipt": {**receipt, "job_id": claim["job"]["id"], "attempt": claim["attempt"], "group_size": len(claims)}, "result": None, "error": reason, "stderr_tail": None})
    request = directory / "group-finish.json"
    write_private(request, {"group_finish_version": 1, "members": [{"outcome": "retry", "reason": reason} for _ in claims]})
    response = supervisor.adapter.FinishGroup(claim_path, request)
    supervisor.report("group_released", None, {"session": name, "group_size": len(claims), "members": response["members"]})
    shutil.rmtree(claim_path)


class GroupSession(Session):
    def __init__(self, supervisor, pool, claims, claim_path, name):
        super().__init__(supervisor, pool, claims[0], claim_path, name)
        self.deadline = min(claim["deadline"] for claim in claims)
        self.stop_at = min(claim["deadline"] - min(supervisor.grace + 2, claim["job"]["timeout_seconds"] / 2) for claim in claims)
        self.renew_every = min(claim["job"]["lease_seconds"] for claim in claims) / 3
        self.next_renew = self.started + self.renew_every
        self.members = []
        for index, claim in enumerate(claims):
            member = Session(supervisor, pool, claim, claim_path, name)
            member.directory = self.directory / "jobs" / f"{index:02d}"
            member.stop_at = self.stop_at
            member.preparation_heartbeat = self.keep_leases
            self.members.append(member)

    def keep_leases(self):
        now = time.time()
        for session in self.supervisor.running.values():
            if session.stop_reason is None and now >= session.next_renew:
                session.renew(now)
        if now < self.next_renew:
            return
        renewed = self.supervisor.adapter.RenewGroup(self.claim_path)
        if renewed["stale"]:
            raise ValueError("group lease became stale during input preparation")
        self.next_renew = now + self.renew_every

    def prepare(self):
        self.directory.mkdir(mode=0o700)
        (self.directory / "work").mkdir(mode=0o700)
        (self.directory / "jobs").mkdir(mode=0o700)
        paths = []
        self.next_renew = 0
        for index, member in enumerate(self.members):
            self.keep_leases()
            member.prepare()
            paths.append(f"jobs/{index:02d}/job.json")
        self.next_renew = 0
        self.keep_leases()
        write_private(self.directory / "group.json", {"group_session_version": 1, "session": self.name, "pool": self.pool, "members": paths, "stop_at": self.stop_at})

    def complete(self, exit_info):
        receipt = {**self.exit_receipt(exit_info), "group_session_version": 1, "group_size": len(self.members)}
        write_private(self.directory / "receipt.json", receipt)
        records, total = [], 0
        for member in self.members:
            member.stop_reason = self.stop_reason
            item = member.result_payload({**receipt, "job_id": member.spec["id"], "attempt": member.claim["attempt"]})
            result = item[2]["result"]
            if isinstance(result, dict):
                total += sum(value["size_bytes"] for value in result.get("artifacts", {}).values())
            records.append(item)
        if total > MAX_OUTPUT_BYTES:
            reason = "group output declarations exceed 256 MiB in aggregate"
            records = [("retry", reason, {**payload, "result": None, "error": reason}) for _, _, payload in records]
        for member, (_, _, payload) in zip(self.members, records):
            write_private(member.directory / "finish.json", payload)
        path = self.directory / "group-finish.json"
        write_private(path, {"group_finish_version": 1, "members": [{"outcome": outcome, "reason": reason} for outcome, reason, _ in records]})
        response = self.supervisor.adapter.FinishGroup(self.claim_path, path)
        results = response.get("members") if isinstance(response, dict) else None
        if not isinstance(results, list) or len(results) != len(self.members) or any(not isinstance(item, dict) or type(item.get("stale")) is not bool or not item["stale"] and item.get("outcome") not in {"completed", "retry", "rejected", "waiting_evidence", "waiting_ci", "waiting_application"} for item in results):
            raise ValueError("group finish response does not match member count and outcome contract")
        accepted = []
        for member, result in zip(self.members, results):
            if result["stale"]:
                self.supervisor.counts["stale"] += 1
            else:
                finished = self.supervisor.counts["finished"]
                finished[result["outcome"]] = finished.get(result["outcome"], 0) + 1
            accepted.append(not result["stale"] and result["outcome"] == "completed")
            self.supervisor.report("finished", member, {**result, "receipt": {**receipt, "job_id": member.spec["id"], "attempt": member.claim["attempt"]}})
        self.supervisor.budget.record(self.spec, self.name, "completed" if all(accepted) else "retry", False, receipt, self.supervisor.report)
        self.remove()
        return True
