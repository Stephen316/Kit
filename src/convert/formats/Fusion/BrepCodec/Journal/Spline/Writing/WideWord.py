from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken

# short text must remain consistent across callers so topology changes retain their native revision relationships
KShortText = 255

# wide text must remain consistent across callers so topology changes retain their native revision relationships
KWideText = 32767


# wide word needs an explicit validity boundary so topology changes retain their native revision relationships
def WideWord(TextValue: str) -> KAsmToken:
    if not TextValue.isascii():
        raise ValueError("Fusion journal program text must be ASCII")
    if len(TextValue) <= KShortText:
        return 7, TextValue
    return (8 if len(TextValue) <= KWideText else 9), TextValue
