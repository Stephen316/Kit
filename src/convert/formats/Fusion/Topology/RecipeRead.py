# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.MetaCursor import MetaCursor

# the counted recipe record can describe several kinds of selected topology
KRecipeGuid = "7ACC2A03-0261-4879-A14A-A93D661A5BDC"


# recipe terms are opaque naming operands and never resolve by numeric coincidence
def ReadRecipe(
    Cursor: MetaCursor,
) -> tuple[str, tuple[tuple[tuple[str, int, tuple[int, ...]], ...], ...], bytes]:
    if Cursor.TakeBytes(2) != bytes(2) or (Cursor.ReadWord(), Cursor.ReadWord()) != (
        1,
        3,
    ):
        raise ValueError("Unsupported Fusion topology recipe header")
    TableCount = Cursor.ReadCount(100000)
    if not TableCount:
        raise ValueError("Empty Fusion topology recipe table")
    Entries = []
    for _ in range(TableCount):
        TermCount = Cursor.ReadCount(64)
        if not TermCount:
            raise ValueError("Empty Fusion topology recipe name entry")
        Terms = []
        for _ in range(TermCount):
            NameValue = Cursor.ReadText(Maximum=128)
            Index = Cursor.ReadWord()
            Components = tuple(Cursor.ReadWord() for _ in range(Cursor.ReadCount(2)))
            if not NameValue or Cursor.ReadWord() != 0:
                raise ValueError("Invalid Fusion topology recipe term")
            Terms.append((NameValue, Index, Components))
        Entries.append(tuple(Terms))
    if Cursor.ReadWord() != 0:
        raise ValueError("Invalid Fusion topology recipe separator")
    KindValue = Cursor.ReadText(Maximum=128)
    if not KindValue.endswith("_recipe_data"):
        raise ValueError("Invalid Fusion topology recipe kind")
    Payload = Cursor.TakeBytes(len(Cursor.DataValue) - Cursor.Offset)
    return KindValue, tuple(Entries), Payload
