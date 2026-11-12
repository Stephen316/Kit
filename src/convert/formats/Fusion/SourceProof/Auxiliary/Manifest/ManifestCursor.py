from uuid import UUID as ParseUuid

from convert.formats.Fusion.MetaCursor import MetaCursor


# manifest fields share the native counted string grammar and exact record boundaries
class ManifestCursor(MetaCursor):

    # canonical nonzero tokens permit exact identity comparisons across records
    def ReadGuid(self) -> str:
        Value = self.ReadText(True, Maximum=36)
        GuidValue = ParseUuid(Value)
        if GuidValue.int == 0 or str(GuidValue) != Value:
            raise ValueError("Invalid Fusion manifest GUID")
        return Value

    # fixed property keys keep unrelated version values from satisfying a manifest schema
    def ReadVersions(self, KeysValue: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
        if self.ReadCount(len(KeysValue)) != len(KeysValue):
            raise ValueError("Invalid Fusion manifest version count")
        Values = tuple((self.ReadText(), self.ReadWord()) for _ in KeysValue)
        if tuple(KeyName for KeyName, _ in Values) != KeysValue:
            raise ValueError("Invalid Fusion manifest version keys")
        return Values

    # unknown trailing fields must keep the current schema from being observed
    def CheckEnd(self) -> None:
        if self.Offset != len(self.DataValue):
            raise ValueError("Unexpected Fusion manifest trailing data")
