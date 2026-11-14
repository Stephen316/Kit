from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken

KShortText = 255

KWideText = 32767


def WideWord(TextValue: str) -> KAsmToken:
    if not TextValue.isascii():
        raise ValueError("Fusion journal program text must be ASCII")
    if len(TextValue) <= KShortText:
        return 7, TextValue
    return (8 if len(TextValue) <= KWideText else 9), TextValue
