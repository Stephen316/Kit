import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import ReadEntityNode
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import BulletinChange
from convert.formats.Fusion.BrepCodec.Journal.Validation.BuildAliases import BuildAliases
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.BrepCodec.Journal.Validation.UndoStateMut import UndoStateMut
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def pop_head(model):
    aliases = BuildAliases(model)
    head_index = model.Stream.ActiveNode
    head = model.States[head_index]
    versions = {i: i for i in range(model.ActiveCount)}
    UndoStateMut(head, versions, aliases)
    live_slots = sorted(versions)
    live_pos = {slot: index for index, slot in enumerate(live_slots)}
    remaining = [i for i in range(len(model.States)) if i != head_index]
    archived = [c.OldRef for i in remaining for b in model.States[i].Boards for c in b.Changes if c.OldRef >= 0]
    archived_pos = {old: len(live_slots) + index for index, old in enumerate(archived)}

    def mapref(ref):
        if ref in archived_pos:
            return archived_pos[ref]
        slot = ResolveSlot(aliases, ref)
        if slot in live_pos:
            return live_pos[slot]
        raise ValueError("Dangling reference after truncation %d" % ref)

    def remap(entity):
        record = MakeEntityNode(entity)
        tokens = tuple((tag, mapref(field)) if tag == 12 and isinstance(field, int) and field >= 0 else (tag, field) for tag, field in record.Tokens)
        return ReadEntityNode(AsmRecord(record.Name, tokens))

    entities = [remap(model.Entities[versions[slot]]) for slot in live_slots] + [remap(model.Entities[old]) for old in archived]
    node_pos = {old: new for new, old in enumerate(remaining)}

    def mapnode(node):
        return -1 if node == -1 else node_pos[node]

    states = []
    for old in remaining:
        state = model.States[old]
        boards = tuple(BulletinBoard(mapnode(board.OwnerNode) if board.OwnerNode >= 0 else board.OwnerNode, board.Status, tuple(BulletinChange(archived_pos[c.OldRef] if c.OldRef >= 0 else -1, mapref(c.NewRef) if c.NewRef >= 0 else -1) for c in board.Changes)) for board in state.Boards)
        previous = -1 if state.PreviousNode == head_index else mapnode(state.PreviousNode)
        states.append(replace(state, PreviousNode=previous, NextNode=mapnode(state.NextNode), PartnerNode=mapnode(state.PartnerNode), Boards=boards, StateLinks=tuple(mapnode(n) for n in state.StateLinks)))
    new_head = node_pos[head.NextNode]
    stream = replace(model.Stream, CurrentStateId=states[new_head].StateId, ActiveNode=new_head, InitialNode=mapnode(model.Stream.InitialNode))
    bodies = sum(type(entity).__name__ == "BodyNode" for entity in entities[: len(live_slots)])
    result = replace(model, Header=replace(model.Header, RootCount=bodies + 1), ActiveCount=len(live_slots), Entities=tuple(entities), States=tuple(states), Stream=stream)
    Materialize(result)
    return result


def truncate(model, state_id):
    while model.Stream.CurrentStateId != state_id:
        model = pop_head(model)
    return model


def rewrite(source, target, state_id, design_edit=None):
    with ZipFile(source) as archive:
        members = [n for n in archive.namelist() if n.endswith(".smbh")]
        if len(members) != 1:
            raise ValueError("Expected one journal")
        original = ReadJournal(archive.read(members[0]))
        model = truncate(original, state_id)
        emitted = EmitJournal(model)
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as output:
            for entry in archive.infolist():
                data = archive.read(entry.filename)
                if entry.filename == members[0]:
                    data = emitted
                if entry.is_dir():
                    output.writestr(entry, b"")
                else:
                    output.writestr(entry.filename, data)
    return {"source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "target": target.name, "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "history_member": members[0].split("/")[-1], "original_stream": asdict(original.Stream), "truncated_stream": asdict(model.Stream), "original_states": [s.StateId for s in Materialize(original)], "truncated_states": [s.StateId for s in Materialize(model)], "original_entities": len(original.Entities), "truncated_entities": len(model.Entities), "truncated_active": model.ActiveCount}


if __name__ == "__main__":
    controls = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Controls"
    output = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Recompute"
    output.mkdir(parents=True, exist_ok=True)
    cases = [("Fillet", 5, "FilletWithoutFilletState"), ("ExtrudeCut", 5, "ExtrudeCutWithoutCutState"), ("MultiFeature", 16, "MultiFeatureBaseStateOnly"), ("Shell", 5, "ShellWithoutShellState"), ("RectPattern", 17, "RectPatternWithoutPatternState"), ("Chamfer", 5, "ChamferWithoutChamferState"), ("MirrorBody", 6, "MirrorBodyWithoutMirrorState")]
    report = {"scope": "Same-source native controls with typed truncation of the BRep journal only; Design records unchanged; recompute experiment evidence, not Kit authoring", "cases": []}
    for source, state_id, name in cases:
        entry = rewrite(controls / (source + ".f3d"), output / (name + ".f3d"), state_id)
        entry["name"] = name
        report["cases"].append(entry)
        print(name, entry["original_states"], "->", entry["truncated_states"], entry["truncated_entities"])
    (output / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n")
