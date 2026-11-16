from __future__ import annotations

from typing import Protocol as TypeProtocol

from interchange.brep.Validation.GeometryAccess import GeometryAccess
from interchange.brep.Validation.TopologyAccess import TopologyAccess


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(GeometryAccess, TopologyAccess, TypeProtocol):
    """combined diagnostic surface sharing one immutable topology snapshot"""
