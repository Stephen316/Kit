import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(BASE))

import AsmScan  # noqa: E402

LEAF_TAGS = {"int": (4,), "real": (6,), "enum": (21,), "text": (7,), "point": (19,), "vector": (20,)}


def S(*items):
    return ("seq", items)


def L(kind):
    return ("leaf", kind)


def M(rule):
    return ("many", rule)


def G(rule):
    return ("gate", rule)


def P(options, probe="name"):
    return ("pick", probe, options)


def C(name):
    return ("call", name)


B = L("bound")
B2 = S(B, B)
B4 = S(B, B, B, B)
ARR = M(L("real"))
TAIL = C("tail")

RULES = {}
RULES["surf"] = P({
    "null_surface": S(),
    "plane": S(L("point"), L("vector"), L("vector"), L("flag"), B4),
    "cone": S(L("point"), L("vector"), L("vector"), L("real"), B, B, L("real"), L("real"), L("real"), L("flag"), B4),
    "sphere": S(L("point"), L("real"), L("vector"), L("vector"), L("flag"), B4),
    "torus": S(L("point"), L("vector"), L("real"), L("real"), L("vector"), L("flag"), B4),
    "spline": S(L("flag"), C("scope"), B4),
})
RULES["curv"] = P({
    "null_curve": S(),
    "straight": S(L("point"), L("vector"), B2),
    "ellipse": S(L("point"), L("vector"), L("vector"), L("real"), B2),
    "degenerate_curve": S(L("point"), B2),
    "intcurve": S(L("flag"), C("scope"), B2),
})
RULES["bs2n"] = P({"nullbs": S(), "nubs": C("bs2body"), "nurbs": C("bs2wbody")})
RULES["tail"] = S(L("enum"), C("bss"), L("real"), ARR, ARR, ARR, ARR, ARR, ARR, L("flag"))
RULES["ctx"] = S(L("int"), L("enum"), C("bs3"), L("real"), C("surf"), C("surf"), C("bs2n"), C("bs2n"), B2, ARR, ARR, ARR, L("int"))
RULES["formula"] = C("formula")
RULES["subdata"] = C("subdata")
RULES["member"] = S(L("int"), C("curv"), C("memberdata"))
RULES["lpath"] = S(C("curv"), M(C("bs3")), L("int"))
RULES["section"] = M(S(L("real"), M(C("member")), C("lpath")))
RULES["side"] = S(L("text"), C("surf"), C("curv"), C("bs2n"), L("point"), C("bs2n"), L("int"), C("bs2n"))
RULES["blendvalue"] = C("blendvalue")
RULES["vbl"] = P({
    "pcurve": S(L("flag"), L("vector"), L("flag"), L("flag"), L("real"), C("surf"), C("bs2n"), L("flag"), L("real")),
})
RULES["rail"] = C("rail")

SUBTYPES = {
    "exact_spl_sur": S(L("int"), TAIL, B2, B2, L("enum")),
    "exact_int_cur": S(C("ctx"), B2, L("enum"), L("enum")),
    "par_int_cur": S(C("ctx"), L("flag"), L("flag")),
    "int_int_cur": S(C("ctx")),
    "spring_int_cur": S(C("ctx"), L("enum")),
    "helix_int_cur": S(L("int"), B2, L("point"), L("vector"), L("vector"), L("vector"), L("real"), L("vector"), C("surf"), C("surf"), C("bs2n"), C("bs2n")),
    "exp_par_cur": S(C("bs2"), L("real"), C("surf")),
    "cyl_spl_sur": S(L("int"), C("curv"), L("vector"), L("point"), TAIL),
    "sum_spl_sur": S(L("int"), C("curv"), C("curv"), L("point"), TAIL),
    "helix_spl_line": S(L("int"), B2, B2, B2, L("point"), L("vector"), L("vector"), L("vector"), L("real"), L("vector"), C("surf"), C("surf"), C("bs2n"), C("bs2n"), L("vector")),
    "sweep_sur": S(L("int"), L("flag"), L("int"), C("curv"), B2, G(S(L("point"), L("vector"))), L("point"), L("vector"), L("vector"), L("vector"), C("rail"), TAIL),
    "loft_spl_sur": S(L("int"), C("section"), C("section"), B2, B2, L("flag"), L("flag"), L("flag"), L("flag"), L("int"), L("int"), TAIL),
    "cl_loft_spl_sur": C("clloft"),
    "srf_srf_v_bl_spl_sur": C("varblend"),
    "VBL_SURF": S(L("int"), M(C("vbl")), L("int"), L("real")),
    "g2_blend_spl_sur": C("g2"),
}

