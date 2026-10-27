# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# historical mesh fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsMesh = (
    (
        "interchange.mesh.Mesh",
        ("id", "name", "vertices", "triangles", "normals", "provenance", "attributes"),
    ),
)
