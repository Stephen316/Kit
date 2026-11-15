import argparse
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ApplicationProtocol import (
    COUNTERPART,
    PROTOCOL,
    configuration,
    file_bytes,
    load_pinned,
    require,
    sha256,
    write_new,
)
from FusionPhasePlan import phase_identity, phase_options, phase_paths, phase_rule, plan_scope
from Ledger import Ledger
from Records import canonical, digest, label, specification
from Runners import Registry
from Supervisor import ROOT, read_config

WORKER = Path(__file__).with_name("FusionApplicationWorker.py").resolve()


def queue_configuration(path, kind, resource):
    config = read_config(path)
    controller = config["controller"]
    require(
        controller.get("adapter") == "a03" and set(controller) == {"adapter", "store"},
        "Fusion phase queue requires the built-in A03 store",
    )
    require(
        config["resources"].get(resource) == 1,
        "select the configured capacity-one Fusion installation resource",
    )
    registry = Registry(config["registry"], ROOT)
    runner = registry.runners.get(kind)
    require(
        runner is not None and runner["pool"] in config["pools"],
        "Fusion runner must be in a configured supervisor pool",
    )
    argv = runner["argv"]
    require(
        len(argv) >= 5
        and argv[-3] == "--installation"
        and argv[-1] == "{session}"
        and (ROOT / argv[-4]).resolve() == WORKER,
        "runner must use the fixed Fusion application worker",
    )
    install_path = ROOT / argv[-2]
    installation = configuration(install_path)
    require(
        installation["application"] == "fusion",
        "selected runner must use a Fusion installation",
    )
    acknowledgement = runner["application_installation"]
    require(
        acknowledgement is None or acknowledgement.resolve() == install_path.resolve(),
        "runner and acknowledgement must share the same Fusion installation",
    )
    return Path(controller["store"]), installation, acknowledgement is not None


def check_plan(installation, directory, plan_hash):
    protocol = load_pinned(installation, PROTOCOL)
    counterpart = protocol["load_pinned"](installation, COUNTERPART)
    counterpart["protocol"] = protocol
    plan, _ = counterpart["pinned_plan"](
        SimpleNamespace(config=installation),
        directory,
        {"plan_sha256": plan_hash},
    )
    return plan


def phase_jobs(installation, kind, resource, run, plan, plan_hash):
    scope = plan_scope(plan)
    binding = f"fusion-plan:{plan_hash}"
    run_hash = sha256(
        canonical(
            {
                "installation": installation["installation"],
                "kind": kind,
                "resource": resource,
                "run": run,
                "plan_sha256": plan_hash,
            }
        ).encode("utf-8")
    )
    phase_a, phase_b = (f"fusion-phase:{run_hash}:{phase}" for phase in ("a", "b"))
    roles = phase_paths(plan, "a")
    follow_inputs = {role: {"dependency": phase_a, "artifact": role} for role in roles}
    common = {
        "kind": kind,
        "resources": [resource],
        "rule_version": phase_rule(scope),
        "tool_version": installation["source_revision"],
    }
    jobs = [
        {
            **common,
            "id": phase_a,
            "options": phase_options(scope, "a"),
            "inputs": {"plan": binding},
        },
        {
            **common,
            "id": phase_b,
            "options": phase_options(scope, "b"),
            "depends_on": [phase_a],
            "inputs": {
                "plan": binding,
                "phase-a.accepted": {"dependency": phase_a},
                **follow_inputs,
            },
        },
    ]
    return binding, jobs


def queue_phases(config, source_plan, kind, resource, run):
    kind, resource, run = (label(value) for value in (kind, resource, run))
    store, installation, acknowledgement = queue_configuration(config, kind, resource)
    raw = file_bytes(source_plan)
    plan_hash = sha256(raw)
    with tempfile.TemporaryDirectory(prefix="kit-fusion-phase-queue-") as temporary:
        directory = Path(temporary)
        staged = directory / "plan.json"
        write_new(staged, raw)
        plan = check_plan(installation, directory, plan_hash)
        binding, jobs = phase_jobs(installation, kind, resource, run, plan, plan_hash)
        with Ledger(store) as ledger:
            for job in jobs:
                current = ledger.db.execute(
                    "SELECT definition_hash FROM jobs WHERE id=?", (job["id"],)
                ).fetchone()
                require(
                    current is None
                    or current["definition_hash"] == digest(specification(job)),
                    "existing generated phase job has a different definition",
                )
            old = ledger.db.execute(
                "SELECT sha256 FROM bindings WHERE name=?", (binding,)
            ).fetchone()
            if old is None:
                require(
                    ledger.bind(binding, staged)["sha256"] == plan_hash,
                    "issued plan binding differs from the validated bytes",
                )
            else:
                require(
                    old["sha256"] == plan_hash,
                    "content-addressed plan label is already bound to different bytes",
                )
                ledger.verify_object(plan_hash)
            ledger.submit_many(jobs)
    return {
        "installation": installation["installation"],
        "resource": resource,
        "source_revision": installation["source_revision"],
        **phase_identity(plan),
        "plan_sha256": plan_hash,
        "plan_binding": binding,
        "jobs": {job["options"]["phase"]: job["id"] for job in jobs},
        "supervised_acknowledgement": acknowledgement,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Bind a verified Fusion plan and queue both A03 phases"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--kind", default="capture.fusion")
    parser.add_argument("--resource", required=True)
    parser.add_argument("--run", default="fresh")
    args = parser.parse_args()
    try:
        result = queue_phases(
            args.config, args.plan, args.kind, args.resource, args.run
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion phase queue: {type(error).__name__}: {error}"[:2048],
            file=sys.stderr,
        )
        return 1
    print(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
