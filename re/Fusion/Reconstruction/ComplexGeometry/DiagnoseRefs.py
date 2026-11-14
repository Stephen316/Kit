import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Validation.EntityRefRules import KEntityRefRules  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode  # noqa: E402
from convert.formats.Fusion.MetaCursor import MetaCursor  # noqa: E402


def main():
    data = json.loads((BASE / "VerifyComplex.json").read_text())
    issues = collections.Counter()
    for member in data["members"]:
        if "class-incompatible" not in member.get("error", "") or not member["member"].endswith(".smb"):
            continue
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            payload = archive.read(member["member"])
        cursor = MetaCursor(payload)
        ReadModelHead(cursor, False)
        records = [MakeEntityNode(value) for value in ReadEntitiesMut(cursor, "End-of-ASM-data")]
        for index, record in enumerate(records):
            rules = KEntityRefRules[record.Name]
            for position, (tag, value) in enumerate(record.Tokens):
                if tag != 12 or value == -1:
                    continue
                if position not in rules or records[value].Name not in rules[position]:
                    issues[(record.Name, position, records[value].Name, str(record.Tokens[5]))] += 1
    for key, count in issues.items():
        print(count, key)


main()
