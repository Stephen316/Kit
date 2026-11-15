import os
import re
import secrets
from pathlib import Path

from Records import canonical

STAGE_NAME = re.compile(r"\.claim-stage-[a-f0-9]{24}")


def write_claim(path, record):
    content = canonical(record) + "\n"
    staging = (
        path.with_name(f".claim-stage-{secrets.token_hex(12)}")
        if os.name == "nt"
        else path
    )
    descriptor = os.open(staging, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        if staging != path:
            os.rename(staging, path)
    except BaseException:
        if staging != path:
            staging.unlink(missing_ok=True)
        raise


def claim_to_file(ledger, worker, pool, claim_file):
    claim_file = Path(claim_file)
    if claim_file.exists() or claim_file.is_symlink():
        raise ValueError("claim destination already exists")
    leased = ledger.claim(worker, pool)
    if leased["job"] is None:
        return leased
    write_claim(claim_file, leased)
    return {
        "job": leased["job"]["id"],
        "attempt": leased["attempt"],
        "claim_file": str(claim_file),
    }


def clear_claim_stages(claims):
    for path in claims.glob(".claim-stage-*"):
        if STAGE_NAME.fullmatch(path.name):
            path.unlink(missing_ok=True)
