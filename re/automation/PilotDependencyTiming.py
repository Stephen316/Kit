import math
from dataclasses import dataclass
from graphlib import TopologicalSorter

from Artifacts import Artifacts
from ResourceOccupancy import closed_attempt_receipt, stored_record
from StoreRead import read_store


# each accepted attempt retains the exact dependencies consumed by that generation
@dataclass(frozen=True)
class TimedAttempt:
    job: str
    started: float
    finished: float
    result: str
    dependencies: dict

    # controller attempt elapsed time supplies the weight of this dependency node
    @property
    def seconds(self):
        return self.finished - self.started


# immutable receipt identity and claim clocks must agree before timing an attempt
def read_attempt(connection, objects, checksum):
    record = stored_record(objects, checksum)
    attempt = connection.execute(
        "SELECT id,job_id,generation,number,fingerprint,started,ended,receipt,outcome "
        "FROM attempts WHERE id=?",
        (record["execution_id"],),
    ).fetchone()
    if (
        attempt is None
        or attempt["receipt"] != checksum
        or attempt["outcome"] != "completed"
    ):
        raise ValueError("dependency timing requires an exact completed attempt")
    receipt = closed_attempt_receipt(objects, attempt)
    dependencies = receipt["snapshot"]["dependencies"]
    if (
        receipt["outcome"] != "completed"
        or any("pending_ci_fingerprint" in item for item in dependencies.values())
        or not math.isfinite(attempt["started"])
        or not math.isfinite(receipt["finished_at"])
    ):
        raise ValueError("dependency timing requires a settled nonprovisional receipt")
    return TimedAttempt(
        attempt["job_id"],
        attempt["started"],
        receipt["finished_at"],
        receipt["result_sha256"],
        dependencies,
    )


# read ancestors by historical receipt rather than by the present job generation
def read_chain(store, roots):
    database = store.resolve() / "ledger.sqlite3"
    objects = Artifacts(store, create=False)
    nodes = {}
    pending = list(roots)
    with read_store(database, None, (4,)) as connection:
        while pending:
            checksum = pending.pop()
            if checksum in nodes:
                continue
            node = read_attempt(connection, objects, checksum)
            nodes[checksum] = node
            pending.extend(link["receipt"] for link in node.dependencies.values())
    for checksum, event in roots.items():
        node = nodes[checksum]
        if node.job != event["job_id"] or node.finished > event["at"]:
            raise ValueError("completed event does not bind its timed attempt")
    return nodes


# the longest measured path adds accepted attempt time across exact dependency edges
def longest_chain(nodes, roots):
    order = TopologicalSorter()
    for checksum, node in nodes.items():
        parents = []
        for job, link in node.dependencies.items():
            dependency = nodes[link["receipt"]]
            if (
                dependency.job != job
                or dependency.result != link["result"]
                or dependency.finished > node.started
            ):
                raise ValueError("dependency edge does not bind its earlier attempt")
            parents.append(link["receipt"])
        order.add(checksum, *parents)

    elapsed = {}
    prior = {}
    for checksum in order.static_order():
        node = nodes[checksum]
        candidates = (link["receipt"] for link in node.dependencies.values())
        parent = max(candidates, key=lambda item: (elapsed[item], item), default=None)
        prior[checksum] = parent
        elapsed[checksum] = node.seconds + (elapsed[parent] if parent else 0.0)

    cursor = max(roots, key=lambda item: (elapsed[item], item))
    seconds = elapsed[cursor]
    path = []
    while cursor is not None:
        node = nodes[cursor]
        path.append(
            {"job": node.job, "receipt_sha256": cursor, "attempt_seconds": node.seconds}
        )
        cursor = prior[cursor]
    return {"attempt_seconds": seconds, "path": path[::-1]}


# an empty accepted window carries no measured dependency path
def dependency_timing(store, roots):
    nodes = read_chain(store, roots) if roots else {}
    return {
        "settled_events": len(roots),
        "timed_attempts_with_ancestors": len(nodes),
        "longest_dependency_chain": longest_chain(nodes, roots) if nodes else None,
    }