STATS = collections.Counter()


class Cur:
    def __init__(self, toks):
        self.toks = toks
        self.at = 0

    def peek(self):
        if self.at >= len(self.toks):
            raise ValueError("eof")
        return self.toks[self.at]

    def take(self, tags):
        tag, value = self.peek()
        if tag not in tags:
            raise ValueError(f"expected {tags} got {tag}:{value!r} at {self.at}")
        self.at += 1
        return value

    def name(self):
        tag, value = self.peek()
        if tag not in (13, 14):
            raise ValueError(f"expected name got {tag}:{value!r} at {self.at}")
        self.at += 1
        return value


def read_leaf(cur, kind, out):
    if kind == "flag":
        tag, _ = cur.peek()
        if tag not in (10, 11):
            raise ValueError(f"flag expected got {tag} at {cur.at}")
        cur.at += 1
        out.append((tag, None))
        return tag == 10
    if kind == "bound":
        flag = read_leaf(cur, "flag", out)
        if flag:
            value = cur.take((6,))
            out.append((6, value))
            return value
        return None
    tags = LEAF_TAGS[kind]
    value = cur.take(tags)
    out.append((tags[0], value))
    return value


def read_curve_block(cur, out, dim, name=None):
    if name is None:
        name = cur.name()
        out.append((13, name))
    if name not in ("nubs", "nurbs"):
        raise ValueError("bs name " + name)
    degree = read_leaf(cur, "int", out)
    closure = read_leaf(cur, "enum", out)
    count = read_leaf(cur, "int", out)
    knots = []
    for _ in range(count):
        knots.append((read_leaf(cur, "real", out), read_leaf(cur, "int", out)))
    poles = sum(m for _, m in knots) - degree + 1
    width = dim + (1 if name == "nurbs" else 0)
    values = [read_leaf(cur, "real", out) for _ in range(poles * width)]
    STATS[f"bs{dim}:{name}:c{closure}"] += 1
    return ("bs", name, degree, closure, tuple(knots), tuple(values))


def read_surface_block(cur, out):
    name = cur.name()
    out.append((13, name))
    if name not in ("nubs", "nurbs"):
        raise ValueError("bss name " + name)
    du = read_leaf(cur, "int", out)
    dv = read_leaf(cur, "int", out)
    rational = None
    if name == "nurbs":
        rational = cur.name()
        out.append((13, rational))
        STATS["rational:" + rational] += 1
    enums = [read_leaf(cur, "enum", out) for _ in range(4)]
    ku = read_leaf(cur, "int", out)
    kv = read_leaf(cur, "int", out)
    uk = [(read_leaf(cur, "real", out), read_leaf(cur, "int", out)) for _ in range(ku)]
    vk = [(read_leaf(cur, "real", out), read_leaf(cur, "int", out)) for _ in range(kv)]
    nu = sum(m for _, m in uk) - du + 1
    nv = sum(m for _, m in vk) - dv + 1
    width = 4 if name == "nurbs" else 3
    values = [read_leaf(cur, "real", out) for _ in range(nu * nv * width)]
    STATS[f"bss:{name}:{rational}:{enums}"] += 1
    return ("bss", name, du, dv, rational, enums, uk, vk, values)


ARITY = {**{k: 1 for k in "COS SIN TAN COT SEC CSC COSH SINH TANH COTH SECH CSCH ARCCOS ARCSIN ARCTAN ARCOT ARCSEC ARCCSC ARCCOSH ARCSINH ARCTANH ARCOTH ARCSECH ARCCSCH ABS EXP LN LOG SIGN SIZE SET SQRT NORM NOT".split()},
         **{k: 2 for k in "CROSS DOT DCUR O ROTATE TERM".split()}, "VEC": 3, "DSURF": 3}


def read_law(cur, out):
    tag, value = cur.peek()
    if tag == 4:
        return read_leaf(cur, "int", out)
    if tag == 6:
        return read_leaf(cur, "real", out)
    if tag == 19:
        return read_leaf(cur, "point", out)
    if tag == 20:
        return read_leaf(cur, "vector", out)
    op = read_leaf(cur, "text", out)
    STATS["law:" + op] += 1
    if op == "null_law":
        return (op,)
    if op == "EDGE":
        return (op, read_rule(cur, RULES["curv"], out), read_leaf(cur, "real", out), read_leaf(cur, "real", out))
    if op in ARITY:
        return (op, tuple(read_law(cur, out) for _ in range(ARITY[op])))
    raise ValueError("law op " + op)


