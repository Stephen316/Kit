import hashlib
import json
import lzma
import math
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "re/Fusion/LocalOracle/TSpline"
OUT = Path(__file__).resolve().parent


def parse(path):
    result = {"declarations": {}, "faces": [], "edges": [], "vertices": [], "halfedges": [], "endConditions": [], "gripMap": [], "compoundGrips": [], "grips": [], "symmetryMaps": {}, "creasedEdges": [], "creasedVertices": [], "smartGrips": []}
    declarations = {"degree", "cap-type", "star-smoothness", "units", "end-conditions", "star-knot-rule", "tol", "geom-tol", "ver", "behavior-version", "compat-version"}
    for line in path.read_text().splitlines():
        words = line.split()
        if not words:
            continue
        kind, values = words[0], words[1:]
        if kind == "#TS0200":
            if values or result.get("header"):
                raise ValueError("Invalid TSM header")
            result["header"] = kind
        elif kind in declarations:
            if kind in result["declarations"]:
                raise ValueError("Duplicate TSM declaration")
            result["declarations"][kind] = values
        elif kind == "f":
            root, flags = map(int, values)
            if flags not in (0, 1):
                raise ValueError("Unsupported hidden-face flags")
            result["faces"].append(dict(root=root, isHidden=bool(flags)))
        elif kind == "e":
            root, interval = values
            result["edges"].append(dict(root=int(root), knotInterval=float(interval)))
        elif kind == "v":
            root, direction = values
            if direction not in ("NORTH", "SOUTH", "EAST", "WEST"):
                raise ValueError("Unknown primary grip direction")
            result["vertices"].append(dict(root=int(root), direction=direction))
        elif kind == "l":
            previous, next_id, mate, vertex, face, edge, valence = map(int, values)
            result["halfedges"].append(dict(next=next_id, previous=previous, mate=mate, vertex=vertex, face=face, edge=edge, valenceOffset=valence))
        elif kind == "ec":
            edge, value = values
            result["endConditions"].append(dict(edge=int(edge), value=float(value)))
        elif kind == "0m":
            if values == ["odd-grip-map"]:
                result["oddGripMap"] = True
            elif values[0] in ("gv", "gvp"):
                role, vertex = values
                result["gripMap"].append(dict(primary=role == "gvp", vertex=int(vertex)))
            elif values[0] == "cg":
                vertex, count, *remaining = map(int, values[1:])
                spokes, indices = remaining[:count], remaining[count:]
                expected = sum(length + length * spokes[(i + 1) % count] for i, length in enumerate(spokes))
                if len(spokes) != count or len(indices) != expected:
                    raise ValueError("Derived grip spoke cardinality mismatch")
                result["compoundGrips"].append(dict(vertex=vertex, spokeLengths=spokes, gripIndices=indices))
            else:
                raise ValueError("Unknown grip map record")
        elif kind == "0g":
            x, y, z, weight = map(float, values)
            if not all(math.isfinite(v) for v in (x,y,z,weight)) or weight <= 0:
                raise ValueError("Invalid weighted grip")
            result["grips"].append(dict(position=(x,y,z), weight=weight))
        elif kind == "105sym":
            result["symmetryMode"], = map(int,values)
        elif kind == "105plane":
            coefficients = list(map(float,values))
            if len(coefficients) != 12:
                raise ValueError("Invalid homogeneous plane frame")
            result["symmetryFrame"] = dict(origin=coefficients[:4], firstAxis=coefficients[4:8], secondAxis=coefficients[8:])
        elif kind == "105a":
            role, *items = values
            ids = list(map(int,items))
            if len(ids) % 2 or role not in ("fr", "er", "vr", "f", "e", "v"):
                raise ValueError("Invalid symmetry correspondence")
            result["symmetryMaps"][role] = list(zip(ids[::2],ids[1::2]))
        elif kind in ("100edges", "100verts", "50000grip"):
            key={"100edges":"creasedEdges","100verts":"creasedVertices","50000grip":"smartGrips"}[kind]
            result[key].extend(map(int,values))
        else:
            raise ValueError("Unmapped TSM record " + kind)
    return result


