import hashlib
import json
import lzma
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
Root = Path(__file__).resolve().parents[4]
Source = Root / "src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz"
Evidence = Root / "re/Fusion/Reconstruction/SketchConstraints/ConstraintGraphs.json.xz"
Archive = Root / "re/Fusion/LocalOracle/RectangleConstraints/WidthDepthDimensions.f3d"
Catalog = json.loads(lzma.decompress(Source.read_bytes()))["Classes"]
Schemas = json.loads(lzma.decompress(Evidence.read_bytes()))["graphs"][-2]["schemas"]
Api = runpy.run_path(str(Root / "re/Fusion/Reconstruction/EntityGraph/DecodeGraph.py"))
Metadata = Api["TOOLS"]["read_archive"](Archive)["classes"]
Spaces = {Entry["identifier"].upper(): Entry["namespace"] for Entry in Metadata.values()}
Names = (
    "SketchGeomConstraint", "FusionSketchLinearDim", "SketchDimension", "Dimension",
    "LinearDimensionInfoValue", "DimensionInfoValue",
)
Selected = []
for Name in Names:
    Declaration = next(Entry for Entry in Schemas.values() if Entry["className"] == Name + "MetaType")
    Entry = next(Entry for Entry in Catalog if Entry["ClassGuid"].upper() == Declaration["classId"] and Entry["SchemaVersion"] == Declaration["schemaVersion"])
    Selected.append(dict(Entry, NameValue=Name, ClassSpace=Spaces[Entry["ClassGuid"].upper()]))
Target = Root / "src/convert/formats/Fusion/DocumentCodec/Rectangle/Dimensions/DimensionClasses.json"
Target.parent.mkdir(parents=True, exist_ok=True)
Target.write_text(json.dumps(Selected, indent=2) + "\n")
Report = {
    "scope": "Six class declarations only; no record fields, frame subjects, identifiers, geometry or payload values copied into production",
    "catalogSha256": hashlib.sha256(Source.read_bytes()).hexdigest(),
    "constraintSchemaEvidenceSha256": hashlib.sha256(Evidence.read_bytes()).hexdigest(),
    "classSpaceSourceSha256": hashlib.sha256(Archive.read_bytes()).hexdigest(),
    "outputSha256": hashlib.sha256(Target.read_bytes()).hexdigest(),
    "classes": [{Key: Entry[Key] for Key in ("NameValue", "ClassGuid", "SchemaVersion", "ClassSpace")} for Entry in Selected],
}
(Path(__file__).parent / "VocabularyEvidence.json").write_text(json.dumps(Report, indent=2) + "\n")
print(json.dumps(Report, indent=2))
