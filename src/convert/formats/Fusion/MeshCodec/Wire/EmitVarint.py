def EmitVarint(Number: int) -> bytes:
    if type(Number) is not int or not 0 <= Number < 1 << 64:
        raise ValueError("Fusion mesh varint exceeds uint64")
    Output = bytearray()
    while Number >= 128:
        Output.append((Number & 127) | 128)
        Number >>= 7
    Output.append(Number)
    return bytes(Output)
