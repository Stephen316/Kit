from typing import Mapping as TypeMap

# exceptional legacy fields stay explicit because three names differ from their wire spellings
KPythonCompatAnnots: TypeMap[str, tuple[str, ...]] = {
    "ComponentDef": (
        "id",
        "name",
        "kind",
        "document_id",
        "configuration_name",
        "configuration_id",
        "bounding_box",
        "body_ids",
        "mesh_ids",
        "source_path",
        "source_format_id",
        "source_sha256",
        "provenance",
        "attributes",
    ),
    "ConstraintRef": ("entity_id", "point"),
    "SelectPathElem": ("entity_kind", "entity_id", "subelement"),
}
