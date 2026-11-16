from datetime import datetime, timezone
import json
import os
import time


SCOPE = "two-body-through-all-discovery"
SCOPE_MODES = ("automatic", "explicit_a", "explicit_ab")


def pinned_plan(host, work, body):
    raw = protocol["file_bytes"](work / "plan.json")
    protocol["require"](protocol["sha256"](raw) == body["plan_sha256"], "dispatch plan changed")
    try:
        plan = json.loads(raw)
    except RecursionError as error:
        raise ValueError("application plan exceeds the supported nesting") from error
    protocol["require"](isinstance(plan, dict), "application plan must be an object")
    if protocol["windows_phase_a"](host.config):
        protocol["require"]("scope" not in plan, "Windows Fusion only admits ordinary Phase A")
    if plan.get("scope") == SCOPE:
        return pinned_scope_plan(host, plan)
    protocol["require"](set(plan) == {"schema", "source_revision", "recipes", "pins", "existing"}
                        and plan["schema"] == 1 and plan["source_revision"] == host.config["source_revision"]
                        and isinstance(plan["recipes"], list) and 1 <= len(plan["recipes"]) <= 4
                        and len(set(plan["recipes"])) == len(plan["recipes"])
                        and set(plan["recipes"]) <= {"P01", "P02", "P03", "P04"}, "invalid pinned Fusion phase plan")
    tool = protocol["load_pinned"](host.config, protocol["TOOL"])
    if protocol["windows_phase_a"](host.config):
        tool["WINDOWS_GIT"] = protocol["windows_git"]()
    names = {"tool": tool["TOOL"], "helper": tool["HELPER"], "bindings": tool["BINDINGS"],
             "specification": tool["SPEC"], "control": tool["CONTROL"]}
    protocol["require"](set(plan["pins"]) == set(names), "Fusion phase pin roster changed")
    for name, relative in names.items():
        pin = plan["pins"][name]
        protocol["require"](pin["path"] == relative.as_posix(), "unexpected Fusion phase input path")
        committed = protocol["committed_bytes"](host.config, relative.as_posix())
        protocol["require"](pin["sha256"] == protocol["sha256"](committed) and pin["size_bytes"] == len(committed),
                            "Fusion phase pin is not anchored to the trusted installed revision")
    protocol["require"](isinstance(plan["existing"], dict) and set(plan["existing"]) <= set(plan["recipes"]), "invalid prior capture roster")
    for recipe, existing in plan["existing"].items():
        protocol["require"](existing == tool["pinned_existing"](host.config["source_revision"], recipe),
                            "prior capture pins differ from the trusted committed recipe")
    return plan, tool


# scope plans select one fixed trusted entry point and the committed study specification
def pinned_scope_plan(host, plan):
    protocol["require"](
        set(plan) == {"schema", "scope", "source_revision", "pins"}
        and type(plan["schema"]) is int
        and plan["schema"] == 1
        and plan["scope"] == SCOPE
        and plan["source_revision"] == host.config["source_revision"],
        "invalid pinned Fusion scope plan",
    )
    tool = protocol["load_pinned"](host.config, protocol["SCOPE_TOOL"])
    paths = tool["PINS"]
    protocol["require"](
        tool["SCHEMA"] == 1
        and tool["SCOPE"] == SCOPE
        and set(plan["pins"]) == set(paths),
        "Fusion scope pin roster changed",
    )
    sources = {}
    for role, relative in paths.items():
        content = protocol["committed_bytes"](host.config, relative.as_posix())
        expect = {
            "path": relative.as_posix(),
            "sha256": protocol["sha256"](content),
            "size_bytes": len(content),
        }
        protocol["require"](
            plan["pins"][role] == expect,
            "Fusion scope pin differs from the trusted installed revision",
        )
        sources[role] = content
    model = tool["execute_source"](paths["model"], sources["model"])
    model["validate_spec"](json.loads(sources["specification"]))
    return plan, tool


