# historical mesh fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsMesh = (
    (
        "interchange.mesh.Mesh",
        ("id", "name", "vertices", "triangles", "normals", "provenance", "attributes"),
    ),
)
