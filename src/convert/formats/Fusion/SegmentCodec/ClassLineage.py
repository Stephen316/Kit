# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


# subtree ranges qualify every continuation without repeatedly walking deep class chains
def MapLineage(Parents: dict[str, str]) -> dict[str, tuple[int, int]]:
    Children: dict[str, list[str]] = {}
    Pending: list[tuple[str, bool]] = []
    for ClassGuid, BaseGuid in Parents.items():
        if BaseGuid in Parents:
            Children.setdefault(BaseGuid, []).append(ClassGuid)
        else:
            Pending.append((ClassGuid, False))
    Ranges: dict[str, tuple[int, int]] = {}
    while Pending:
        ClassGuid, IsLeaving = Pending.pop()
        if IsLeaving:
            Ranges[ClassGuid] = (Ranges[ClassGuid][0], len(Ranges))
        else:
            Ranges[ClassGuid] = (len(Ranges), 0)
            Pending.append((ClassGuid, True))
            Pending.extend(
                (ChildGuid, False) for ChildGuid in Children.get(ClassGuid, ())
            )
    if len(Ranges) != len(Parents):
        raise ValueError("Cyclic Fusion segment class registry")
    return Ranges
