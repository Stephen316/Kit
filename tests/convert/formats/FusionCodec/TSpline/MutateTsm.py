def MutateTsm(Payload: bytes, Fault: str) -> bytes:
    Records = Payload.decode("ascii").splitlines()
    KindValue = "0g" if Fault == "number" else "l"
    Position = next(
        Index
        for Index, Value in enumerate(Records)
        if Value.startswith(KindValue + " ")
    )
    Fields = Records[Position].split()
    if Fault == "mate":
        Fields[3] = "2147483647"
    elif Fault == "flags":
        Fields[7] = "4"
    elif Fault == "owner":
        Fields[4] = "2147483647"
    elif Fault == "number":
        Fields[1] = "nan"
    elif Fault == "arity":
        Fields.append("0")
    elif Fault == "unknown":
        Records.append("50001vert 0")
    else:
        raise ValueError("Unknown integration mutation")
    Records[Position] = " ".join(Fields)
    return ("\n".join(Records) + "\n").encode("ascii")
