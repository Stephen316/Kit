# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.mesh.SurfaceMesh import SurfaceMesh

BindCompatMut((SurfaceMesh,), {__name__: globals()})

Mesh = SurfaceMesh

# mesh consumers need one intentional historical public contract
__all__ = ("Mesh",)
