import struct


IDENTIFIER = "BE7E2847-FBC4-4898-A6E7-632A559A7F89"


def read_progenitor_aux(reader):
    return {"tag": reader.number("I")}


def emit_progenitor_aux(value):
    if type(value) is not dict or set(value) != {"tag"}:
        raise ValueError("Progenitor auxiliary data requires exactly its tag field")
    if type(value["tag"]) is not int or not 0 <= value["tag"] < 1 << 32:
        raise ValueError("Progenitor auxiliary tag exceeds unsigned 32-bit range")
    return struct.pack("<I", value["tag"])
