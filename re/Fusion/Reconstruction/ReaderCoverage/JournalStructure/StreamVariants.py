import collections
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadBoardMut as BoardModule
import convert.formats.Fusion.Topology.AsmEdge.AsmTable as StatesModule

BoardModule.KBoardChanges = 1 << 20
StatesModule.KRecordTokens = 1 << 20
sys.path.insert(0, str(Path(__file__).parent))
from Journals import members, raw_model


# every saved history stream: which header nodes are set and what the working node looks like
def main():
    shapes = collections.Counter()
    working = []
    errors = 0
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        for name, payload in members(path, '.smbh').items():
            try:
                model = raw_model(payload)
            except Exception:
                errors += 1
                continue
            stream = model.Stream
            shapes[json.dumps({
                'max_states_to_keep': stream.MaxStatesToKeep,
                'owner_entity': stream.OwnerEntity,
                'working': 'none' if stream.WorkingNode == -1 else ('active' if stream.WorkingNode == stream.ActiveNode else 'other'),
            }, sort_keys=True)] += 1
            if stream.WorkingNode == -1:
                continue
            state = model.States[stream.WorkingNode]
            closed = model.States[state.NextNode] if state.NextNode != -1 else None
            working.append({
                'file': str(Path(path).relative_to(ROOT)),
                'current_state_id': stream.CurrentStateId,
                'working_state_id': state.StateId,
                'working_previous': state.PreviousNode,
                'working_boards': [len(board.Changes) for board in state.Boards],
                'next_state_id': None if closed is None else closed.StateId,
                'next_matches_current': closed is not None and closed.StateId == stream.CurrentStateId,
            })
    report = {
        'scope': 'History stream header shapes of every .smbh under re/, plus the open working delta when WorkingNode is set',
        'unread': errors,
        'shapes': {key: value for key, value in shapes.most_common()},
        'working': working,
    }
    Path(__file__).with_name('StreamVariants.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'working'}, indent=1))
    print(len(working), 'working', collections.Counter((row['working_state_id'], tuple(row['working_boards']), row['next_matches_current']) for row in working))


if __name__ == '__main__':
    main()
