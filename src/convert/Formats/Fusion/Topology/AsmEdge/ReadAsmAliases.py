from convert.Formats.Fusion.Topology.AsmEdge.AsmHistory import AsmHistory


# every archived entity must come from an explicit nonrepeated typed replacement
def ReadAsmAliases(
    History: AsmHistory,
) -> tuple[set[int], set[int], dict[int, int]]:
    InitialCount = len(History.Initial.Records)
    Removed: set[int] = set()
    Restored: set[int] = set()
    Aliases: dict[int, int] = {}
    for Change in History.Changes:
        Older, Newer = Change.OldRef, Change.NewRef
        if (
            Older == Newer
            or (
                Older != -1
                and (
                    not InitialCount <= Older < len(History.Records)
                    or Older in Restored
                )
            )
            or (Newer != -1 and (not 0 < Newer < InitialCount or Newer in Removed))
        ):
            raise ValueError("Invalid Fusion ASM history replacement")
        if Older != -1:
            Restored.add(Older)
        if Newer != -1:
            Removed.add(Newer)
        if Older != -1 and Newer != -1:
            if History.Records[Older].Name != History.Records[Newer].Name:
                raise ValueError("Fusion ASM history replacement changes entity kind")
            Aliases[Newer] = Older
    if not Removed or Restored != set(range(InitialCount, len(History.Records))):
        raise ValueError("Fusion ASM history has unbound archive entities")
    return Removed, Restored, Aliases