def read_formula(cur, out):
    name = read_leaf(cur, "text", out)
    STATS["formula"] += 1
    if name == "null_law":
        return (name,)
    count = read_leaf(cur, "int", out)
    return (name, tuple(read_law(cur, out) for _ in range(count)))


def read_rail(cur, out):
    kind = read_leaf(cur, "int", out)
    STATS[f"rail:{kind}"] += 1
    head = (read_leaf(cur, "flag", out), read_rule(cur, RULES["curv"], out), read_rule(cur, B2, out), read_leaf(cur, "real", out))
    if kind == 1:
        return (kind, head, read_leaf(cur, "flag", out), read_formula(cur, out), read_leaf(cur, "flag", out))
    if kind == 2:
        flags = (read_leaf(cur, "flag", out), read_leaf(cur, "flag", out))
        guide = (read_rule(cur, RULES["curv"], out), read_rule(cur, B2, out))
        ncontrol = read_leaf(cur, "int", out)
        nknot = read_leaf(cur, "int", out)
        knots = tuple(read_leaf(cur, "real", out) for _ in range(nknot))
        controls = tuple(read_leaf(cur, "real", out) for _ in range(ncontrol))
        tail = tuple(read_leaf(cur, "flag", out) for _ in range(3))
        return (kind, head, flags, guide, ncontrol, nknot, knots, controls, tail)
    if kind == 5:
        flag = read_leaf(cur, "flag", out)
        inner = read_rail(cur, out)
        return (kind, head, flag, inner, read_leaf(cur, "point", out), read_leaf(cur, "vector", out), read_leaf(cur, "real", out), read_leaf(cur, "real", out))
    if kind == 3:
        flag = read_leaf(cur, "flag", out)
        surf = read_rule(cur, RULES["surf"], out)
        aux = read_leaf(cur, "flag", out)
        if aux:
            raise ValueError("rail aux curve")
        return (kind, head, flag, surf, aux, read_leaf(cur, "flag", out))
    raise ValueError(f"rail kind {kind}")


def read_subdata(cur, out):
    kind = read_leaf(cur, "int", out)
    rows = read_leaf(cur, "int", out)
    cols = read_leaf(cur, "int", out)
    STATS[f"subdata:{kind}:{rows}:{cols}"] += 1
    if kind == 211:
        nrows, pairs = 1, 1
    else:
        nrows, pairs = rows, 1 + cols + 1
    return (kind, rows, cols, tuple(read_leaf(cur, "real", out) for _ in range(nrows * pairs * 2)))


def read_memberdata(cur, out, kind):
    if kind:
        data = (read_rule(cur, RULES["surf"], out), read_rule(cur, RULES["bs2n"], out), read_leaf(cur, "flag", out))
    else:
        data = (read_rule(cur, RULES["bs2n"], out), read_rule(cur, RULES["bs2n"], out))
    return data + (read_leaf(cur, "int", out), read_subdata(cur, out), read_rule(cur, G(L("vector")), out))


def read_blendvalue(cur, out):
    name = cur.name()
    out.append((13, name))
    STATS["blend:" + name] += 1
    calibrated = read_leaf(cur, "enum", out)
    flag = read_leaf(cur, "flag", out)
    if name in ("edge_offset", "fixed_width"):
        return (name, calibrated, flag, tuple(read_leaf(cur, "real", out) for _ in range(3)))
    if name == "interp":
        head = (read_leaf(cur, "real", out), read_leaf(cur, "real", out))
        function = read_rule(cur, RULES["bs2n"], out)
        ext = read_leaf(cur, "enum", out)
        count = read_leaf(cur, "int", out)
        points = tuple((read_leaf(cur, "real", out), read_leaf(cur, "real", out), read_leaf(cur, "real", out), read_leaf(cur, "real", out), read_leaf(cur, "point", out), read_leaf(cur, "vector", out)) for _ in range(count))
        return (name, calibrated, flag, head, function, ext, points)
    raise ValueError("blend value " + name)


