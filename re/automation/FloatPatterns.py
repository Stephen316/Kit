"""Adjacent finite encodings for IEEE binary32 and binary64 byte searches."""

from math import isfinite


def adjacent_finite(codec, encoded):
    order = {"<": "little", ">": "big"}[codec.format[0]]
    bits = int.from_bytes(encoded, order)
    sign_bit = 1 << (codec.size * 8 - 1)
    value = codec.unpack(encoded)[0]
    if not isfinite(value):
        return
    # IEEE encodings reverse the bit ordering below zero. Each zero's neighbors
    # are the two smallest signed subnormals.
    if value == 0:
        neighbors = (sign_bit + 1, 1)
    elif bits & sign_bit:
        neighbors = (bits + 1, bits - 1)
    else:
        neighbors = (bits - 1, bits + 1)
    for neighbor in neighbors:
        raw = neighbor.to_bytes(codec.size, order)
        if isfinite(codec.unpack(raw)[0]):
            yield raw
