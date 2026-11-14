from struct import unpack_from as UnpackFrom


def CheckStore(Payload: bytes) -> None:
    assert UnpackFrom("<IIII", Payload) == (136, 0xFFFFFFFF, 0xFFFFFFFF, 0)
    for Offset in range(16, len(Payload), 136):
        NextBlock, UsedCount, Flags = UnpackFrom("<IHH", Payload, Offset)
        assert 1 <= UsedCount <= 128
        assert Flags in (0, 1)
        assert NextBlock == 0xFFFFFFFF or NextBlock == (Offset - 16) // 136 + 1
        assert Payload[Offset + 8 + UsedCount : Offset + 136] == bytes(128 - UsedCount)