def read_varblend(cur, out):
    rev = read_leaf(cur, "int", out)
    sides = (read_rule(cur, RULES["side"], out), read_rule(cur, RULES["side"], out))
    slice_ = read_rule(cur, RULES["curv"], out)
    offsets = (read_leaf(cur, "real", out), read_leaf(cur, "real", out))
    two = read_leaf(cur, "enum", out)
    values = tuple(read_blendvalue(cur, out) for _ in range(2 if two == 1 else 1))
    section = read_leaf(cur, "enum", out)
    if section != 0:
        raise ValueError(f"cross section {section}")
    ranges = read_rule(cur, S(B2, B2), out)
    shape = (read_leaf(cur, "int", out), read_leaf(cur, "real", out), read_leaf(cur, "real", out), read_leaf(cur, "int", out))
    tail = read_rule(cur, TAIL, out)
    ext = tuple(read_leaf(cur, "int", out) for _ in range(3))
    second = read_rule(cur, RULES["curv"], out)
    flags = (read_leaf(cur, "flag", out), read_leaf(cur, "flag", out))
    post = read_rule(cur, B2, out)
    post_pcurve = read_rule(cur, RULES["bs2n"], out)
    post_curve = read_rule(cur, P({"nullbs": S()}), out)
    return (rev, sides, slice_, offsets, two, values, section, ranges, shape, tail, ext, second, flags, post, post_pcurve, post_curve)


def read_clloft(cur, out):
    rev = read_leaf(cur, "int", out)
    tail = read_rule(cur, TAIL, out)
    scale = S(M(C("member")), C("lpath"))
    base = read_rule(cur, scale, out)
    entries = read_rule(cur, M(S(scale, L("real"))), out)
    flags = (read_leaf(cur, "flag", out), read_leaf(cur, "flag", out))
    kind = read_leaf(cur, "int", out)
    if kind != 0:
        raise ValueError("clloft kind")
    kflags = (read_leaf(cur, "flag", out), read_leaf(cur, "flag", out))
    selector = read_leaf(cur, "int", out)
    if selector == 0:
        direction = read_leaf(cur, "vector", out)
    else:
        direction = read_curve_block(cur, out, 3)
    interval = read_rule(cur, B2, out)
    curve = None
    if interval[0] is not None and interval[1] is not None:
        curve = read_curve_block(cur, out, 3)
    STATS[f"clloft:sel{selector}:{interval[0] is not None}{interval[1] is not None}"] += 1
    return (rev, tail, base, entries, flags, kind, kflags, selector, direction, interval, curve)


def read_g2(cur, out):
    rev = read_leaf(cur, "int", out)
    scalars = (read_leaf(cur, "real", out), read_leaf(cur, "real", out))
    sides = (read_rule(cur, RULES["side"], out), read_rule(cur, RULES["side"], out))
    center = read_rule(cur, RULES["curv"], out)
    radii = (read_leaf(cur, "real", out), read_leaf(cur, "real", out))
    selector = read_leaf(cur, "enum", out)
    if selector != -1:
        raise ValueError("g2 selector")
    ranges = read_rule(cur, S(B2, B2), out)
    prologue = (read_leaf(cur, "int", out), read_leaf(cur, "real", out), read_leaf(cur, "real", out), read_leaf(cur, "int", out))
    tail = read_rule(cur, TAIL, out)
    ext = tuple(read_leaf(cur, "int", out) for _ in range(3))
    return (rev, scalars, sides, center, radii, selector, ranges, prologue, tail, ext)


CUSTOM = {
    "bs2": lambda cur, out: read_curve_block(cur, out, 2),
    "bs3": lambda cur, out: read_curve_block(cur, out, 3),
    "bs2body": lambda cur, out: read_curve_block(cur, out, 2, "nubs"),
    "bs2wbody": lambda cur, out: read_curve_block(cur, out, 2, "nurbs"),
    "bss": read_surface_block,
    "formula": read_formula,
    "rail": read_rail,
    "subdata": read_subdata,
    "blendvalue": read_blendvalue,
    "varblend": read_varblend,
    "clloft": read_clloft,
    "g2": read_g2,
}


def read_scope(cur, out):
    cur.take((15,))
    out.append((15, None))
    name = cur.name()
    out.append((13, name))
    if name == "ref":
        value = ("ref", read_leaf(cur, "int", out))
    else:
        grammar = SUBTYPES.get(name)
        if grammar is None:
            raise ValueError("subtype " + name)
        STATS["sub:" + name] += 1
        value = (name, read_rule(cur, grammar, out))
    cur.take((16,))
    out.append((16, None))
    return value


