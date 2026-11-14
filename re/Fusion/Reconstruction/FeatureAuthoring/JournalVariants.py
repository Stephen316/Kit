"""Build journal-swap variants that isolate why Fusion rejects a Kit part journal.

Run with Python 3.14 from the repository root. Each variant keeps one side of
the document fixed (Design records or BRep journal) and swaps or edits the
other, so a native open separates record faults from journal faults.
"""

import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import EmitAuthored  # noqa: E402
import TruncateHistory  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EmitPartHist import EmitPartHist  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import BuildShape  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart  # noqa: E402

OUTPUT = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Variants"
CONTROLS = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Controls"


def journal_member(payload):
    with ZipFile(__import__("io").BytesIO(payload)) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".smbh"))
        return name, archive.read(name)


def swap_journal(payload, journal):
    import io

    source = ZipFile(io.BytesIO(payload))
    name = next(n for n in source.namelist() if n.endswith(".smbh"))
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as output:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == name:
                data = journal
            output.writestr(entry.filename, data)
    return buffer.getvalue()


def strip_tags(model, body_tag=0):
    entities = []
    for index, entity in enumerate(model.Entities):
        prefix = getattr(entity, "Prefix", None)
        if prefix is not None and prefix.EntityTag >= 0:
            tag = body_tag if type(entity).__name__ == "BodyNode" else -1
            entity = replace(entity, Prefix=replace(prefix, EntityTag=tag))
        entities.append(entity)
    return replace(model, Entities=tuple(entities), Stream=replace(model.Stream, NextEntityTag=body_tag + 1))


def renumber(model, mapping):
    states = tuple(replace(s, StateId=mapping.get(s.StateId, s.StateId)) for s in model.States)
    current = mapping.get(model.Stream.CurrentStateId, model.Stream.CurrentStateId)
    return replace(model, States=states, Stream=replace(model.Stream, CurrentStateId=current, MaxStateId=current))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    micros = float(time.time_ns() // 1000)
    variants = {}
    box_spec = EmitAuthored.spec("Box", ())
    box_payload = EmitDocument(box_spec)
    fillet_spec = EmitAuthored.spec("Fillet", EmitAuthored.CASES["Fillet"])
    fillet_payload = EmitDocument(fillet_spec)
    base, stages = SolvePart(fillet_spec)
    single = EmitPartHist(((BuildShape(base),),), (4,), 2, micros)
    variants["BoxProduction"] = (box_payload, "plain cuboid document, production prism journal (control)")
    variants["BoxKitJournal"] = (swap_journal(box_payload, single), "plain cuboid Design with the Kit part-journal emitter for one state")
    variants["BoxKitNoTags"] = (swap_journal(box_payload, EmitJournal(strip_tags(ReadJournal(single)))), "as BoxKitJournal with face entity tags removed and body tag 0")
    _, kit_journal = journal_member(fillet_payload)
    kit_model = ReadJournal(kit_journal)
    variants["FilletKit"] = (fillet_payload, "Kit fillet document as authored")
    variants["FilletKitBaseOnly"] = (swap_journal(fillet_payload, EmitJournal(TruncateHistory.truncate(kit_model, 4))), "Kit fillet Design with the Kit journal truncated to the base state")
    variants["FilletKitNoTags"] = (swap_journal(fillet_payload, EmitJournal(strip_tags(kit_model))), "Kit fillet document with face entity tags removed")
    native_journal = ReadJournal(journal_member((CONTROLS / "Fillet.f3d").read_bytes())[1])
    variants["FilletNativeJournal"] = (swap_journal(fillet_payload, EmitJournal(renumber(native_journal, {5: 4, 6: 5}))), "Kit fillet Design with the native control journal renumbered to Kit state ids")
    manifest = {}
    for name, (payload, purpose) in variants.items():
        _, journal = journal_member(payload)
        model = ReadJournal(journal)
        Materialize(model)
        path = OUTPUT / (name + ".f3d")
        path.write_bytes(payload)
        manifest[name] = {"file": path.name, "sha256": hashlib.sha256(payload).hexdigest(), "purpose": purpose, "states": [s.StateId for s in model.States], "entities": len(model.Entities)}
        print(name, manifest[name]["states"], manifest[name]["entities"])
    (OUTPUT / "Manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