# an archive preflight needs the same native measurement without creating a dispatch grant
def measure_control_proof(host, plan_sha, app, plan, tool):
    protocol["require"](app.documents.count == 0, "exclusive Fusion host has open documents")
    scope = plan.get("scope") == SCOPE
    measure = protocol["load_pinned"](host.config, protocol["TOOL"]) if scope else tool
    helper = measure["load_helper"](plan["pins"]["helper"], plan["pins"]["bindings"])
    owned, readings = [], {}
    try:
        measure["measure_control"](
            helper, app, plan["pins"]["control"], owned, readings, "healthy_control"
        )
    finally:
        for document in list(owned):
            helper["close"](document, owned)
    protocol["require"](app.documents.count == 0, "healthy-control cleanup left open documents")
    proof = {"claim": "unqualified_application_observation", "control": "healthy", "host": host.host,
             "plan_sha256": plan_sha, "fusion_version": app.version,
             "readings": readings, "measured_at": time.time(), "documents_after": 0,
             "loaded_sources": {**host.loaded_sources, "counterpart": _source_pin, "tool": tool["_source_pin"]},
             "input_pins": plan["pins"]}
    if scope:
        proof["scope"] = SCOPE
        proof["loaded_sources"]["fresh_process"] = measure["_source_pin"]
    return proof


def measure_probe(host, work, value, app, plan, tool):
    proof = measure_control_proof(host, value["body"]["plan_sha256"], app, plan, tool)
    protocol["write_record"](host.root / "grant.json", {"job_id": value["job_id"], "client": value["client"],
                             "until": min(time.time() + 60, value["deadline"])}, replace=True)
    return "completed", "fresh main-thread challenge and pinned control completed", proof, {}


def capture_phase(host, work, value, app, plan, tool):
    body = value["body"]
    raw = protocol["file_bytes"](work / "probe.done")
    scope = plan.get("scope") == SCOPE
    probe = json.loads(raw) if scope else protocol["record"](work / "probe.done")
    protocol["require"](protocol["sha256"](raw) == body["probe_sha256"]
                        and probe["status"] == "completed" and probe["host"] == host.host
                        and probe["installation"] == host.config["installation"]
                        and probe["source_revision"] == host.config["source_revision"]
                        and probe["proof"]["plan_sha256"] == body["plan_sha256"]
                        and probe["proof"]["control"] == "healthy" and probe["proof"]["documents_after"] == 0
                        and probe["proof"]["fusion_version"] == app.version
                        and 0 <= time.time() - probe["proof"]["measured_at"] <= 60,
                        "phase dispatch requires a fresh control from this application process")
    grant = protocol["record"](host.root / "grant.json")
    protocol["require"](grant["job_id"] == value["job_id"] and grant["client"] == value["client"]
                        and time.time() < grant["until"], "application control reservation expired")
    if scope:
        protocol["require"](
            probe["proof"].get("scope") == SCOPE
            and probe["proof"]["input_pins"] == plan["pins"]
            and probe["proof"]["host"] == host.host,
            "scope phase requires its own pinned scope control",
        )
        return capture_scope_phase(host, work, value, app, plan, tool)
    phase = body["phase"]
    windows = protocol["windows_phase_a"](host.config)
    if windows:
        process = protocol["windows_process"](host.host)
        tool["run_phase"](work / "plan.json", body["plan_sha256"], phase, windows_process=process)
    else:
        tool["run_phase"](work / "plan.json", body["plan_sha256"], phase)
    result = protocol["record"](work / f"phase-{phase}" / "measurements.json")
    protocol["require"](result["status"] == "complete" and result["phase"] == phase
                        and result["plan_sha256"] == body["plan_sha256"]
                        and result["process"]["pid"] == os.getpid()
                        and result["source_revision"] == host.config["source_revision"]
                        and result["fusion_version"] == app.version,
                        "Fusion phase receipt does not match the dispatched process and plan")
    if windows:
        protocol["require"](result["process"] == process, "Windows phase process identity changed")
    names = {f"phase-{phase}.receipt": f"phase-{phase}/receipt.json",
             f"phase-{phase}.measurements": f"phase-{phase}/measurements.json"}
    names.update({f"phase-{phase}.{recipe}": f"phase-{phase}/{recipe}-fusion-fresh-baseline-{phase}.f3d"
                  for recipe in plan["recipes"]})
    files = {role: protocol["pin"](work / name, name) for role, name in names.items()}
    protocol["require"](sum(item["size_bytes"] for item in files.values()) <= protocol["MAX_BYTES"], "Fusion phase outputs exceed 256 MiB")
    proof = {"claim": "unqualified_application_observation", "phase": phase, "plan_sha256": body["plan_sha256"],
             "host": host.host, "fusion_version": app.version, "probe_sha256": body["probe_sha256"],
             "loaded_sources": {**host.loaded_sources, "counterpart": _source_pin, "tool": tool["_source_pin"]}}
    if phase == "a":
        proof["restart_handoff"] = host.restart_handoff(value, body["plan_sha256"])
    (host.root / "grant.json").unlink(missing_ok=True)
    return "completed", "pinned Fusion phase completed; native qualification remains open", proof, files


