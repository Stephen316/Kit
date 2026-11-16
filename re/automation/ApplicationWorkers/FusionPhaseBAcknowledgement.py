import json
import os
import re

from ApplicationProtocol import ACKNOWLEDGEMENT, directory, file_bytes, require, sha256
from FusionRestartPairs import second_definition


def acknowledgement_drained(root, supervisor_state, ledger, pair, proof):
    second = second_definition(ledger, pair)
    require(
        second is not None
        and second["state"] == "completed"
        and second["receipt"] == proof["phase_b_receipt_sha256"]
        and second["result"] == proof["phase_b_result_sha256"],
        "Fusion acknowledgement no longer belongs to the accepted Phase B",
    )
    checkpoint = file_bytes(ledger.objects.path(second["result"]))
    require(sha256(checkpoint) == second["result"], "accepted Phase B result changed")
    result = json.loads(checkpoint)
    session = result["receipt"]["session"]
    binding = result.get("application_acknowledgement_sha256")
    require(
        isinstance(session, str)
        and re.fullmatch("[0-9a-f]+-[0-9a-f]{8}", session)
        and isinstance(binding, str)
        and re.fullmatch("[0-9a-f]{64}", binding),
        "accepted Fusion Phase B lacks its supervisor acknowledgement intent",
    )
    intents = directory(supervisor_state / "application-acknowledgements")
    return (
        not os.path.lexists(intents / f"{session}.json")
        and not os.path.lexists(root / ACKNOWLEDGEMENT)
        and not os.path.lexists(root / "fence.json")
        and not any(directory(root / "jobs").iterdir())
    )
