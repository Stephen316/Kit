from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# explicit facade exports preserve historical imports while keeping ownership discoverable
__all__ = ["BoundingBox", "PlaneVector", "SpaceVector", "Transform"]
