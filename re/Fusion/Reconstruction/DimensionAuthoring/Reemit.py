from hashlib import sha256
from json import dumps
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


Root = Path(__file__).resolve().parents[4]
Output = Root / "re/Fusion/LocalOracle/DimensionAuthoring"
Reports = []
for Name in ("DimensionedRectangle", "DimensionedCuboid"):
    Source = Output / (Name + ".f3d")
    Original = Source.read_bytes()
    Model = ReadDocument(Original)
    Reconstructed = EmitParsed(Model)
    Target = Output / (Name + "Reemitted.f3d")
    Target.write_bytes(Reconstructed)
    Reports.append({
        "name": Name,
        "sourceSha256": sha256(Original).hexdigest(),
        "outputSha256": sha256(Reconstructed).hexdigest(),
        "sourceBytes": len(Original),
        "outputBytes": len(Reconstructed),
        "byteExact": Reconstructed == Original,
        "entityRecords": sum(len(Segment.Records) for Segment in Model.Segments),
        "bodyHistories": len(Model.Bodies),
        "materialPackages": len(Model.Materials),
        "path": str(Target),
    })
Report = {"scope": "Complete public typed read/re-emission artifact preparation, no test invocation or native calls", "cases": Reports}
(Output / "TypedReemission.json").write_text(dumps(Report, indent=2) + "\n")
print(dumps(Report, indent=2))