def check(model):
    halves = model["halfedges"]
    for index, half in enumerate(halves):
        if halves[half["next"]]["previous"] != index or halves[half["previous"]]["next"] != index:
            raise ValueError("Nonreciprocal TSM face ring")
        if halves[half["mate"]]["mate"] != index or halves[half["mate"]]["edge"] != half["edge"]:
            raise ValueError("Nonreciprocal TSM edge mates")
        if not 0 <= half["vertex"] < len(model["vertices"]) or not -1 <= half["face"] < len(model["faces"]):
            raise ValueError("Invalid TSM ownership reference")
    face_sizes=[]
    for face, record in enumerate(model["faces"]):
        current=record["root"]; visited=set()
        while current not in visited:
            visited.add(current)
            if halves[current]["face"] != face:
                raise ValueError("TSM face ring crosses face ownership")
            current=halves[current]["next"]
        if current != record["root"]:
            raise ValueError("TSM face ring does not close at its root")
        face_sizes.append(len(visited))
    for edge, record in enumerate(model["edges"]):
        if halves[record["root"]]["edge"] != edge or record["knotInterval"] <= 0:
            raise ValueError("Invalid TSM edge root or interval")
    for vertex, record in enumerate(model["vertices"]):
        if halves[record["root"]]["vertex"] != vertex:
            raise ValueError("Invalid TSM vertex root")
    if model["gripMap"]:
        if len(model["gripMap"]) != len(model["grips"]):
            raise ValueError("Grip map size differs")
        primary={row["vertex"]:model["grips"][i]["position"] for i,row in enumerate(model["gripMap"]) if row["primary"]}
    else:
        primary={i:row["position"] for i,row in enumerate(model["grips"])}
    if set(primary) != set(range(len(model["vertices"]))):
        raise ValueError("Incomplete primary control points")
    return dict(faceValences=face_sizes, boundaryHalfedges=sum(h["face"] == -1 for h in halves), primaryControlPoints=primary)


def main():
    captures=json.loads((SOURCE/'Capture.json').read_text());models={};summary=[]
    for case in captures['cases']:
        for stage,field in [('initial','initial_tsm'),('vertex_edited','edited_tsm')]:
            path=SOURCE/case[field]['file'];model=parse(path);facts=check(model)
            rounded=lambda p:tuple(round(v,12) for v in p)
            native=sorted(rounded(p) for p in case['stages'][stage]['control_points_cm'])
            derived=sorted(rounded(p) for p in facts['primaryControlPoints'].values())
            if native!=derived:
                raise ValueError('Native control point set mismatch '+path.name)
            archive=SOURCE/case['archive' if stage=='initial' else 'edited_archive']['file']
            with ZipFile(archive) as z:
                member,=[name for name in z.namelist() if name.endswith('.tsm')]
                if z.read(member)!=path.read_bytes():raise ValueError('Archive/description mismatch')
            models[path.name]=model
            summary.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),archive=archive.name,member=member,faces=len(model['faces']),edges=len(model['edges']),vertices=len(model['vertices']),halfedges=len(model['halfedges']),grips=len(model['grips']),compoundGripLayouts=len(model['compoundGrips']),boundaryHalfedges=facts['boundaryHalfedges'],faceValences=facts['faceValences'],nativeControlPointSetEqual=True,archiveDescriptionEqual=True,unitsDeclaration=model['declarations']['units']))
    encoded=lzma.compress(json.dumps(models,indent=2).encode());(OUT/'ControlModels.json.xz').write_bytes(encoded)
    result=dict(scope='Read-only structural decoding and native capture correspondence; no production codec or independently generated native acceptance',modelSha256=hashlib.sha256(encoded).hexdigest(),cases=summary,unresolved=['General grip evaluation and patch generation','Unit declaration interpretation outside this Fusion API route','Deleted slots, radial symmetry, user knots and additional record families'])
    (OUT/'ControlInventory.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(cases=len(summary),faces=sum(x['faces'] for x in summary),grips=sum(x['grips'] for x in summary))))


if __name__=='__main__':main()
