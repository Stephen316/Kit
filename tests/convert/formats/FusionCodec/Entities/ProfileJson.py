from typing import TypedDict

from tests.convert.formats.FusionCodec.Entities.ClassJson import ClassJson


class ProfileJson(TypedDict):
    RootGuid: str
    Classes: list[ClassJson]
    ExternalTargets: list[object]
