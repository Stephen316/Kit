from ApplicationHolds import holds_installed
from FusionRestartPairs import pair_for, second_definition, verify_schema

POLICY = "fusion_cold_start_version"
TABLE = """CREATE TABLE fusion_cold_start (
    resource TEXT PRIMARY KEY,
    phase_a TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    generation INTEGER NOT NULL,
    fingerprint TEXT NOT NULL,
    request TEXT NOT NULL UNIQUE,
    startup_receipt TEXT
)"""


def excludes_claim(job):
    return f"""EXISTS (
        SELECT 1 FROM fusion_cold_start boot
        JOIN job_resources claimed ON claimed.resource=boot.resource
        WHERE claimed.job_id={job}.id AND NOT EXISTS (
            SELECT 1 FROM fusion_restart_pairs pair WHERE pair.phase_a=boot.phase_a
                AND pair.resource=boot.resource AND pair.a_definition=boot.definition
                AND pair.a_generation=boot.generation AND pair.a_fingerprint=boot.fingerprint
                AND pair.a_receipt IS NOT NULL
        )
          AND NOT (boot.startup_receipt IS NOT NULL AND {job}.id=boot.phase_a
                   AND {job}.definition_hash=boot.definition AND {job}.generation=boot.generation
                   AND {job}.fingerprint=boot.fingerprint AND EXISTS (
                       SELECT 1 FROM fusion_restart_pairs pair WHERE pair.phase_a=boot.phase_a
                       AND pair.resource=boot.resource AND pair.a_definition=boot.definition
                       AND pair.a_receipt IS NULL
                   ))
    )"""


GUARD = f"""CREATE TRIGGER fusion_cold_start_claim_guard
BEFORE UPDATE OF state ON jobs
WHEN OLD.state<>'running' AND NEW.state='running' AND {excludes_claim("NEW")}
BEGIN
    SELECT RAISE(ABORT, 'resource reserved for exact Fusion initial startup');
END"""


def installed(ledger):
    setting = ledger.db.execute(
        "SELECT value FROM settings WHERE key=?", (POLICY,)
    ).fetchone()
    if setting is None:
        return False
    if setting[0] != 1:
        raise ValueError("unsupported Fusion initial admission policy")
    return True


def install(ledger):
    if not installed(ledger):
        ledger.db.execute(TABLE)
        ledger.db.execute(GUARD)
        ledger.db.execute("INSERT INTO settings VALUES (?,1)", (POLICY,))
    verify_cold_schema(ledger)


# an archive retry must verify the existing claim guard without installing a new reservation
def verify_cold_schema(ledger):
    if not installed(ledger):
        raise ValueError("missing Fusion initial admission policy")
    rows = ledger.db.execute(
        "SELECT name,sql FROM sqlite_master WHERE name IN ('fusion_cold_start','fusion_cold_start_claim_guard')"
    ).fetchall()
    if {row["name"]: row["sql"] for row in rows} != {
        "fusion_cold_start": TABLE,
        "fusion_cold_start_claim_guard": GUARD,
    }:
        raise ValueError(
            "Fusion initial admission schema differs from its reviewed policy"
        )


def prior(ledger, resource):
    if not installed(ledger):
        return None
    return ledger.db.execute(
        "SELECT * FROM fusion_cold_start WHERE resource=?", (resource,)
    ).fetchone()


def initial_snapshot(ledger, queue, queue_sha, install_sha):
    resource = queue["resource"]
    phase = queue["jobs"]["a"]
    pair = pair_for(ledger, phase)
    if pair is None:
        raise ValueError(
            "initial startup requires an explicitly registered Fusion lifecycle pair"
        )
    verify_schema(ledger)
    first = ledger.db.execute("SELECT * FROM jobs WHERE id=?", (phase,)).fetchone()
    second = second_definition(ledger, pair)
    counted = ledger.db.execute(
        "SELECT capacity,available FROM resources WHERE name=?", (resource,)
    ).fetchone()
    if (
        pair["phase_b"] != queue["jobs"]["b"]
        or pair["resource"] != resource
        or pair["installation"] != queue["installation"]
        or pair["queue_sha256"] != queue_sha
        or pair["installation_sha256"] != install_sha
        or pair["plan_sha256"] != queue["plan_sha256"]
        or pair["a_receipt"] is not None
        or first is None
        or first["definition_hash"] != pair["a_definition"]
        or first["state"] != "waiting_application"
        or first["attempts"] != 0
        or first["parked"]
        or not first["fingerprint"]
        or first["generation"] <= 0
        or second is None
        or second["state"] != "waiting_evidence"
        or second["attempts"] != 0
        or counted is None
        or counted["capacity"] != 1
        or counted["available"]
        or blocked(ledger, resource)
    ):
        raise ValueError(
            "Fusion initial startup lost its exact unattempted and unavailable pair"
        )
    return {
        "resource": resource,
        "phase_a": phase,
        "definition": first["definition_hash"],
        "generation": first["generation"],
        "fingerprint": first["fingerprint"],
    }


def blocked(ledger, resource):
    if (
        holds_installed(ledger)
        and ledger.db.execute(
            "SELECT 1 FROM application_holds WHERE resource=? AND job_id IS NOT NULL",
            (resource,),
        ).fetchone()
    ):
        return True
    if ledger.db.execute(
        "SELECT 1 FROM fusion_restart_pairs WHERE resource=? AND a_receipt IS NOT NULL AND final_evidence IS NULL",
        (resource,),
    ).fetchone():
        return True
    return (
        ledger.db.execute(
            "SELECT 1 FROM job_resources r JOIN jobs ON r.job_id=jobs.id WHERE r.resource=? AND jobs.state='running'",
            (resource,),
        ).fetchone()
        is not None
    )


def exact_record(row, admission, request):
    return (
        row is not None
        and row["request"] == request
        and all(row[key] == value for key, value in admission.items())
    )


def reserve(ledger, admission, request):
    install(ledger)
    existing = prior(ledger, admission["resource"])
    if existing is not None:
        if not exact_record(existing, admission, request):
            raise ValueError(
                "an unrelated Fusion initial startup already reserved the installation"
            )
        return
    ledger.db.execute(
        "INSERT INTO fusion_cold_start(resource,phase_a,definition,generation,fingerprint,request)"
        " VALUES (?,?,?,?,?,?)",
        (*admission.values(), request),
    )


def admit(ledger, admission, request, receipt):
    install(ledger)
    row = prior(ledger, admission["resource"])
    if not exact_record(row, admission, request) or row["startup_receipt"] is not None:
        raise ValueError("Fusion initial reservation changed before Phase A admission")
    ledger.db.execute(
        "UPDATE fusion_cold_start SET startup_receipt=? WHERE request=?",
        (receipt, request),
    )
    ledger.change_resource(admission["resource"], True, unpark_waiters=False)
    ledger.refresh()
    next_job = ledger.db.execute(
        "SELECT state FROM jobs WHERE id=?", (admission["phase_a"],)
    ).fetchone()
    if next_job["state"] != "queued":
        raise ValueError("exact Fusion Phase A did not become runnable")
    ledger.event(
        admission["phase_a"],
        "fusion_cold_start_admitted",
        {"request": request, "receipt": receipt},
    )
