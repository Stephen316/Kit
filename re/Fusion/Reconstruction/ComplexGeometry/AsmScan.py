import math
import struct

TAGS = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def tokens(data):
    if data[:15] != b"ASM BinaryFile8":
        raise ValueError("magic")
    words = struct.unpack_from("<4q", data, 15)
    at = 47
    out = []
    n = len(data)
    while at < n:
        start = at
        tag = data[at]
        at += 1
        if tag in (4, 12, 21, 23):
            value = struct.unpack_from("<q", data, at)[0]
            at += 8
        elif tag == 6:
            value = struct.unpack_from("<d", data, at)[0]
            at += 8
        elif tag == 5:
            value = struct.unpack_from("<f", data, at)[0]
            at += 4
        elif tag == 2:
            value = data[at]
            at += 1
        elif tag == 3:
            value = struct.unpack_from("<h", data, at)[0]
            at += 2
        elif tag in (7, 13, 14):
            size = data[at]
            value = data[at + 1:at + 1 + size].decode("utf-8")
            at += 1 + size
        elif tag == 8:
            size = struct.unpack_from("<H", data, at)[0]
            value = data[at + 2:at + 2 + size].decode("utf-8")
            at += 2 + size
        elif tag in (9, 18):
            size = struct.unpack_from("<q", data, at)[0]
            value = data[at + 8:at + 8 + size].decode("utf-8")
            at += 8 + size
        elif tag in (19, 20):
            value = struct.unpack_from("<3d", data, at)
            at += 24
        elif tag == 22:
            value = struct.unpack_from("<2d", data, at)
            at += 16
        elif tag in (10, 11, 15, 16, 17):
            value = None
        else:
            raise ValueError(f"tag {tag} at {start}")
        out.append((tag, value, start))
    return words, out


def records(data):
    words, toks = tokens(data)
    head = toks[:6]
    rest = toks[6:]
    recs = []
    index = 0
    section = "active"
    while index < len(rest):
        names = []
        while True:
            tag, value, _ = rest[index]
            if tag not in (13, 14):
                raise ValueError(f"name expected at {rest[index][2]}")
            names.append(value)
            index += 1
            if tag == 13:
                break
        name = "-".join(names)
        if name == "End-of-ASM-data":
            break
        if name == "End-of-ASM-History-Section":
            section = "archived"
            continue
        if name.startswith("Begin-of-ASM-History-Data"):
            section = "history"
            if name == "Begin-of-ASM-History-Data":
                continue
        body = []
        depth = 0
        while True:
            tag, value, offset = rest[index]
            index += 1
            if tag == 17 and depth == 0:
                break
            if tag == 15:
                depth += 1
            elif tag == 16:
                depth -= 1
            body.append((tag, value))
        recs.append({"name": name, "section": section, "tokens": body})
        if name == "history_stream":
            section = "history"
    return words, head, recs


def subtree(body):
    root = []
    stack = [root]
    for tag, value in body:
        if tag == 15:
            node = []
            stack[-1].append(("sub", node))
            stack.append(node)
        elif tag == 16:
            stack.pop()
        else:
            stack[-1].append((tag, value))
    return root


def subnames(node, depth=0, out=None):
    if out is None:
        out = []
    for item in node:
        if item[0] == "sub":
            child = item[1]
            label = None
            for tag, value in child[:3] if child and child[0] != "sub" else []:
                if tag in (13, 14):
                    label = value if label is None else label + "-" + value
                    if tag == 13:
                        break
            out.append((depth, label))
            subnames(child, depth + 1, out)
    return out
