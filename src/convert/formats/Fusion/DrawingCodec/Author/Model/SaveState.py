from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Author.Defaults.ActClasses import KActOrder
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DesignClasses import (
    KDesignOrder,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KChangeWord,
    KCycleColor,
    KFirstSave,
    KFirstStamp,
    KFolderOrder,
)


@MakeDataClass(frozen=True, slots=True)
class SaveState:
    SaveLabel: str = KFirstSave
    PriorVersions: tuple[str, ...] = ()
    ChangeWord: int = KChangeWord
    DesignNextId: int | None = None
    ActNextId: int | None = None
    InstanceGates: bool = False
    PropertyColumns: bool = False
    CycleColor: tuple[float, float, float] = KCycleColor
    DesignOrder: tuple[str, ...] = KDesignOrder
    ActOrder: tuple[str, ...] = KActOrder
    FolderOrder: tuple[str, ...] = KFolderOrder
    StampWords: tuple[int, int] = KFirstStamp
    CacheFolder: str = ""
