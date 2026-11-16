"""Read the native body identities carried by the pinned automatic partitions."""

from struct import Struct

from PairedCaptureIntake import require

from convert.geometry.Parasolid import NativeId, ParaHeaderData, ScanPartRecords

# native body attributes preserve the identity needed to compare across streams
KAtomName = b"ATOM_ID_2001"


# the pinned transfer schema defines the shell and attribute reference layouts
KScopeSchema = "SCH_3701250_37102_13006"


# native nodes can announce an optional flag before their compact record index
def Records(data, kind, fields, *, flagged=False):
    tag = bytes((0, kind))
    layout = Struct(fields)
    start = 0
    while (offset := data.find(tag, start)) >= 0:
        start = offset + 1
        body = offset + 2
        if flagged and data[body : body + 1] == b"\xff":
            body += 1
        if body + layout.size <= len(data):
            yield offset, layout.unpack_from(data, body)


# a named definition distinguishes the saved atom field from other integer attributes
def AtomDef(data):
    names = [
        index
        for _, (length, index, value) in Records(data, 79, ">IH12s")
        if length == len(KAtomName) and value == KAtomName and index > 1
    ]
    require(len(names) == 1, "partition atom identifier is absent or ambiguous")
    definitions = [
        index
        for _, (count, index, _, name, domain) in Records(data, 80, ">IHHHi24x")
        if count == 2 and name == names[0] and domain == 9000 and index > 1
    ]
    require(len(definitions) == 1, "partition atom definition is absent or ambiguous")
    return definitions[0]


# each shell owner must identify exactly one authored atom before geometry is considered
def BodyAtoms(data, owners, origin):
    definition = AtomDef(data)
    rows = [
        (owner, offset, attribute, value)
        for offset, (
            count,
            attribute,
            node,
            ref,
            owner,
            _,
            _,
            _,
            _,
            null,
            value,
        ) in Records(data, 81, ">IHI8H")
        if count == 2
        and ref == definition
        and node > 0
        and attribute > 1
        and null == 1
        and value > 1
    ]
    require(
        len(rows) == len(owners)
        and {row[0] for row in rows} == owners
        and len({row[2] for row in rows})
        == len({row[3] for row in rows})
        == len(owners),
        "partition atom attributes do not uniquely cover the shell owners",
    )
    indexes = {row[3] for row in rows}
    values = {}
    for offset, (count, index, atom) in Records(data, 82, ">IHi"):
        if count == 1 and index in indexes:
            require(
                index not in values and atom > 0, "partition atom value is ambiguous"
            )
            values[index] = (offset, atom)
    require(values.keys() == indexes, "partition atom value is absent")
    require(
        len({atom for _, atom in values.values()}) == len(owners),
        "partition atom IDs repeat",
    )
    return {
        owner: {
            "atom_attribute_index": attribute,
            "atom_attribute_offset": origin + offset,
            "atom_value_index": value,
            "atom_value_offset": origin + values[value][0],
            "recent_atom_id": values[value][1],
        }
        for owner, offset, attribute, value in rows
    }


# the fallback regions have no owner unless they match complete reciprocal native chains
def ShellFaces(data, table, shell, origin):
    records = [
        (offset, owner, head, region)
        for offset, (
            index,
            node,
            attr,
            owner,
            sibling,
            head,
            left,
            right,
            region,
            complement,
        ) in Records(data, 13, ">HI8H", flagged=True)
        if index == shell
        and node > 0
        and (attr, sibling, left, right, complement) == (1, 1, 1, 1, 1)
        and min(owner, head, region) > 1
        and head in table
    ]
    require(len(records) == 1, "solid shell is absent or ambiguous")
    offset, owner, head, region = records[0]
    regions = [
        position
        for position, (
            index,
            node,
            attr,
            body,
            sibling,
            previous,
            anchor,
            extra,
            sense,
        ) in Records(data, 19, ">HI6HB", flagged=True)
        if (index, body, anchor, sense) == (region, owner, shell, ord("S"))
        and node > 0
        and (attr, sibling, extra) == (1, 1, 1)
        and previous > 1
    ]
    require(len(regions) == 1, "solid region does not reciprocally own its shell")
    faces = {}
    previous = 1
    while head != 1:
        face = table.get(head)
        require(
            face is not None
            and head not in faces
            and face.references[1] == previous
            and face.references[3] == shell,
            "partition shell face chain is incomplete or nonreciprocal",
        )
        faces[head] = origin + face.offset
        previous, head = head, face.references[0]
    return {
        "body_index": owner,
        "shell_index": shell,
        "shell_offset": origin + offset,
        "region_index": region,
        "region_offset": origin + regions[0],
        "faces": [{"index": index, "offset": pos} for index, pos in faces.items()],
    }


# existing neutral topology can corroborate a native identity without assigning one by bounds
def ReadNativeIds(payload, region_faces):
    header = ParaHeaderData(payload)
    require(
        header is not None
        and header.schema == KScopeSchema
        and "transmit file (partition)" in header.description.casefold(),
        "unsupported scope partition identity schema",
    )
    origin = header.body_offset
    data = payload[origin:]
    tables = ScanPartRecords(data)
    require(tables is not None, "cannot recover scope partition faces")
    bridges = tables.bridges
    shells = {face.references[3] for face in bridges.values()}
    require(len(shells) == len(region_faces) == 2, "expected two native solid shells")
    native = [ShellFaces(data, bridges, shell, origin) for shell in shells]
    owners = {row["body_index"] for row in native}
    require(len(owners) == 2, "native shells share a single body owner")
    atoms = BodyAtoms(data, owners, origin)
    candidates = {}
    seen = set()
    for row in native:
        ids = {face["index"] for face in row["faces"]}
        require(not (seen & ids), "native shells share a face")
        seen.update(ids)
        decoded = {NativeId("face", index) for index in ids}
        matches = [region for region, faces in region_faces.items() if faces == decoded]
        require(
            len(matches) == 1 and matches[0] not in candidates,
            "native shell does not own one decoded region",
        )
        candidates[matches[0]] = {**row, **atoms[row["body_index"]]}
    require(seen == bridges.keys(), "native shells do not cover the partition faces")
    return candidates