def scope_roles(phase):
    prefix = f"phase-{phase}"
    return {
        f"{prefix}.receipt": f"{prefix}/receipt.json",
        f"{prefix}.report": f"{prefix}/report.json",
        **{f"{prefix}.{mode}": f"{prefix}/fusion-{mode}.f3d" for mode in SCOPE_MODES},
    }


def scope_process(host):
    started = datetime.strptime(host["started"], "%a %b %d %H:%M:%S %Y").replace(
        tzinfo=timezone.utc
    )
    return {"pid": host["pid"], "start_unix_seconds": int(started.timestamp())}


# output names come from the trusted study roster and the report only binds their contents
def scope_outputs(work, phase, expected, expected_host):
    directory = work / f"phase-{phase}"
    protocol["require"](
        directory.is_dir() and not directory.is_symlink(),
        "Fusion scope phase must be a regular directory in the private spool",
    )
    names = scope_roles(phase)
    raw = protocol["file_bytes"](work / names[f"phase-{phase}.report"])
    report = json.loads(raw)
    sealed = protocol["file_bytes"](work / names[f"phase-{phase}.receipt"])
    receipt = json.loads(sealed)
    protocol["require"](
        receipt
        == {
            "schema": 1,
            "scope": SCOPE,
            "phase": phase,
            "status": "complete",
            "plan_sha256": expected["plan_sha256"],
            "report_sha256": protocol["sha256"](raw),
        }
        and all(report.get(key) == detail for key, detail in expected.items())
        and report["schema"] == 1
        and report["scope"] == SCOPE
        and report["phase"] == phase
        and report["application"] == "fusion"
        and report["status"] == "complete"
        and report["errors"] == []
        and report["process"] == scope_process(expected_host)
        and [item["mode"] for item in report["cases"]] == list(SCOPE_MODES)
        and all(
            report[label]["compute_all_return"] is True
            and report[label]["native_input"] == expected["pins"]["control"]
            for label in ("healthy_control_before", "healthy_control_after")
        ),
        "Fusion scope report does not match the sealed phase, process and controls",
    )
    files = {role: protocol["pin"](work / name, name) for role, name in names.items()}
    protocol["require"](
        files[f"phase-{phase}.report"]["sha256"] == receipt["report_sha256"]
        and files[f"phase-{phase}.receipt"]["sha256"] == protocol["sha256"](sealed),
        "Fusion scope report or receipt changed before publication",
    )
    for item in report["cases"]:
        pin = files[f"phase-{phase}.{item['mode']}"]
        protocol["require"](
            item["archive"]
            == {
                "file": pin["path"].split("/")[-1],
                "sha256": pin["sha256"],
                "size_bytes": pin["size_bytes"],
            },
            "Fusion scope native output does not match its sealed case",
        )
    protocol["require"](
        sum(item["size_bytes"] for item in files.values()) <= protocol["MAX_BYTES"],
        "Fusion scope outputs exceed 256 MiB",
    )
    return report, files


