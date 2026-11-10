"""Compare derived unary-function references with captured dependency getters."""

import argparse
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_parameters import decode_file
from decode_expression_dependencies import ArithmeticReferences


# expression support must agree across public readers and saved getters
def validate(root, zstd_library):
    captures = [
        ("parameterfunctions-bc10224394fe", None),
        (
            "parameterexpressions-3ddbef2b20bd",
            {"function_outside_subset.f3d", "product_sum.f3d", "text_name_literal.f3d"},
        ),
    ]
    report = {
        "scope": "Derived references only; no native dependency graph or expression evaluation",
        "samples": [],
        "negative_checks": [],
    }
    names = None
    for folder, selected in captures:
        truth = json.loads((root / folder / "ground_truth.json").read_text())
        assert (root / folder / "complete.txt").exists() and not truth["errors"]
        for sample in truth["samples"]:
            if selected is not None and sample["file"] not in selected:
                continue
            path = root / folder / sample["file"]
            main = decode_basics(path, zstd_library)["streams"][0]
            derived = main["derived_expression_dependencies"]
            parameter_only = decode_file(path, zstd_library)["streams"][0]
            assert parameter_only["derived_expression_dependencies"] == derived
            by_name = {p["parameter_name"]: p for p in derived["derived"]}
            unresolved = {p["parameter_name"]: p for p in derived["unresolved"]}
            checks = []
            for actual in sample["parameters"]:
                if actual["unit"].lower() == "text":
                    parsed = by_name[actual["name"]]
                    assert actual["name"] not in unresolved
                    assert parsed["syntax_tree"] == {
                        "kind": "TextLiteral",
                        "spelling": actual["expression"],
                        "value": actual["text_value"],
                    }
                    assert parsed["stored_expression"] == actual["expression"]
                    assert parsed["reference_occurrences"] == []
                    assert parsed["referenced_parameter_object_ids"] == []
                    assert (
                        parsed["referenced_parameter_names"]
                        == actual["dependency_names"]
                        == []
                    )
                    parameters = main["parameter_tables"]["user_parameters"]
                    (native,) = [
                        p for p in parameters if p["parameter_name"] == actual["name"]
                    ]
                    assert (
                        native["parameter_object_id"] == parsed["parameter_object_id"]
                    )
                    assert native["text_value"] == actual["text_value"]
                    assert (
                        native["collection_object_id"] == parsed["collection_object_id"]
                    )
                    assert (
                        native["name_registry_object_id"]
                        == parsed["name_registry_object_id"]
                    )
                    assert parsed in main["text_literal_dependencies"]["derived"]
                    checks.append(
                        {
                            "name": actual["name"],
                            "complete_text_literal_matches_api": True,
                            "empty_references_match_api": True,
                            "owned_parameter_identity_is_preserved": True,
                        }
                    )
                    continue
                parsed = by_name[actual["name"]]
                assert set(parsed["referenced_parameter_names"]) == set(
                    actual["dependency_names"]
                )
                assert parsed["stored_expression"] == actual["expression"]
                checks.append(
                    {
                        "name": actual["name"],
                        "reference_names_match_api": True,
                        "stored_expression_matches_api": True,
                    }
                )
            report["samples"].append(
                {
                    "file": str(path.relative_to(root)),
                    "checks": checks,
                    "derived": derived["derived"],
                    "unresolved": derived["unresolved"],
                    "both_entrypoints_equal": True,
                }
            )
            if names is None:
                parameters = main["unbound_parameters"]
                names = {p["parameter_name"]: p for p in parameters}
    for label, expression in (
        ("Unknown function", "sin(probeScale)"),
        ("Extra function argument", "abs(probeScale, probeWidth)"),
        ("Missing function argument", "sqrt()"),
        ("Trailing syntax", "sqrt(probeScale) probeWidth"),
        ("Excessive call nesting", "sqrt(" * 70 + "probeScale" + ")" * 70),
    ):
        try:
            ArithmeticReferences(expression, names).parse()
        except (ValueError, IndexError) as error:
            report["negative_checks"].append(
                {"check": label, "passed": True, "reason": str(error)}
            )
        else:
            raise AssertionError(label)
    report["summary"] = {
        "new_archives": 4,
        "prior_archives": 3,
        "api_parameter_checks": sum(len(s["checks"]) for s in report["samples"]),
        "unresolved_text_expressions": sum(
            len(s["unresolved"]) for s in report["samples"]
        ),
        "negative_checks": len(report["negative_checks"]),
        "all_passed": True,
    }
    return report


if __name__ == "__main__":

    # explicit command options keep validation independent of local defaults
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zstd-library", required=True)

    # caller options must remain separate from native capture data
    args = parser.parse_args()

    # saved evidence must resolve independently of the working directory
    root = Path(__file__).resolve().parent

    # machine readable evidence keeps validation failures visible to later audits
    report = validate(root, args.zstd_library)
    (root / "parameter-function-decoding.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report["summary"]))