def read_rule(cur, rule, out):
    kind = rule[0]
    if kind == "seq":
        return tuple(read_rule(cur, item, out) for item in rule[1])
    if kind == "leaf":
        return read_leaf(cur, rule[1], out)
    if kind == "many":
        count = read_leaf(cur, "int", out)
        if not 0 <= count <= 100000:
            raise ValueError("count")
        return tuple(read_rule(cur, rule[1], out) for _ in range(count))
    if kind == "gate":
        return read_rule(cur, rule[1], out) if read_leaf(cur, "flag", out) else None
    if kind == "pick":
        name = cur.name()
        out.append((13, name))
        if name not in rule[2]:
            raise ValueError("pick " + name)
        return (name, read_rule(cur, rule[2][name], out))
    if kind == "call":
        name = rule[1]
        if name == "scope":
            return read_scope(cur, out)
        if name == "memberdata":
            return read_memberdata(cur, out, out_member_kind(out))
        if name in CUSTOM:
            return CUSTOM[name](cur, out)
        return read_rule(cur, RULES[name], out)
    raise ValueError(kind)


def out_member_kind(out):
    for index in range(len(out) - 1, -1, -1):
        pass
    return MEMBER_KIND[-1]


MEMBER_KIND = []
_orig_member = RULES["member"]


def read_member(cur, out):
    kind = read_leaf(cur, "int", out)
    MEMBER_KIND.append(kind)
    curve = read_rule(cur, RULES["curv"], out)
    data = read_memberdata(cur, out, kind)
    MEMBER_KIND.pop()
    return (kind, curve, data)


CUSTOM["member"] = read_member
RULES.pop("member")

RECORDS = {
    "spline-surface": S(L("flag"), C("scope"), B4),
    "intcurve-curve": S(L("flag"), C("scope"), B2),
    "tedge-edge": S(L("real"), L("int"), L("int")),
    "tvertex-vertex": S(L("real"), L("real"), L("real"), L("int")),
    "wire": S(),
}


def read_record(rec):
    toks = rec["tokens"]
    name = rec["name"]
    out = []
    if name == "pcurve":
        cur = Cur(toks)
        for _ in range(3):
            tag, value = cur.peek()
            cur.at += 1
            out.append((tag, value))
        selector = read_leaf(cur, "int", out)
        if selector == 0:
            value = read_rule(cur, S(L("flag"), C("scope"), L("real"), L("real")), out)
        else:
            ref = cur.take((12,))
            out.append((12, ref))
            value = read_rule(cur, S(L("real"), L("real")), out)
    elif name == "tcoedge-coedge":
        cur = Cur(toks)
        for _ in range(11):
            tag, value = cur.peek()
            cur.at += 1
            out.append((tag, value))
        value = read_rule(cur, S(L("real"), L("real")), out)
        ref = cur.take((12,))
        out.append((12, ref))
        value = read_rule(cur, S(L("int"), C("curv"), L("int")), out)
    else:
        skip = {"spline-surface": 3, "intcurve-curve": 3, "tedge-edge": 11, "tvertex-vertex": 6, "wire": 8}[name]
        cur = Cur(toks)
        for _ in range(skip):
            tag, value = cur.peek()
            cur.at += 1
            out.append((tag, value))
        value = read_rule(cur, RECORDS[name], out)
    if cur.at != len(toks):
        raise ValueError(f"trailing {len(toks) - cur.at} tokens: {toks[cur.at:cur.at + 6]}")
    if out != list(toks):
        raise ValueError("re-emission mismatch")
    return value


def main():
    rows = json.loads((BASE / "Inventory.json").read_text())
    kinds = ("spline-surface", "intcurve-curve", "pcurve", "tcoedge-coedge", "tedge-edge", "tvertex-vertex", "wire")
    failures = collections.Counter()
    examples = {}
    ok = collections.Counter()
    for row in rows:
        if "names" not in row or not any(key.split(":", 1)[1] in kinds for key in row["names"]):
            continue
        with zipfile.ZipFile(ROOT / row["path"]) as archive:
            data = archive.read(row["member"])
        _, _, recs = AsmScan.records(data)
        for index, rec in enumerate(recs):
            if rec["name"] not in kinds:
                continue
            try:
                read_record(rec)
                ok[rec["name"]] += 1
            except Exception as error:
                key = f"{rec['name']}: {error}"[:200]
                failures[key] += 1
                examples.setdefault(key, (row["path"], row["member"], index))
    print("ok", dict(ok))
    for key, count in failures.most_common():
        print(count, key, examples[key])
    print(json.dumps(dict(sorted(STATS.items())), indent=0))


if __name__ == "__main__":
    main()
