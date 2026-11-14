import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
repository = root.parents[2]
sys.path.insert(0, str(repository / "src"))

from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle


source = repository / "re/Fusion/examples/.f3z/example1.f3z"
source_data = source.read_bytes()
bundle = ReadBundle(source_data)
output_data = EmitBundle(bundle)
output = root / "Bundles"
output.mkdir(exist_ok=True)
archive = output / "kit_production_example1.f3z"
archive.write_bytes(output_data)
report = {
    "purpose": "Prepare the production F3Z envelope artifact for authorized native upload acceptance",
    "operation": "ReadBundle(source) then EmitBundle(typed_model)",
    "source": str(source.relative_to(repository)),
    "source_sha256": hashlib.sha256(source_data).hexdigest(),
    "source_bytes": len(source_data),
    "output": str(archive.relative_to(repository)),
    "output_sha256": hashlib.sha256(output_data).hexdigest(),
    "output_bytes": len(output_data),
    "producer": "convert.formats.Fusion.BundleCodec.EmitBundle",
    "reader": "convert.formats.Fusion.BundleCodec.ReadBundle",
    "root_member": bundle.Description.RootPath,
    "root_ids": bundle.Description.Graph.RootIds,
    "document_count": len(bundle.Documents),
    "relationship_count": sum(len(group.Relations) for item in bundle.Description.Graph.Objects for group in item.References),
    "documents": [{"member": item.FileName, "bytes": len(item.DataValue),
                   "sha256": hashlib.sha256(item.DataValue).hexdigest()}
                  for item in bundle.Documents],
    "scope": "Reconstructed JSON and ZIP bundle envelope; complete source document members explicitly supplied and preserved, not a nested-document conversion claim",
    "native_acceptance": "pending; no native operation or cloud upload performed by preparation",
}
(output / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: value for key, value in report.items() if key != "documents"}, indent=2))
