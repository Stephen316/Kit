from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Profiles.ProfileRef import KLoopGuid
from convert.Formats.Fusion.RecordSpan import RecordSpan


# sketch only and selected side uses preserve different source identities
@MakeDataClass(frozen=True, slots=True)
class RectSideOrigin:
    Record: RecordSpan

    # each key reflects the presence of a native consuming profile
    @property
    def Prefix(self) -> str:
        if self.Record.ClassGuid == KLoopGuid:
            return "fusion.selected_profile"
        return "fusion.authored_contour"

    # the record class distinguishes loop addresses from sketch addresses
    @property
    def IdentityKey(self) -> str:
        if self.Record.ClassGuid == KLoopGuid:
            return "fusion.selected_profile_loop_object_id"
        return "fusion.authored_contour_sketch_object_id"
