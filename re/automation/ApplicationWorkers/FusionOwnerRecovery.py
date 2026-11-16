from functools import partial
from types import SimpleNamespace

from ApplicationProtocol import require
from ArchiveFusionProbe import archive_probe
from FusionLifecyclePair import pairs
from FusionProbeArchiveCustody import authorize_archive
from FusionQueueReceipt import owned_bytes, receipt_bytes
from FusionRecoveryBasis import retain_basis
from FusionReplacementPreflight import stage_preflight
from FusionRestartPairs import installed
from QueueFusionPhases import recover_receipt
from StoreRead import read_store


# only the continuous owner of a registered untouched timeout may archive its quarantine
def archive_timeout(owner, fence):
    if fence is not None and (
        fence.get("reason") != "quarantined"
        or fence.get("installation") != owner.config["installation"]
        or fence.get("host") is not None
    ):
        return None
    match = parked_first_attempt(owner)
    if match is None:
        return None
    job, kind = match
    selected = [
        (path, queue)
        for path, queue in pairs(owner.inbox, owner.config, owner.store)
        if queue["jobs"]["a"] == job
    ]
    require(
        len(selected) == 1, "parked Fusion probe lacks its exact durable queue receipt"
    )
    ((path, expected),) = selected
    queue = recover_receipt(owner.args.config, path)
    raw = owned_bytes(path)
    require(
        queue == expected and raw == receipt_bytes(expected),
        "Fusion probe archive lost its durable queue receipt",
    )
    if (
        fence is None
        and owner.exit_watch is not None
        and owner.exit_watch.epoch is not None
        and owner.args.launch_archived_replacement
    ):
        from FusionArchivedReplacement import reconcile_replacement

        saved = reconcile_replacement(owner, path, queue, kind, raw)
        return archive_status(saved)
    saved = archive_probe(
        owner.args.config,
        queue,
        kind,
        authorize=partial(authorize_archive, owner, path, queue, raw),
        retain=(
            partial(retain_recovery, owner, queue, raw)
            if owner.exit_watch is not None and owner.exit_watch.epoch is not None
            else None
        ),
    )
    return archive_status(saved)


# the public owner status exposes evidence digest fields without local paths or launch challenges
def archive_status(saved):
    rearmed = saved.get("archive_replacement_status") == "retry_admitted"
    return {
        "status": (
            "phase_a_archive_retry_admitted" if rearmed else "phase_a_probe_archived"
        ),
        "archive_manifest_sha256": saved["archive_manifest_sha256"],
        "resource_rearmed": rearmed,
        "native_retry": (
            "authorized_second_attempt"
            if rearmed
            else "waiting_for_verified_owner_readiness"
        ),
        **{
            key: value
            for key, value in saved.items()
            if key.startswith(
                ("recovery_basis_", "replacement_preflight_", "archive_replacement_")
            )
        },
    }


# the archive locks and parked snapshot cover both the joined basis and replacement preflight
def retain_recovery(owner, queue, raw, database, config, timeout, archive):
    basis = retain_basis(owner, queue, raw, database, config, timeout, archive)
    checksum = basis.get("recovery_basis_sha256")
    if checksum is not None:
        basis.update(
            stage_preflight(
                owner, queue, database, archive["archive_manifest_sha256"], checksum
            )
        )
    return basis


# candidates are read from one parked controller snapshot before archive acquires custody
def parked_first_attempt(owner):
    resource = f"application:{owner.config['installation']}"
    path = owner.store / "ledger.sqlite3"
    if not path.is_file():
        return None
    require(
        not path.is_symlink(), "Fusion owner archive requires a private A03 database"
    )
    with read_store(path, None, (4,)) as database:
        if not installed(SimpleNamespace(db=database)):
            return None
        rows = database.execute(
            "SELECT jobs.id,jobs.kind FROM fusion_restart_pairs pair "
            "JOIN jobs ON jobs.id=pair.phase_a AND jobs.definition_hash=pair.a_definition "
            "JOIN resources ON resources.name=pair.resource "
            "WHERE pair.resource=? AND pair.installation=? AND pair.a_receipt IS NULL "
            "AND resources.available=0 AND resources.capacity=1 "
            "AND jobs.state='waiting_application' AND jobs.parked=1 AND jobs.attempts=1 "
            "LIMIT 2",
            (resource, owner.config["installation"]),
        ).fetchall()
    require(len(rows) <= 1, "Fusion archive candidate is ambiguous")
    return tuple(rows[0]) if rows else None
