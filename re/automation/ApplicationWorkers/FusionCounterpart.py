import os
from pathlib import Path
import time


def pinned_plan(host, work, body):
    raw = protocol["file_bytes"](work / "plan.json")
    protocol["require"](protocol["sha256"](raw) == body["plan_sha256"], "dispatch plan changed")
    plan = protocol["record"](work / "plan.json")
    protocol["require"](set(plan) == {"schema", "source_revision", "recipes", "pins", "existing"}
                        and plan["schema"] == 1 and plan["source_revision"] == host.config["source_revision"]
                        and isinstance(plan["recipes"], list) and 1 <= len(plan["recipes"]) <= 4
                        and len(set(plan["recipes"])) == len(plan["recipes"])
                        and set(plan["recipes"]) <= {"P01", "P02", "P03", "P04"}, "invalid pinned Fusion phase plan")
    tool = protocol["load_pinned"](host.config, protocol["TOOL"])
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


def measure_probe(host, work, value, app, plan, tool):
    protocol["require"](app.documents.count == 0, "exclusive Fusion host has open documents")
    helper = tool["load_helper"](plan["pins"]["helper"], plan["pins"]["bindings"])
    owned, readings = [], {}
    try:
        tool["measure_control"](helper, app, plan["pins"]["control"], owned, readings, "healthy_control")
    finally:
        for document in list(owned):
            helper["close"](document, owned)
    protocol["require"](app.documents.count == 0, "healthy-control cleanup left open documents")
    proof = {"claim": "unqualified_application_observation", "control": "healthy", "host": host.host,
             "plan_sha256": value["body"]["plan_sha256"], "fusion_version": app.version,
             "readings": readings, "measured_at": time.time(), "documents_after": 0,
             "loaded_sources": {**host.loaded_sources, "counterpart": _source_pin, "tool": tool["_source_pin"]},
             "input_pins": plan["pins"]}
    protocol["write_record"](host.root / "grant.json", {"job_id": value["job_id"], "client": value["client"],
                             "until": min(time.time() + 60, value["deadline"])}, replace=True)
    return "completed", "fresh main-thread challenge and pinned control completed", proof, {}


def capture_phase(host, work, value, app, plan, tool):
    body = value["body"]
    raw = protocol["file_bytes"](work / "probe.done")
    probe = protocol["record"](work / "probe.done")
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
    phase = body["phase"]
    tool["run_phase"](work / "plan.json", body["plan_sha256"], phase)
    result = protocol["record"](work / f"phase-{phase}" / "measurements.json")
    protocol["require"](result["status"] == "complete" and result["phase"] == phase
                        and result["plan_sha256"] == body["plan_sha256"]
                        and result["process"]["pid"] == os.getpid()
                        and result["source_revision"] == host.config["source_revision"]
                        and result["fusion_version"] == app.version,
                        "Fusion phase receipt does not match the dispatched process and plan")
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


def serve(host, request_path, app):
    def action(value, work):
        protocol["require"](host.config["application"] == "fusion" and os.name == "posix", "Fusion dispatch host is unsupported")
        body = value["body"]
        expected = {"plan_sha256"} if value["operation"] == "probe" else {"plan_sha256", "probe_sha256", "phase"}
        protocol["require"](set(body) == expected, "application request contains unsupported fields")
        if value["operation"] == "phase":
            protocol["require"](body["phase"] in ("a", "b"), "unsupported Fusion phase")
        plan, tool = pinned_plan(host, work, body)
        if value["operation"] == "probe":
            return measure_probe(host, work, value, app, plan, tool)
        return capture_phase(host, work, value, app, plan, tool)

    return host.perform(request_path, action)
