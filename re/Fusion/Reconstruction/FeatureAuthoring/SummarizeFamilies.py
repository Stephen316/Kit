import json
import lzma
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from DecodeControls import decode


def groups(entity):
    return {g["class"]: g["fields"] for g in entity["groups"]}


def symbol(value, by_id):
    if isinstance(value, dict) and set(value) == {"ref"}:
        target = by_id.get(value["ref"])
        return {"ref": target["class"] if target else value["ref"]}
    if isinstance(value, dict):
        return {k: symbol(v, by_id) for k, v in value.items()}
    if isinstance(value, list):
        return [symbol(v, by_id) for v in value]
    return value


def feature_summary(entity, by_id, op_map, params):
    g = groups(entity)
    dc = g.get("DcFeature", {})
    children = []
    for ref in dc.get("childNodes", []):
        child = by_id[ref["ref"]]
        item = {"class": child["class"]}
        cg = groups(child)
        if child["class"] == "DcDoubleParameter" or "DcParameter" in cg:
            p = by_id[cg["DcParameter"]["parameter"]["ref"]]
            pf = groups(p)["Parameter"]
            item.update(parameter=pf["name"], userName=pf["userName"], expression=pf["expression"], value=pf["value"], unit=pf["unit"], rparamId=cg["DcParameter"]["rparamId"])
        for key in ("BrepRef", "DRBody", "EntityDataRef"):
            if key in cg and cg[key].get("rRecipe"):
                recipe = by_id[cg[key]["rRecipe"]["ref"]]
                item["recipe"] = {"class": recipe["class"], "fields": groups(recipe)}
        if "DataRef" in cg:
            item["trackingType"] = cg["DataRef"]["trackingType"]
            item["updateFlag"] = cg["DataRef"]["updateFlag"]
        if "ModelDataRef" in cg:
            item["dataRefs"] = [by_id[r["ref"]]["class"] for r in cg["ModelDataRef"]["dataRefs"]]
        children.append(item)
    own = {k: symbol(v, by_id) for k, v in g.items() if k not in ("DcFeature", "DcComputableAction", "DcAction", "DcNode", "ManagedEntity")}
    table = by_id[dc["rProgenitorTable"]["ref"]] if dc.get("rProgenitorTable") else None
    progenitors = []
    if table:
        for pair in groups(table)["ProgenitorTable"]["ProgenitorTagVec"]:
            target = by_id[pair[0]["ref"]]
            progenitors.append({"tag": pair[1], "class": target["class"]})
    return {"id": entity["id"], "class": entity["class"], "baseName": dc.get("featureBaseName"), "userName": dc.get("featureUserName"), "featureIndex": dc.get("featureIndex"), "startModelHS": dc.get("startModelHS"), "endModelHS": dc.get("endModelHS"), "operationIds": op_map.get(entity["id"], []), "fields": own, "children": children, "progenitors": progenitors}


def summarize(path):
    design = decode(path, "FusionDesignSegmentType")
    by_id = {e["id"]: e for e in design["entities"]}
    op_map = {}
    order = []
    for e in design["entities"]:
        g = groups(e)
        if e["class"] == "DcFeatureIdManager":
            op_map = {k: v for k, v in g["DcFeatureIdManager"]["enetityIdMap"]["map"]}
        if e["class"] == "DcCreationOrderFeatures":
            order = [r["ref"] for r in g["DcCreationOrderFeatures"]["representationFeatures"]]
    features = [feature_summary(by_id[i], by_id, op_map, None) for i in order]
    bodies = []
    for e in design["entities"]:
        if e["class"] == "DcBody":
            g = groups(e)["DcBody"]
            body = groups(by_id[g["rBody"]["ref"]])["Body"]
            bodies.append({"ownFeature": by_id[g["rOwnFeature"]["ref"]]["class"], "creationIndex": body["creationIndex"], "volume_cm3": body["cache"]["object"][0]["fields"]["volume"] if body.get("cache") else None})
    params = []
    for e in design["entities"]:
        if e["class"] == "Parameter":
            p = groups(e)["Parameter"]
            params.append({k: p[k] for k in ("name", "userName", "expression", "value", "unit", "creationIndex", "isUserDefined")})
    return {"classes": sorted({c["class"] for c in design["classes"]}), "features": features, "bodies": bodies, "parameters": params}


if __name__ == "__main__":
    controls = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Controls"
    capture = json.loads((controls / "Capture.json").read_text())
    result = {"scope": "Typed decode of native one-variable controls: timeline features, owned parameters, data references, naming recipes and progenitor tables", "fusion_version": capture["fusion_version"], "families": {}}
    base_classes = None
    for control in capture["controls"]:
        if control["status"] != "captured":
            result["families"][control["name"]] = {"status": "not captured"}
            continue
        try:
            summary = summarize(controls / control["file"])
        except Exception as error:
            result["families"][control["name"]] = {"status": "not decoded", "error": repr(error)[:300], "sha256": control["sha256"]}
            continue
        if control["name"] == "ExtrudeNew":
            base_classes = set(summary["classes"])
        summary["sha256"] = control["sha256"]
        summary["observed"] = control["observed"]
        result["families"][control["name"]] = summary
    for name, summary in result["families"].items():
        if "classes" in summary and base_classes is not None:
            summary["added_classes"] = sorted(set(summary["classes"]) - base_classes)
    text = json.dumps(result, indent=1) + "\n"
    (HERE / "FamilyRecords.json.xz").write_bytes(lzma.compress(text.encode()))
    print(len(text))