# the client stages a controller accepted result and the owner verifies its native inputs
def accepted_scope(host, work, expected):
    protocol["directory"](work / "phase-a")
    accepted = protocol["record"](work / "phase-a/accepted.json")
    result = accepted["result"]
    records = result["records"]
    previous = records["host"]
    handoff = records["restart_handoff"]
    protocol["require"](
        accepted["output_artifacts_version"] == 1
        and result["outcome"] == "completed"
        and result["artifacts"] == accepted["output_artifacts"]
        and records["scope"] == SCOPE
        and records["phase"] == "a"
        and records["application"] == "fusion"
        and records["installation"] == host.config["installation"]
        and records["plan_sha256"] == expected["plan_sha256"]
        and records["fusion_version"] == expected["application_build"]
        and set(handoff)
        == {"installation", "job_id", "reason", "host", "plan_sha256", "at", "owner"}
        and handoff["installation"] == host.config["installation"]
        and handoff["plan_sha256"] == expected["plan_sha256"]
        and handoff["reason"] == "restart_required"
        and handoff["owner"] == "external_application_owner"
        and handoff["host"] == previous
        and previous["pid"] != host.host["pid"]
        and protocol["identity"](previous["pid"]) is None,
        "accepted Fusion scope phase A lacks its exact installation and exited host handoff",
    )
    prior, files = scope_outputs(work, "a", expected, previous)
    manifest = accepted["output_artifacts"]
    protocol["require"](
        set(manifest) == set(files) | {"dispatch"}
        and all(
            manifest[role] == {key: pin[key] for key in ("sha256", "size_bytes")}
            for role, pin in files.items()
        )
        and prior["ended_unix_seconds"] <= handoff["at"] <= time.time()
        and scope_process(host.host)["start_unix_seconds"]
        > prior["ended_unix_seconds"],
        "Fusion scope phase A inputs or process chronology differ from accepted evidence",
    )
    return prior, files["phase-a.report"]["sha256"]


def capture_scope_phase(host, work, value, app, plan, tool):
    body = value["body"]
    phase = body["phase"]
    expected = {
        "plan_sha256": body["plan_sha256"],
        "source_revision": host.config["source_revision"],
        "application_build": app.version,
        "pins": plan["pins"],
        "specification_sha256": plan["pins"]["specification"]["sha256"],
    }
    if phase == "b":
        prior, report_hash = accepted_scope(host, work, expected)
        expected.update(
            previous_phase_report_sha256=report_hash, previous_process=prior["process"]
        )
    tool["run_phase"](work / "plan.json", body["plan_sha256"], phase)
    report, files = scope_outputs(work, phase, expected, host.host)
    if phase == "b":
        protocol["require"](
            all(
                report_case["archive"] == saved["archive"]
                for report_case, saved in zip(
                    report["cases"], prior["cases"], strict=True
                )
            ),
            "Fusion scope phase B did not return the accepted phase A archive bytes",
        )
    proof = {
        "claim": "unqualified_application_observation",
        "scope": SCOPE,
        "phase": phase,
        "plan_sha256": body["plan_sha256"],
        "host": host.host,
        "fusion_version": app.version,
        "probe_sha256": body["probe_sha256"],
        "loaded_sources": {
            **host.loaded_sources,
            "counterpart": _source_pin,
            "tool": tool["_source_pin"],
        },
    }
    if phase == "a":
        proof["restart_handoff"] = host.restart_handoff(value, body["plan_sha256"])
    (host.root / "grant.json").unlink(missing_ok=True)
    return "completed", "pinned Fusion scope discovery phase completed", proof, files


def serve(host, request_path, app):
    def action(value, work):
        windows = protocol["windows_phase_a"](host.config)
        protocol["require"](host.config["application"] == "fusion" and (windows or os.name == "posix"), "Fusion dispatch host is unsupported")
        body = value["body"]
        expected = {"plan_sha256"} if value["operation"] == "probe" else {"plan_sha256", "probe_sha256", "phase"}
        protocol["require"](set(body) == expected, "application request contains unsupported fields")
        if value["operation"] == "phase":
            protocol["require"](body["phase"] in ("a", "b"), "unsupported Fusion phase")
            protocol["require"](not windows or body["phase"] == "a", "Windows Fusion Phase B remains parked")
        plan, tool = pinned_plan(host, work, body)
        if value["operation"] == "probe":
            return measure_probe(host, work, value, app, plan, tool)
        return capture_phase(host, work, value, app, plan, tool)

    return host.perform(request_path, action)
