# historical document fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsDocument = (
    (
        "interchange.document.CadDocument",
        (
            "source",
            "configurations",
            "parameters",
            "support_planes",
            "sketches",
            "selections",
            "feature_timeline",
            "bodies",
            "meshes",
            "brep_payloads",
            "diagnostics",
            "capabilities",
            "metadata",
            "units",
            "schema_version",
            "assembly",
            "brep",
            "materials",
        ),
    ),
)
