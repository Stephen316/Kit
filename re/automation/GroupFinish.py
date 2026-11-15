from pathlib import Path

from GroupClaims import mark_solo, read_group, renew_group
from OutputManifest import MAX_OUTPUT_BYTES, InvalidOutput, output_manifest
from Records import StaleLease, read_record, reason_text


def finish_group(ledger, claim_path, request_path):
    claims = read_group(claim_path)
    request_path = Path(request_path)
    request = read_record(request_path)
    if set(request) != {"group_finish_version", "members"} or type(request["group_finish_version"]) is not int or request["group_finish_version"] != 1:
        raise ValueError("group finish must use protocol 1")
    if not isinstance(request["members"], list) or len(request["members"]) != len(claims):
        raise ValueError("group finish count does not match claims")
    records, total = [], 0
    for index, item in enumerate(request["members"]):
        renew_group(ledger, claims)
        if not isinstance(item, dict) or set(item) != {"outcome", "reason"}:
            raise ValueError("group finish member fields do not match protocol 1")
        reason_text(item["reason"])
        path = request_path.parent / "jobs" / f"{index:02d}" / "finish.json"
        payload = read_record(path)
        declared = payload.get("result")
        manifest = output_manifest(declared["artifacts"]) if isinstance(declared, dict) and "artifacts" in declared else None
        total += sum(value["size_bytes"] for value in manifest.values()) if manifest is not None else 0
        records.append((item["outcome"], item["reason"], path, payload, manifest is not None))
    oversized = total > MAX_OUTPUT_BYTES
    results = []
    for claim, (outcome, reason, path, payload, intake) in zip(claims, records):
        renew_group(ledger, claims)
        if oversized:
            outcome, reason, intake = "retry", "group output declarations exceed 256 MiB in aggregate", False
            payload = {**payload, "result": None, "error": reason}
        if outcome == "retry":
            mark_solo(ledger, claim)
        ledger.db.execute("SAVEPOINT group_member")
        try:
            ledger.finish(claim["job"]["id"], claim["lease_token"], outcome, path, reason, path.parent / "work" if intake else None, payload)
        except InvalidOutput as error:
            ledger.db.execute("ROLLBACK TO group_member")
            outcome, reason = "retry", f"invalid output artifacts: {error}"[:2048]
            mark_solo(ledger, claim)
            payload = {**payload, "result": None, "error": reason}
            try:
                ledger.finish(claim["job"]["id"], claim["lease_token"], outcome, path, reason, result_record=payload)
            except StaleLease:
                results.append({"stale": True, "outcome": None, "reason": reason})
            else:
                results.append({"stale": False, "outcome": outcome, "reason": reason})
        except StaleLease:
            ledger.db.execute("ROLLBACK TO group_member")
            mark_solo(ledger, claim)
            results.append({"stale": True, "outcome": None, "reason": reason})
        else:
            results.append({"stale": False, "outcome": outcome, "reason": reason})
        finally:
            ledger.db.execute("RELEASE group_member")
    return {"members": results}
