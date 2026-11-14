"""Analyse what Fusion reported in the second native pass.

Two questions need work outside Fusion.

* Attributes: the Fusion API exposes no attribute values. AcceptComplexSecond.py
  exports the imported original and mutant bodies of attribute cases back to SMB
  through TemporaryBRepManager. This script decodes them with the production reader
  and records whether the edited attribute survived the Fusion round trip.
* Representations: when a refined spline is not reported pole for pole, the run
  report keeps the coedge curve Fusion reported. This script compares it with the
  predicted refined curve as geometry, and tests whether Fusion raised the inserted
  knot to full multiplicity.
* Authored bodies: one row per authored body and run, with the persisted and reopened
  measures, the largest drifts and the body volume of the default accuracy beside the
  very high accuracy volume.

Reads every completed run report in ComplexGeometry/SecondPass/Runs except Crashed.json.
Run with /opt/homebrew/bin/python3.14 -I.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import StitchAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402

import NurbsMath  # noqa: E402

FOLDER = ROOT / "re/Fusion/LocalOracle/ComplexGeometry/SecondPass"


def decode(path):
    data = path.read_bytes()
    entry = dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), header=data[:64].decode("latin-1"), containsStitchName=b"stitch_hint" in data)
    try:
        model = ReadGeometry(data)
    except ValueError as error:
        entry["decoded"] = False
        entry["error"] = str(error)
        return entry
    entry["decoded"] = True
    entry["byteExact"] = EmitGeometry(model) == data
    entry["records"] = len(model.Entities)
    entry["stitchHints"] = [list(value.HintValues) for value in model.Entities if isinstance(value, StitchAttrib)]
    return entry


def point(knots, degree, poles, parameter):
    values = NurbsMath.basis(degree, knots, len(poles), parameter)
    return [sum(value * pole[axis] for value, pole in zip(values, poles)) for axis in range(len(poles[0]))]


def insert(knots, degree, poles, parameter):
    span = NurbsMath.find_span(degree, knots, len(poles), parameter)
    result = []
    for index in range(len(poles) + 1):
        if index <= span - degree:
            result.append(list(poles[index]))
        elif index > span:
            result.append(list(poles[index - 1]))
        else:
            alpha = (parameter - knots[index]) / (knots[index + degree] - knots[index])
            result.append([alpha * a + (1.0 - alpha) * b for a, b in zip(poles[index], poles[index - 1])])
    return sorted(knots + [parameter]), result


def representation(case, pair):
    diagnosis = pair["diagnosis"]
    original = diagnosis["original"][0]["nurbs"]
    reported = diagnosis["mutant"][0]["nurbs"]
    degree = original["degree"]
    inserted = case["detail"]["insertedKnot"]
    knots, poles = insert(list(original["knots"]), degree, original["controlPoints"], inserted)
    predicted = diagnosis["predicted"]
    prediction_poles = max(math.dist(a, b) for a, b in zip(poles, predicted)) if len(poles) == len(predicted) else None
    full_knots, full_poles = knots, poles
    while full_knots.count(inserted) < degree:
        full_knots, full_poles = insert(full_knots, degree, full_poles, inserted)
    low, high = original["knots"][0], original["knots"][-1]
    samples = [low + (high - low) * index / 200 for index in range(201)]
    drift = max(math.dist(point(knots, degree, poles, value), point(reported["knots"], degree, reported["controlPoints"], value)) for value in samples)
    same_knots = full_knots == reported["knots"]
    pole_gap = max(math.dist(a, b) for a, b in zip(full_poles, reported["controlPoints"])) if len(full_poles) == len(reported["controlPoints"]) else None
    return dict(label=case["label"], pcurve=pair["pcurve"], form=pair["form"], insertedKnot=inserted, degree=degree, predictedPoles=len(predicted), reportedPoles=len(reported["controlPoints"]), reportedKnots=reported["knots"], recomputedPredictionGap=prediction_poles, reportedKnotMultiplicity=reported["knots"].count(inserted), fullMultiplicityKnotsEqual=same_knots, fullMultiplicityPoleGap=pole_gap, geometryDrift=drift, samples=len(samples))


def largest(entries, key):
    values = [entry[key] for entry in entries if entry.get(key) is not None]
    return max(values) if values else None


def checked(checks, expected):
    shape = checks["summary"]
    row = dict(valid=shape["valid"], solid=shape["solid"], faces=shape["faces"], edges=shape["edges"], vertices=shape["vertices"], surfaceTypes=shape["surfaceTypes"], curveTypes=shape["curveTypes"])
    row.update(areaCm2=checks["physical"]["areaCm2"], areaRelativeError=checks["areaRelativeError"], volumeCm3=checks["physical"]["volumeCm3"], volumeRelativeError=checks.get("volumeRelativeError"), centerDriftCm=checks.get("centerDriftCm"))
    if expected["solid"] and shape["volumeCm3"] is not None:
        row["bodyVolumeCm3"] = shape["volumeCm3"]
        row["bodyVolumeRelativeError"] = abs(shape["volumeCm3"] - expected["volumeCm3"]) / expected["volumeCm3"]
    surfaces = checks["surfaces"]
    row.update(nurbsFaces=len(surfaces), surfacesMatched=sum(1 for entry in surfaces if entry.get("matched")), poleDriftCm=largest(surfaces, "poleDriftCm"), knotDrift=largest(surfaces, "knotDrift"), weightDrift=largest(surfaces, "weightDrift"), worstSampleDriftCm=largest(surfaces, "worstSampleDriftCm"))
    row["fusionSurfaces"] = [dict(degree=[entry["fusion"]["degreeU"], entry["fusion"]["degreeV"]], count=[entry["fusion"]["countU"], entry["fusion"]["countV"]], properties=[entry["fusion"]["propertiesU"], entry["fusion"]["propertiesV"]], weights=entry["fusion"]["weights"]) for entry in surfaces]
    coedges = checks["coedges"]
    row.update(pcurvesExpected=coedges["expected"], pcurvesMatched=coedges["matched"], fusionPcurves=len(coedges["fusion"]), vertexDriftCm=checks["vertexDriftCm"], problems=checks["problems"])
    return row


def authored_rows(report, prepared):
    rows = []
    for case in report["authored"]:
        row = dict(run=report["run"], label=case["label"], status=case.get("status"), stage=case.get("stage"))
        if "temporary" in case:
            row["temporary"] = case["temporary"]
        expected = prepared[case["label"]]["expected"]
        for key in ("persisted", "reopened"):
            if key in case:
                row[key] = checked(case[key], expected)
        row["savedSha256"] = case.get("saved_sha256")
        if "persisted" in case and "reopened" in case:
            row["reopenedSummaryEqual"] = case["persisted"]["summary"] == case["reopened"]["summary"]
        rows.append(row)
    return rows


def main():
    preparation = json.loads((FOLDER / "Preparation.json").read_text())
    prepared = {item["label"]: item for item in preparation["subtypes"]}
    shapes = {item["label"]: item for item in preparation["authored"]}
    attributes, representations, runs, authored = [], [], [], []
    for path in sorted((FOLDER / "Runs").glob("*.json")):
        if path.name == "Crashed.json":
            continue
        report = json.loads(path.read_text())
        runs.append(dict(run=report["run"], path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), status=report["status"], fusionVersion=report.get("fusion_version"), documentsBefore=report.get("documents_before"), documentsAfter=report.get("documents_after"), cases=[case["label"] for case in report["authored"] + report["subtypes"]], failures=report["failures"]))
        authored.extend(authored_rows(report, shapes))
        for case in report["subtypes"]:
            if "exported" in case:
                prediction = prepared[case["label"]]["prediction"]
                original = decode(ROOT / case["exported"]["original"]["path"])
                mutant = decode(ROOT / case["exported"]["mutant"]["path"])
                verdict = dict(run=report["run"], label=case["label"], attribute=prediction["attribute"], expectedOriginal=prediction["before"], expectedMutant=prediction["after"], original=original, mutant=mutant)
                if original.get("decoded") and mutant.get("decoded"):
                    verdict["retained"] = prediction["before"] in original["stitchHints"] and prediction["after"] in mutant["stitchHints"] and prediction["before"] not in mutant["stitchHints"]
                attributes.append(verdict)
            for pair in case.get("verdict", {}).get("pairs", []):
                if "diagnosis" in pair and pair["diagnosis"]["original"]:
                    entry = representation(dict(case, detail=prepared[case["label"]]["detail"]), pair)
                    entry["run"] = report["run"]
                    representations.append(entry)
    result = dict(schema="FusionComplexSecondAnalysis/3", script="re/Fusion/Reconstruction/ComplexGeometry/AnalyzeSecondPass.py", runs=runs, authored=authored, attributes=attributes, representations=representations)
    (FOLDER / "Analysis.json").write_text(json.dumps(result, indent=1) + "\n")
    for item in runs:
        print(item["run"], item["status"], item["documentsBefore"], item["documentsAfter"], item["failures"])
    for item in authored:
        print(item["run"], item["label"], item["status"], json.dumps({key: value for key, value in item.get("reopened", {}).items() if key not in ("fusionSurfaces",)}))
    for item in attributes:
        print(item["run"], item["label"], item.get("retained"), item["original"].get("decoded"), item["mutant"].get("decoded"), item["original"].get("stitchHints"), item["mutant"].get("stitchHints"), item["original"].get("error"))
    for item in representations:
        print(item["run"], item["label"], {key: item[key] for key in ("predictedPoles", "reportedPoles", "reportedKnotMultiplicity", "fullMultiplicityKnotsEqual", "fullMultiplicityPoleGap", "geometryDrift", "recomputedPredictionGap")})


main()
