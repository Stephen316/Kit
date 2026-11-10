"""Check saved-file execution and report comment compliance separately.

The reference convention is TryUniCAD/Kit at the pinned commit below. A passing
smoke check proves execution and JSON validity for the supplied fixtures, not
complete semantic coverage, native writing, or the absence of all bugs.
"""

import argparse
import ast
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import io
import json
from pathlib import Path
import tokenize

# a pinned reference keeps style findings reproducible when upstream conventions change
STYLE_REFERENCE = "e64a368a2b644cc223d69556c5fda58f60175b62"


# source location keeps fixture discovery independent of the invoking shell directory
ROOT = Path(__file__).resolve().parent


# content hashes tie audit conclusions to the exact sources and saved archives
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# execution helpers share the same comment requirements as the decoder modules
def runtime_paths(root):
    return sorted(
        path
        for path in root.glob("*.py")
        if not path.name.startswith(("Generate", "validate_", "audit_"))
    )


# statement ownership puts lambda rationales above the entire enclosing expression
def reason_sites(tree):
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    sites = set()
    exempt_aliases = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sites.add(
                (
                    min([node.lineno] + [d.lineno for d in node.decorator_list]),
                    node.col_offset,
                )
            )
        elif isinstance(node, ast.Lambda):
            statement = node
            while not isinstance(statement, ast.stmt):
                statement = parents[statement]
            sites.add((statement.lineno, statement.col_offset))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            scope = parents.get(node)
            while scope is not None and not isinstance(
                scope,
                (
                    ast.Module,
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                scope = parents.get(scope)
            if not isinstance(scope, ast.Module):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if (
                len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and isinstance(node.value, (ast.Name, ast.Attribute))
            ):
                exempt_aliases += 1
            else:
                sites.add((node.lineno, node.col_offset))
    return sorted(sites), exempt_aliases


# syntactic checks reveal migration work without pretending to judge explanatory quality
def check_comments(path):
    source = path.read_text()
    lines = source.splitlines()
    sites, aliases = reason_sites(ast.parse(source))
    findings = []
    rationale_lines = set()
    for line, column in sites:
        previous = lines[line - 2] if line > 1 else ""
        prefix = " " * column + "# "
        if not previous.startswith(prefix):
            findings.append({"line": line, "code": "RAT001"})
            continue
        rationale_lines.add((line - 1, column))
        text = previous[len(prefix) :]
        if line > 2 and lines[line - 3].strip():
            findings.append({"line": line - 1, "code": "RAT002"})
            continue
        if (
            not 5 <= len(text.split()) <= 25
            or text != text.lower()
            or any(not (c.isalnum() or c.isspace()) for c in text)
            or set(text.split()) & {"fixme", "placeholder", "stub", "todo"}
        ):
            findings.append({"line": line - 1, "code": "RAT003"})
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT or token.start in rationale_lines:
            continue
        if token.string.startswith(("#!", "# SPDX-")):
            continue
        findings.append({"line": token.start[0], "code": "CMT001"})
    return {
        "file": path.name,
        "required_sites": len(sites),
        "exempt_aliases": aliases,
        "findings": findings,
    }


# strict serialization catches arithmetic failures that ordinary json output would hide
def check_archive(arguments):
    root, filename, library, baseline = arguments
    path = root / filename
    row = {"file": filename, "archive_sha256": digest(path)}
    try:
        from decode_basics import decode_basics

        model = decode_basics(path, library)
        encoded = json.dumps(
            model, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        streams = model["streams"]
        if not streams:
            raise ValueError("No supported design stream was decoded")
        for stream in streams:
            identities = [feature["object_id"] for feature in stream["features"]]
            if len(set(identities)) != len(identities):
                raise ValueError("Duplicate feature identity in one design stream")
        row.update(
            status="pass",
            output_sha256=hashlib.sha256(encoded).hexdigest(),
            streams=len(streams),
        )
        if baseline is not None:
            cache = baseline / (
                hashlib.sha256(filename.encode()).hexdigest() + ".json.gz"
            )
            with gzip.open(cache, "rb") as handle:
                before = handle.read()
            row["baseline_output_sha256"] = hashlib.sha256(before).hexdigest()
            row["previous_complete_output_unchanged"] = encoded == before
            if encoded != before:
                row["status"] = "changed"
    except Exception as error:
        row.update(status="error", error_type=type(error).__name__, error=str(error))
    return row


# a stable manifest prevents concurrent edits from being presented as one verified revision
def validate(root, library, workers, baseline=None):
    modules = sorted(root.glob("*.py"))
    hashes = {path.name: digest(path) for path in modules}
    syntax_errors = []
    for path in modules:
        try:
            compile(path.read_text(), str(path), "exec")
        except (SyntaxError, UnicodeError, ValueError) as error:
            syntax_errors.append({"file": path.name, "error": str(error)})
    invalid_syntax = {row["file"] for row in syntax_errors}
    comments = [
        check_comments(path)
        for path in runtime_paths(root)
        if path.name not in invalid_syntax
    ]
    archives = sorted(str(path.relative_to(root)) for path in root.glob("*/*.f3d"))
    arguments = [(root, filename, library, baseline) for filename in archives]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(check_archive, arguments))
    unchanged_sources = hashes == {
        path.name: digest(path) for path in sorted(root.glob("*.py"))
    }
    functional_pass = (
        bool(archives)
        and not syntax_errors
        and unchanged_sources
        and all(row["status"] == "pass" for row in results)
    )
    findings = sum(len(row["findings"]) for row in comments)
    return {
        "functional_status": "pass" if functional_pass else "fail",
        "comment_style_status": "fail" if findings else "pass",
        "scope": "Saved archive execution, strict JSON, feature identity uniqueness, syntax and syntactic comment checks; not independent semantic proof for every field",
        "summary": {
            "python_modules": len(modules),
            "syntax_errors": len(syntax_errors),
            "saved_archives": len(archives),
            "successful_archive_checks": sum(
                row["status"] == "pass" for row in results
            ),
            "runtime_style_files": len(comments),
            "required_rationale_sites": sum(row["required_sites"] for row in comments),
            "comment_style_findings": findings,
            "sources_unchanged_during_check": unchanged_sources,
            "live_Fusion_calls": 0,
        },
        "style_reference": {
            "repository": "https://github.com/TryUniCAD/Kit",
            "commit": STYLE_REFERENCE,
            "rules": ".kiro/steering/RationaleComments.md",
            "checker": "tools/steering/SteeringCompliance.py",
            "limitation": "Counts syntax and placement; explanatory purpose still needs human review",
        },
        "source_sha256": hashes,
        "syntax_errors": syntax_errors,
        "archives": results,
        "comment_style": comments,
    }


# separate statuses keep successful execution from concealing an unfinished style migration
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zstd-library")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--baseline-directory", type=Path)
    arguments = parser.parse_args()
    if not 1 <= arguments.workers <= 4:
        parser.error("workers must be between one and four")
    report = validate(
        ROOT,
        arguments.zstd_library,
        arguments.workers,
        arguments.baseline_directory,
    )
    arguments.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("functional_status", "comment_style_status", "summary")
            }
        )
    )
    return int(
        report["functional_status"] != "pass"
        or report["comment_style_status"] != "pass"
    )


if __name__ == "__main__":
    raise SystemExit(main())
