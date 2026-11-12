from convert.formats.Fusion.MetaCursor import MetaCursor

# only the observed inert imported root attributes can leave placement trustworthy
KInertRootAttrs = (
    ("GatedByParent", "IntrinsicMetaTypebool", 1),
    ("ResolutionTime", "IntrinsicMetaTypeHString", 4),
    ("SelfGated", "IntrinsicMetaTypebool", 1),
)


# unsupported active gates or child metadata could alter visible assembly placement
def ReadOccurAttrs(Cursor: MetaCursor, NameValue: str) -> None:
    _ = Cursor.ReadWord()
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Unsupported Fusion occurrence attribute marker")
    Count = Cursor.ReadCount(len(KInertRootAttrs))
    if not Count:
        return
    if NameValue != "rootInstance" or Count != len(KInertRootAttrs):
        raise ValueError("Unsupported Fusion occurrence attributes")
    for NameText, TypeName, ValueWidth in KInertRootAttrs:
        if (
            Cursor.ReadText(Maximum=64) != NameText
            or Cursor.ReadText(Maximum=64) != TypeName
            or Cursor.TakeBytes(ValueWidth) != bytes(ValueWidth)
        ):
            raise ValueError("Unsupported Fusion occurrence gate state")
