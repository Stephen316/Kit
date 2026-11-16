from ApplicationProtocol import require, sha256, windows_process
from FusionCounterpart import scope_process

SCOPE = "two-body-through-all-discovery"
CASES = ("automatic", "explicit_a", "explicit_ab")


def plan_scope(plan):
    require(isinstance(plan, dict), "Fusion phase settings must be a record")
    scope = plan.get("scope")
    require(scope is None or scope == SCOPE, "unknown Fusion phase plan scope")
    return scope


def phase_options(scope, phase):
    return {"phase": phase} if scope is None else {"phase": phase, "scope": scope}


def phase_identity(plan):
    scope = plan_scope(plan)
    return {"recipes": plan["recipes"]} if scope is None else {"scope": scope, "cases": list(CASES)}


def phase_rule(scope):
    return "fresh-fusion@1" if scope is None else "fusion-through-all-scope@1"


def phase_paths(identity, phase):
    scope = plan_scope(identity)
    directory = f"phase-{phase}"
    report = "measurements" if scope is None else "report"
    files = {f"{directory}.receipt": f"{directory}/receipt.json",
             f"{directory}.{report}": f"{directory}/{report}.json"}
    if scope is None:
        files.update({f"{directory}.{recipe}": f"{directory}/{recipe}-fusion-fresh-baseline-{phase}.f3d"
                      for recipe in identity["recipes"]})
    else:
        files.update({f"{directory}.{mode}": f"{directory}/fusion-{mode}.f3d" for mode in CASES})
    return files


# every grouped phase needs the same successful pinned control on both sides
def check_phase_controls(report, plan):
    require(
        report.get("pins") == plan["pins"]
        and all(
            isinstance(reading, dict)
            and reading.get("compute_all_return") is True
            and reading.get("native_input") == plan["pins"]["control"]
            for reading in (
                report.get("healthy_control_before"),
                report.get("healthy_control_after"),
            )
        ),
        "Fusion phase did not preserve both healthy pinned controls",
    )


# phase verification must agree with the generating host on the process lifetime
def phase_process(host):
    if host["started"].startswith("windows:"):
        return windows_process(host)
    return scope_process(host)


def check_scope_report(receipt, report, raw, plan_hash, phase):
    require(receipt["schema"] == report["schema"] == 1
            and receipt["phase"] == report["phase"] == phase
            and receipt["scope"] == report["scope"] == SCOPE
            and receipt["status"] == report["status"] == "complete"
            and receipt["plan_sha256"] == report["plan_sha256"] == plan_hash
            and receipt["report_sha256"] == sha256(raw)
            and report["application"] == "fusion" and report["errors"] == []
            and tuple(item["mode"] for item in report["cases"]) == CASES,
            "Fusion scope report does not bind all three cases to the exact phase receipt")


def check_scope_archives(report, files, phase):
    for item in report["cases"]:
        archive = item["archive"]
        role = f"phase-{phase}.{item['mode']}"
        actual = files[role]
        require(archive["file"] == f"fusion-{item['mode']}.f3d"
                and all(archive[key] == actual[key] for key in ("sha256", "size_bytes")),
                "Fusion scope report archive pins differ from the accepted artifacts")
