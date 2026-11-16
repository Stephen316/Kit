from importlib.util import (
    module_from_spec as LoadModule,
    spec_from_file_location as LoadSpec,
)
from pathlib import Path as FilePath
from sys import modules as Modules
from types import ModuleType
from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.container.Definition import ArchiveWriter
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the handle codec is loaded explicitly because research encoders are outside the installed package
class HandleCodec(Protocol):

    # the enclosing archive supplies the generation and condition for the optional handle fields
    def WriteHandleMut(
        self, Writer: ArchiveWriter, *, Generation: int, ConditionOne: bool
    ) -> int: ...


# the dimension codec links its independent geometry inputs and the shared archive state
class DistCodec(Protocol):

    # the selected frame and signed operation travel together into the encoder
    def DimGeometry(
        self, Frame: Transform, Normal: SpaceVector, Tangent: SpaceVector, Reverse: bool
    ) -> object: ...

    # scope and authored values must reach the same guarded writer used in research
    def WriteDistMut(
        self,
        Writer: ArchiveWriter,
        *,
        Generation: int,
        ConditionOne: bool,
        DimensionId: int,
        RetainCount: int,
        NameValue: str,
        DepthMm: float,
        Geometry: object,
    ) -> int: ...


# the bare research imports must resolve to these exact files for the scoped hosted test
def LoadResearchMut(PatchValue: MonkeyPatch, NameValue: str) -> ModuleType:
    PathValue = FilePath(__file__).resolve().parents[3] / "re/solidworks/WriterResearch"
    SpecValue = LoadSpec(NameValue, PathValue / f"{NameValue}.py")
    assert SpecValue is not None and SpecValue.loader is not None
    ModuleValue = LoadModule(SpecValue)
    PatchValue.setitem(Modules, NameValue, ModuleValue)
    SpecValue.loader.exec_module(ModuleValue)
    return ModuleValue


# the owned child resolves its length and handle dependencies before the hosted call
def LoadPairMut(PatchValue: MonkeyPatch) -> tuple[HandleCodec, DistCodec]:
    _ = LoadResearchMut(PatchValue, "BlindDepth")
    Handle = LoadResearchMut(PatchValue, "DisplayHandle")
    Dimension = LoadResearchMut(PatchValue, "BlindDimension")
    return CastValue(HandleCodec, Handle), CastValue(DistCodec, Dimension)
