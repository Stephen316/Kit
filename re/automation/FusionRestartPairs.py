import hashlib
import json
import re

from Records import digest, specification

POLICY = "fusion_restart_pairs_version"
VERSION = 1
PAIR_TABLE = """CREATE TABLE fusion_restart_pairs (
    phase_a TEXT PRIMARY KEY,
    phase_b TEXT NOT NULL UNIQUE,
    a_definition TEXT NOT NULL,
    b_definition TEXT NOT NULL,
    resource TEXT NOT NULL,
    installation TEXT NOT NULL,
    installation_sha256 TEXT NOT NULL,
    queue_sha256 TEXT NOT NULL,
    plan_sha256 TEXT NOT NULL,
    a_generation INTEGER,
    a_attempt INTEGER,
    a_fingerprint TEXT,
    a_receipt TEXT,
    a_result TEXT,
    restart_intent TEXT,
    b_receipt TEXT,
    b_result TEXT,
    final_evidence TEXT
)"""
RESOURCE_INDEX = """CREATE UNIQUE INDEX fusion_restart_resource ON fusion_restart_pairs(resource)
    WHERE a_receipt IS NOT NULL AND final_evidence IS NULL"""


def exact_first(job, pair):
    return (
        f"{job}.id={pair}.phase_a AND {job}.definition_hash={pair}.a_definition "
        f"AND {job}.state='completed' AND {job}.generation={pair}.a_generation "
        f"AND {job}.attempts={pair}.a_attempt AND {job}.fingerprint={pair}.a_fingerprint "
        f"AND {job}.receipt={pair}.a_receipt AND {job}.result={pair}.a_result"
    )


def excludes_claim(candidate):
    return f"""EXISTS (
        SELECT 1 FROM fusion_restart_pairs reservation
        JOIN job_resources held ON held.resource=reservation.resource
        WHERE held.job_id={candidate}.id AND reservation.a_receipt IS NOT NULL
          AND reservation.final_evidence IS NULL
          AND NOT (
              reservation.restart_intent IS NOT NULL
              AND {candidate}.id=reservation.phase_b
              AND {candidate}.definition_hash=reservation.b_definition
              AND EXISTS (
                  SELECT 1 FROM jobs accepted WHERE {exact_first("accepted", "reservation")}
              )
          )
    )"""


CLAIM_GUARD = f"""CREATE TRIGGER fusion_restart_claim_guard
BEFORE UPDATE OF state ON jobs
WHEN OLD.state<>'running' AND NEW.state='running' AND {excludes_claim("NEW")}
BEGIN
    SELECT RAISE(ABORT, 'resource reserved for the exact acknowledged Fusion restart');
END"""

ACCEPT_GUARD = f"""CREATE TRIGGER fusion_restart_accept_guard
BEFORE UPDATE OF state ON jobs
WHEN OLD.state<>'completed' AND NEW.state='completed'
    AND EXISTS (SELECT 1 FROM fusion_restart_pairs WHERE phase_a=NEW.id)
    AND NOT EXISTS (
        SELECT 1 FROM fusion_restart_pairs pair
        WHERE {exact_first("NEW", "pair")} AND pair.final_evidence IS NULL
    )
BEGIN
    SELECT RAISE(ABORT, 'registered Fusion Phase A requires its exact atomic restart reservation');
END"""

SCHEMA = {
    "fusion_restart_pairs": PAIR_TABLE,
    "fusion_restart_resource": RESOURCE_INDEX,
    "fusion_restart_claim_guard": CLAIM_GUARD,
    "fusion_restart_accept_guard": ACCEPT_GUARD,
}


def installed(ledger):
    row = ledger.db.execute(
        "SELECT value FROM settings WHERE key=?", (POLICY,)
    ).fetchone()
    if row is None:
        return False
    if row[0] != VERSION:
        raise ValueError("unsupported A03 Fusion restart reservation policy")
    return True


def verify_schema(ledger):
    saved = ledger.db.execute(
        "SELECT name,sql FROM sqlite_master WHERE name IN (?,?,?,?)",
        tuple(SCHEMA),
    ).fetchall()
    if {row["name"]: row["sql"] for row in saved} != SCHEMA:
        raise ValueError(
            "A03 Fusion restart reservation schema differs from the reviewed policy"
        )


