import collections
import glob
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadBoardMut as BoardModule
import convert.formats.Fusion.Topology.AsmEdge.AsmTable as StatesModule

# lift the production bounds so the measured maxima are not clipped by them
BoardModule.KBoardChanges = 1 << 20
StatesModule.KRecordTokens = 1 << 20
sys.path.insert(0, str(Path(__file__).parent))
from Journals import raw_model


def main():
    rows = []
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        archive = zipfile.ZipFile(path)
        for info in archive.infolist():
            if not info.filename.endswith('.smbh'):
                continue
            try:
                model = raw_model(archive.read(info.filename))
            except Exception as error:
                rows.append({'file': str(Path(path).relative_to(ROOT)), 'error': f'{type(error).__name__}: {error}'})
                continue
            board_sizes = [len(board.Changes) for state in model.States for board in state.Boards]
            state_sizes = [sum(len(board.Changes) for board in state.Boards) for state in model.States]
            repeats = 0
            for state in model.States:
                for board in state.Boards:
                    counts = collections.Counter(ref for change in board.Changes for ref in (change.OldRef, change.NewRef) if ref != -1)
                    repeats = max(repeats, max(counts.values(), default=0))
            rows.append({
                'file': str(Path(path).relative_to(ROOT)),
                'entities': len(model.Entities),
                'states': len(model.States),
                'max_board_changes': max(board_sizes, default=0),
                'max_state_changes': max(state_sizes, default=0),
                'max_boards': max((len(state.Boards) for state in model.States), default=0),
                'max_reference_repeats_in_board': repeats,
            })
    good = [row for row in rows if 'error' not in row]
    good.sort(key=lambda row: -row['max_board_changes'])
    report = {
        'scope': 'Bulletin-board sizes of every .smbh history under re/ read with relaxed record and board limits',
        'histories': len(rows),
        'errors': len(rows) - len(good),
        'max_board_changes': good[0]['max_board_changes'],
        'max_state_changes': max(row['max_state_changes'] for row in good),
        'max_boards_per_state': max(row['max_boards'] for row in good),
        'max_entities': max(row['entities'] for row in good),
        'boards_over_entity_count': sum(row['max_board_changes'] > row['entities'] for row in good),
        'max_reference_repeats_in_board': max(row['max_reference_repeats_in_board'] for row in good),
        'histories_over_1000_board_changes': sum(row['max_board_changes'] > 1000 for row in good),
        'error_causes': dict(collections.Counter(row['error'] for row in rows if 'error' in row).most_common()),
        'largest': good[:30],
    }
    Path(__file__).with_name('BoardChanges.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'largest'}, indent=1))
    for row in good[:16]:
        print(row)


if __name__ == '__main__':
    main()
