from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp

KMacroTexts = {
    "CMC": "BS {0}Index; BL {0}Rgb; RC {0}Flags; if {0}Flags&1 {{ TU {0}Name }}; if {0}Flags&2 {{ TU {0}Book }}",
    "TIME": "BL {0}Day; BL {0}Msec",
}
KStops = frozenset({"{", "}", ";"})


def ParseSpec(SpecText: str) -> tuple[SpecOp, ...]:
    Spaced = SpecText.replace("{", " { ").replace("}", " } ").replace(";", " ; ")
    Tokens = tuple(Spaced.split())
    SpecOps, Position = ParseBlock(Tokens, 0)
    if Position != len(Tokens):
        raise ValueError("DWG record spec has an unmatched closing brace")
    return SpecOps


def ParseBlock(
    Tokens: tuple[str, ...], Position: int
) -> tuple[tuple[SpecOp, ...], int]:
    SpecOps: list[SpecOp] = []
    while Position < len(Tokens) and Tokens[Position] != "}":
        Words, Position = TakeWords(Tokens, Position)
        IsCompound = Position < len(Tokens) and Tokens[Position] == "{"
        if IsCompound and not Words:
            raise ValueError("DWG record spec opens a block without a statement")
        if IsCompound:
            Compound, Position = ParseCompound(Words, Tokens, Position)
            SpecOps.append(Compound)
        elif Words:
            SpecOps.extend(ExpandMacro(Words))
    return tuple(SpecOps), Position


def TakeWords(Tokens: tuple[str, ...], Position: int) -> tuple[tuple[str, ...], int]:
    Finish = Position
    while Finish < len(Tokens) and Tokens[Finish] not in KStops:
        Finish += 1
    SkipCount = 1 if Finish < len(Tokens) and Tokens[Finish] == ";" else 0
    return Tokens[Position:Finish], Finish + SkipCount


def ParseCompound(
    Words: tuple[str, ...], Tokens: tuple[str, ...], Position: int
) -> tuple[SpecOp, int]:
    BodyOps, Position = ParseBlock(Tokens, Position + 1)
    Position = SkipClose(Tokens, Position)
    ElseOps: tuple[SpecOp, ...] = ()
    if Tokens[Position : Position + 2] == ("else", "{"):
        ElseOps, Position = ParseBlock(Tokens, Position + 2)
        Position = SkipClose(Tokens, Position)
    OpKind = Words[0]
    OpName = "".join(Words[1:2])
    return SpecOp(OpKind, OpName, Words[2:], BodyOps, ElseOps), Position


def SkipClose(Tokens: tuple[str, ...], Position: int) -> int:
    if Position >= len(Tokens) or Tokens[Position] != "}":
        raise ValueError("DWG record spec block is not closed")
    return Position + 1


def ExpandMacro(Words: tuple[str, ...]) -> tuple[SpecOp, ...]:
    if len(Words) < 2:
        raise ValueError(f"DWG record spec statement {Words!r} has no field name")
    MacroText = KMacroTexts.get(Words[0])
    if MacroText is not None:
        return ParseSpec(MacroText.format(Words[1]))
    return (SpecOp(Words[0], Words[1], Words[2:], (), ()),)
