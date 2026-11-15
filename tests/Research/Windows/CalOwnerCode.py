KCalOwnerCode = """
import json
import os
import sys
import time
from pathlib import Path

root, config, children = map(Path, sys.argv[1:4])
sys.path.insert(0, str(root / 're/automation'))
from CalibrationProcesses import start_supervisor
from LogCapture import LogCapture

capture = LogCapture(config.parent / 'Owner.log', 1048576)
command = [sys.executable, str(root / 're/automation/Supervisor.py'), '--config', str(config), 'run', '--max-seconds', '60']
owner, _ = start_supervisor(command, root, config.parent, capture.writer, None, 'decode')
capture.close_writer()
try:
    deadline = time.monotonic() + 30
    while owner.poll() is None and time.monotonic() < deadline:
        capture.drain()
        workers = owner.sample_workers()
        if workers and children.is_file():
            try:
                pids = json.loads(children.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                time.sleep(0.05)
                continue
            assert set(pids) <= set(owner.members()), pids
            print(json.dumps({'pids': [owner.pid, owner.interpreter[0], *pids], 'bytes': workers}), flush=True)
            if sys.argv[4] == 'abrupt':
                os._exit(7)
            print(json.dumps(owner.force_stop()), flush=True)
            break
        time.sleep(0.05)
    else:
        raise RuntimeError('No contained worker observation')
finally:
    owner.retire()
    capture.close()
"""
