from convert.formats.Fusion.DocumentCodec.Model.AuthorData import AuthorData
from copy import deepcopy as CopyValue

from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema


class AuthorState(AuthorData):
    def Allocate(
        self,
        RoleName: str,
        ClassName: str,
        ParentRole: str | None = None,
        RootName: str = "",
        Fields: dict[str, object] | None = None,
        NamedPairs: list[dict[str, object]] | None = None,
        Subjects: list[str] | None = None,
    ) -> None:
        if RoleName in self.Roles or ClassName not in self.ByName:
            raise ValueError("Invalid authored entity role or class")
        self.Roles[RoleName] = self.NextId
        self.NextId += 1
        self.Entities.append(
            DraftEntity(
                RoleName,
                ClassName,
                ParentRole,
                RootName,
                Fields or {},
                NamedPairs,
                Subjects or [],
            )
        )

    def Reference(self, RoleName: str | None) -> dict[str, object] | None:
        return None if RoleName is None else {"entityId": self.Roles[RoleName]}

    def ActReference(self, RoleName: str) -> dict[str, object]:
        ActRoles = {"component": 100, "instances": 101, "root_instance": 102}
        return {"entityId": ActRoles[RoleName], "segmentId": self.Policy.ActSegmentId}

    def FindEntity(self, RoleName: str) -> DraftEntity:
        return next(Entity for Entity in self.Entities if Entity.RoleName == RoleName)

    def Change(self, RoleName: str, **Fields: object) -> None:
        self.FindEntity(RoleName).FieldValues.update(Fields)

    def MakeGroup(self, NameValue: str, Fields: dict[str, object]) -> dict[str, object]:
        return {"identifier": self.ByName[NameValue].Value.ClassGuid, "fields": Fields}

    def Lineage(self, ClassGuid: str) -> tuple[NativeSchema, ...]:
        Result: list[NativeSchema] = []
        while ClassGuid and ClassGuid.upper() != "98542EB9-A4F2-4137-A808-DBB5B3CD6159":
            Schema = self.ByGuid[ClassGuid.upper()]
            Result.append(Schema)
            ClassGuid = Schema.Value.BaseGuid
        return tuple(Result)

    def MakeValue(self, NameValue: str) -> list[dict[str, object]]:
        return [
            self.MakeGroup(Schema.NameValue, CopyValue(self.Defaults[Schema.NameValue]))
            for Schema in self.Lineage(self.ByName[NameValue].Value.ClassGuid)
        ]

    def Localize(self, TextValue: str) -> list[dict[str, object]]:
        return [
            self.MakeGroup(
                "GlobalizedStringValue",
                dict(
                    defaultValue=TextValue,
                    globalized=False,
                    id="",
                    moduleName="",
                    value=TextValue,
                ),
            )
        ]
