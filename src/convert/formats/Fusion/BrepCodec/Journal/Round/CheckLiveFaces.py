from convert.formats.Fusion.BrepCodec.Journal.Round.CheckWholeFace import CheckWholeFace
from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckLiveFaces(
    Records: tuple[AsmRecord, ...], Versions: dict[int, int], Aliases: tuple[int, ...]
) -> None:
    for SlotId, Revision in Versions.items():
        FaceValue = Records[Revision]
        if FaceValue.Name != "face" or ReadLiveRef(FaceValue, 4, Aliases) != -1:
            continue
        Surface = Records[Versions[ReadLiveRef(FaceValue, 7, Aliases)]]
        Shell = Records[Versions[ReadLiveRef(FaceValue, 5, Aliases)]]
        if ReadLiveRef(Shell, 5, Aliases) != SlotId:
            raise ValueError(
                "Fusion untrimmed periodic face must own its shell face list"
            )
        CheckWholeFace(FaceValue, Surface, Aliases)
