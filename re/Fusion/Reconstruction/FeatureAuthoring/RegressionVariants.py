"""Rebuild the two rejected authoring rules beside the accepted writer output.

Run with Python 3.14 from the repository root. The script patches one rule at
a time inside this process only, so production code stays unchanged:

* ReusedTags restores the earlier tag ledger, which gave a trimmed face's
  replacement the same entity tag as the deleted face.
* BodyScope restores the earlier reference scope, which stored the body
  identifier instead of the component identifier.

Observe the folder with ObserveRegressions.py through RunLocked.mjs.
"""

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import EmitAuthored  # noqa: E402
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design import AddPickMut, AddShellMut  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey, FaceLabelOf  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import TagLedger  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanHeading  # noqa: E402

OUTPUT = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Regressions"


def surface_key(face):
    if not isinstance(face, WallFace):
        return ("cap", round(face.LevelCm, 9), face.Upward)
    span = face.Span
    if isinstance(span, LineSpan):
        hx, hy = SpanHeading(span, False)
        return ("plane", round(hx, 9), round(hy, 9), round(span.StartCm[0] * hy - span.StartCm[1] * hx, 9))
    return ("cylinder", round(span.CenterCm[0], 9), round(span.CenterCm[1], 9), round(span.RadiusCm, 9))


def reused_face_tags(self, body, ordinal):
    result = {}
    seen = {}
    for face in body.Faces:
        identity = (ordinal, FaceLabelOf(face), surface_key(face))
        count = seen.get(identity, 0)
        seen[identity] = count + 1
        result[FaceKey(face)] = self.Claim(identity + (count,))
    return result


def body_scope(author):
    return [author.MakeGroup("PassiveScopeValue", dict(assetId=author.AssetId, scopeEntityIdentifier=author.BodyId, scopeIdType=2, segmentId=author.Policy.DesignSegmentId))]


def emit(name):
    return EmitDocument(EmitAuthored.spec(name, EmitAuthored.CASES[name]))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    variants = {
        "FilletAccepted": (emit("Fillet"), "accepted writer output for the fillet case"),
        "ShellAccepted": (emit("Shell"), "accepted writer output for the shell case"),
    }
    accepted_tags = TagLedger.FaceTags
    TagLedger.FaceTags = reused_face_tags
    variants["FilletReusedTags"] = (emit("Fillet"), "fillet with the earlier ledger: a replaced trimmed face reuses the deleted face tag")
    TagLedger.FaceTags = accepted_tags
    accepted_scope = (AddPickMut.PartScope, AddShellMut.PartScope)
    AddPickMut.PartScope = body_scope
    AddShellMut.PartScope = body_scope
    variants["ShellBodyScope"] = (emit("Shell"), "shell whose BrepRef and ETCachedTopology scopes carry the body identifier")
    AddPickMut.PartScope, AddShellMut.PartScope = accepted_scope
    manifest = {}
    for name, (payload, purpose) in variants.items():
        path = OUTPUT / (name + ".f3d")
        path.write_bytes(payload)
        manifest[name] = {"file": path.name, "sha256": hashlib.sha256(payload).hexdigest(), "purpose": purpose}
        print(name, len(payload), manifest[name]["sha256"][:16])
    (OUTPUT / "Manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
