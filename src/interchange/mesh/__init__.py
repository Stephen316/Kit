from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.mesh.SurfaceMesh import SurfaceMesh

BindCompatMut((SurfaceMesh,), {__name__: globals()})

# the public mesh name must remain available so existing integrations keep resolving the canonical implementation
Mesh = SurfaceMesh

# mesh consumers need one intentional historical public contract
__all__ = ("Mesh",)
