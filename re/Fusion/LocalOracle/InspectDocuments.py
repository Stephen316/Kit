import json
from pathlib import Path
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()
rows = []
for index in range(app.documents.count):
    doc = app.documents.item(index)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    rows.append({"index": index, "name": doc.name, "is_saved": doc.isSaved, "is_modified": doc.isModified, "body_count": design.rootComponent.bRepBodies.count if design else None, "timeline_count": design.timeline.count if design and design.designType == adsk.fusion.DesignTypes.ParametricDesignType else None})
Path(__file__).resolve().parent.joinpath("Brep/DocumentsAfterImport.json").write_text(json.dumps(rows, indent=2) + "\n")
