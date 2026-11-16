import re
from pathlib import Path
from types import SimpleNamespace

import ApplicationProtocol as protocol
import FusionStartupEvidence as startup
from ApplicationProtocol import encoded, file_bytes, require, sha256
from FusionColdStartAdmission import exact_record, prior
from FusionExitRecords import read_pinned
from FusionOwnerColdStart import REQUEST
from FusionQueueReceipt import seal
from FusionReplacementLaunch import bundle_pins, replacement_source
from MacApplicationBundle import pinned_bundle


# the same parked archive can prepare only one replacement context without launching an app
def stage_preflight(owner, queue, database, archive_sha, basis_sha):
    basis = read_pinned(
        owner.root / f"archived-recovery-basis-{archive_sha}.json", basis_sha
    )
    epoch = owner.exit_watch.epoch
    require(
        basis["scope"] == "fusion_archived_recovery_basis"
        and basis["epoch"] == epoch
        and basis["archive_manifest_sha256"] == archive_sha
        and basis["first_attempt"] == 1,
        "Fusion replacement preflight lacks the current verified archive basis",
    )
    try:
        deployment = commissioned_deployment(owner, queue, database, epoch, basis_sha)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        return {"replacement_preflight_status": "commissioned_deployment_unverified"}
    binding = {
        "version": 1,
        "scope": "fusion_archived_replacement_preflight",
        "recovery_basis_sha256": basis_sha,
        "archive_manifest_sha256": archive_sha,
        "commissioned_exit_sha256": basis["commissioned_exit_sha256"],
        "resource": queue["resource"],
        "epoch": epoch,
        **deployment,
    }
    path = owner.root / f"archived-replacement-preflight-{archive_sha}.json"
    raw = encoded(binding)
    try:
        seal(path, raw)
    except ValueError:
        return {"replacement_preflight_status": "replacement_binding_conflict"}
    except OSError:
        return {"replacement_preflight_status": "replacement_preflight_unavailable"}
    return {
        "replacement_preflight_status": "sealed",
        "replacement_preflight_sha256": sha256(raw),
    }


# a historical cold launch cannot authorize another installation or a later controller generation
def commissioned_deployment(owner, queue, database, epoch, basis_sha):
    admission_sha = epoch["admission_sha256"]
    admitted = read_pinned(
        owner.root / f"cold-start-admission-{admission_sha}.json", admission_sha
    )
    cold_sha = admitted["owner_request_sha256"]
    cold = read_pinned(owner.root / REQUEST, cold_sha)
    row = prior(SimpleNamespace(db=database), queue["resource"])
    admission = cold["admission"]
    require(
        cold["scope"] == "owner_fusion_cold_start_request"
        and exact_record(row, admission, cold_sha)
        and row["startup_receipt"] == admission_sha
        and cold["queue_receipt_sha256"] == epoch["queue_receipt_sha256"]
        and cold["source_revision"] == epoch["source_revision"]
        and cold["installation_sha256"] == epoch["installation_sha256"]
        and cold["lifecycle_sha256"] == epoch["lifecycle_sha256"]
        and admission["resource"] == queue["resource"]
        and admission["phase_a"] == epoch["job"] == queue["jobs"]["a"]
        and admission["generation"] == epoch["generation"]
        and admission["fingerprint"] == epoch["fingerprint"],
        "Fusion replacement preflight lost the exact commissioned admission",
    )
    return {
        **verified_deployment(owner, cold),
        "launch_challenge": recovery_challenge(cold["launch_challenge"], basis_sha),
    }


# the future replacement must run the reviewed bundle and the same commissioned add in
def verified_deployment(owner, cold):
    lifecycle = file_bytes(owner.args.lifecycle)
    installation = owner.installation_bytes
    installation_sha = sha256(installation)
    require(
        sha256(lifecycle) == cold["lifecycle_sha256"]
        and installation_sha == cold["installation_sha256"],
        "Fusion replacement preflight changed its installation or lifecycle",
    )
    bundle = pinned_bundle(lifecycle, installation_sha)
    _, profile = startup.profile_input(vars(protocol), owner.args.profile)
    raw, _ = startup.verified_profile(
        vars(protocol),
        owner.config,
        installation,
        owner.args.profile,
        Path(profile["installed_bootstrap"]),
        cold["lifecycle_sha256"],
        bundle["executable"],
    )
    source = replacement_source(owner.config, require_admission=True)
    require(
        sha256(raw) == cold["profile_sha256"]
        and sha256(source) == cold["provider_sha256"],
        "Fusion replacement deployment differs from its commissioning pins",
    )
    return {
        "profile_sha256": cold["profile_sha256"],
        "provider_source_sha256": cold["provider_sha256"],
        "bundle": bundle_pins(bundle),
    }


# derive one new archive challenge from the immutable earlier commissioning challenge
def recovery_challenge(commissioned, basis_sha):
    require(
        isinstance(commissioned, str) and re.fullmatch("[0-9a-f]{48}", commissioned),
        "invalid commissioned Fusion launch challenge",
    )
    return sha256(
        encoded(
            {
                "scope": "fusion_archived_replacement_challenge",
                "commissioned_challenge": commissioned,
                "recovery_basis_sha256": basis_sha,
            }
        )
    )[:48]
