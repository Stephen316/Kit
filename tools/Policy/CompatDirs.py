from __future__ import annotations

# public imports and external type discovery require these exact package identities
KCompatDirs = frozenset(
    {
        "src/convert",
        "src/convert/adapters",
        "src/convert/adapters/base",
        "src/convert/adapters/catia",
        "src/convert/adapters/freecad",
        "src/convert/adapters/json",
        "src/convert/adapters/registry",
        "src/convert/adapters/solidworks",
        "src/convert/api",
        "src/convert/engine",
        "src/interchange",
        "src/interchange/assembly",
        "src/interchange/brep",
        "src/interchange/document",
        "src/interchange/geometry",
        "src/interchange/history",
        "src/interchange/materials",
        "src/interchange/mesh",
        "src/interchange/serialization",
        "src/interchange/types",
        "typings/defusedxml",
    }
)
