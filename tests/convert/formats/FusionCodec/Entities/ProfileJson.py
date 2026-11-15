from typing import TypedDict

from tests.convert.formats.FusionCodec.Entities.ClassJson import ClassJson


# the profile json boundary needs grouped coverage so repository automation cannot silently change its observable contract
class ProfileJson(TypedDict):
    RootGuid: str
    Classes: list[ClassJson]
    ExternalTargets: list[object]