def register_pair(ledger, queue, jobs, queue_sha256, installation_sha256):
    if not installed(ledger):
        for declaration in SCHEMA.values():
            ledger.db.execute(declaration)
        ledger.db.execute("INSERT INTO settings VALUES (?,?)", (POLICY, VERSION))
    verify_schema(ledger)
    first, second = (specification(job) for job in jobs)
    registration = {
        "phase_a": first["id"],
        "phase_b": second["id"],
        "a_definition": digest(first),
        "b_definition": digest(second),
        "resource": queue["resource"],
        "installation": queue["installation"],
        "installation_sha256": installation_sha256,
        "queue_sha256": queue_sha256,
        "plan_sha256": queue["plan_sha256"],
    }
    old = ledger.db.execute(
        "SELECT * FROM fusion_restart_pairs WHERE phase_a=?", (first["id"],)
    ).fetchone()
    if old is not None:
        if not same_values(old, registration):
            raise ValueError("existing Fusion restart registration differs")
        return
    if (
        ledger.db.execute(
            "SELECT 1 FROM attempts WHERE job_id IN (?,?) LIMIT 1",
            (first["id"], second["id"]),
        ).fetchone()
        is not None
    ):
        raise ValueError("Fusion restart registration must predate the first attempt")
    ledger.db.execute(
        "INSERT INTO fusion_restart_pairs("
        "phase_a,phase_b,a_definition,b_definition,resource,installation,"
        "installation_sha256,queue_sha256,plan_sha256) VALUES (?,?,?,?,?,?,?,?,?)",
        tuple(registration.values()),
    )
    ledger.event(
        first["id"], "fusion_restart_pair_registered", {"resource": queue["resource"]}
    )


def same_values(row, expected):
    return all(row[key] == value for key, value in expected.items())


def pair_for(ledger, phase_a):
    if not installed(ledger):
        return None
    return ledger.db.execute(
        "SELECT * FROM fusion_restart_pairs WHERE phase_a=?", (phase_a,)
    ).fetchone()


def accepted_hold(ledger, first, spec, result, owner, receipt, result_hash):
    pair = pair_for(ledger, first["id"])
    if pair is None:
        return
    verify_schema(ledger)
    authority = (
        ledger.db.execute(
            "SELECT token_hash FROM supervisor_owner WHERE id=1 AND version=1"
        ).fetchone()
        if owner is not None
        else None
    )
    ack = result.get("application_acknowledgement_sha256")
    record = result["result"]["records"]["restart_handoff"]
    resource = ledger.db.execute(
        "SELECT capacity FROM resources WHERE name=?", (pair["resource"],)
    ).fetchone()
    if (
        authority is None
        or authority["token_hash"] != owner
        or not isinstance(ack, str)
        or not re.fullmatch("[0-9a-f]{64}", ack)
        or record["reason"] != "restart_required"
        or record["owner"] != "external_application_owner"
        or not isinstance(record["job_id"], str)
        or not re.fullmatch("[0-9a-f]{32}", record["job_id"])
        or record["installation"] != pair["installation"]
        or record["plan_sha256"] != pair["plan_sha256"]
        or spec["resources"] != [pair["resource"]]
        or first["definition_hash"] != pair["a_definition"]
        or second_definition(ledger, pair) is None
        or resource is None
        or resource["capacity"] != 1
        or pair["a_receipt"] is not None
    ):
        raise ValueError(
            "automatic Fusion Phase A settlement lacks its registered owner or handoff"
        )
    ledger.db.execute(
        "UPDATE fusion_restart_pairs SET a_generation=?,a_attempt=?,a_fingerprint=?,"
        "a_receipt=?,a_result=? WHERE phase_a=?",
        (
            first["generation"],
            first["attempts"],
            first["fingerprint"],
            receipt,
            result_hash,
            first["id"],
        ),
    )
    ledger.event(
        first["id"],
        "fusion_restart_reserved",
        {"resource": pair["resource"], "receipt": receipt},
    )


