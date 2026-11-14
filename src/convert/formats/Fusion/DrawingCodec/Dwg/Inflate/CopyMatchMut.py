def CopyMatchMut(Output: bytearray, Distance: int, Length: int, Limit: int) -> None:
    Start = len(Output) - Distance - 1
    if Start < 0:
        raise ValueError("DWG compressed match precedes the page start")
    if len(Output) + Length > Limit:
        raise ValueError("DWG compressed page exceeds its declared size")
    Remaining = Length
    while Remaining > 0:
        Chunk = Output[Start : Start + min(Remaining, Distance + 1)]
        Output.extend(Chunk)
        Start += len(Chunk)
        Remaining -= len(Chunk)