def second_definition(ledger, pair):
    return ledger.db.execute(
        "SELECT * FROM jobs WHERE id=? AND definition_hash=?",
        (pair["phase_b"], pair["b_definition"]),
    ).fetchone()


def bound_pair(ledger, queue, installation_sha256, active):
    verify_schema(ledger)
    pair = pair_for(ledger, queue["jobs"]["a"])
    if pair is None or not same_values(
        pair,
        {
            "phase_b": queue["jobs"]["b"],
            "resource": queue["resource"],
            "installation": queue["installation"],
            "installation_sha256": installation_sha256,
            "queue_sha256": active["queue_receipt_sha256"],
            "plan_sha256": queue["plan_sha256"],
            "a_receipt": active["receipt_sha256"],
            "a_result": active["result_sha256"],
            "a_generation": active["generation"],
            "a_attempt": active["attempt"],
            "a_fingerprint": active["fingerprint"],
        },
    ):
        raise ValueError(
            "Fusion restart custody differs from the exact accepted reservation"
        )
    first = ledger.db.execute(
        f"SELECT 1 FROM jobs accepted JOIN fusion_restart_pairs pair ON {exact_first('accepted', 'pair')} "
        "WHERE pair.phase_a=?",
        (pair["phase_a"],),
    ).fetchone()
    if first is None:
        raise ValueError("reserved Fusion Phase A was replaced or invalidated")
    return pair


def open_pair(ledger, queue, installation_sha256, active):
    pair = bound_pair(ledger, queue, installation_sha256, active)
    intent = active["restart_intent_sha256"]
    if pair["restart_intent"] == intent:
        return
    second = second_definition(ledger, pair)
    resource = ledger.db.execute(
        "SELECT capacity,available FROM resources WHERE name=?", (pair["resource"],)
    ).fetchone()
    if (
        pair["restart_intent"] is not None
        or pair["final_evidence"] is not None
        or second is None
        or second["state"] != "queued"
        or resource is None
        or resource["capacity"] != 1
        or not resource["available"]
    ):
        raise ValueError(
            "Fusion Phase B cannot open its exact retained restart reservation"
        )
    ledger.db.execute(
        "UPDATE fusion_restart_pairs SET restart_intent=? WHERE phase_a=?",
        (intent, pair["phase_a"]),
    )
    ledger.event(
        pair["phase_b"],
        "fusion_restart_admitted",
        {"resource": pair["resource"], "intent": intent},
    )


def release_pair(ledger, queue, installation_sha256, active, final_bytes):
    pair = bound_pair(ledger, queue, installation_sha256, active)
    final = json.loads(final_bytes)
    evidence = final["phase_b"]
    checksum = hashlib.sha256(final_bytes).hexdigest()
    second = second_definition(ledger, pair)
    if (
        pair["restart_intent"] != active["restart_intent_sha256"]
        or final["restart_intent_sha256"] != pair["restart_intent"]
        or final["scope"] != "fusion_owner_lifecycle"
        or evidence["status"] != "replacement_phase_b_verified"
        or second is None
        or second["state"] != "completed"
        or evidence["phase_b_receipt_sha256"] != second["receipt"]
        or evidence["phase_b_result_sha256"] != second["result"]
        or json.loads(second["snapshot"])["dependencies"].get(pair["phase_a"])
        != {
            "receipt": pair["a_receipt"],
            "result": pair["a_result"],
        }
    ):
        raise ValueError(
            "final Fusion Phase B does not release the exact reserved pair"
        )
    if pair["final_evidence"] is not None:
        if not same_values(
            pair,
            {
                "b_receipt": second["receipt"],
                "b_result": second["result"],
                "final_evidence": checksum,
            },
        ):
            raise ValueError(
                "Fusion restart reservation was released with different evidence"
            )
        return
    ledger.objects.verify(second["receipt"])
    ledger.objects.verify(second["result"])
    ledger.db.execute(
        "UPDATE fusion_restart_pairs SET b_receipt=?,b_result=?,final_evidence=? WHERE phase_a=?",
        (second["receipt"], second["result"], checksum, pair["phase_a"]),
    )
    ledger.event(
        pair["phase_b"],
        "fusion_restart_released",
        {"resource": pair["resource"], "evidence": checksum},
    )
