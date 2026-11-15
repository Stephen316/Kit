import os as OsLayer
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.SupervisorClient import KRepoRoot


# cleanup evidence needs a real owned windows handle while leaving the licensed application untouched
@TestMark.skipif(OsLayer.name != "nt", reason="requires Windows process identity")
@TestMark.parametrize(
    ("ModeName", "FaultName"),
    (
        ("timeout", "missing"),
        ("timeout", "ticket"),
        ("timeout", "identity"),
        ("timeout", "exited"),
        ("failure", "none"),
        ("failure", "missing"),
        ("failure", "ticket"),
        ("failure", "identity"),
        ("failure", "deadline"),
    ),
)
def CheckOwnerGuard(ModeName: str, FaultName: str) -> None:
    with TempFiles.TemporaryDirectory() as TempName:
        RootPath = FilePath(TempName).resolve()
        ScriptPath = RootPath / "OwnerProbe.py"
        _ = ScriptPath.write_text(
            """import os
import subprocess
import sys
import time
from pathlib import Path
import win32event
import win32process

sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import encoded, identity, record, sha256, write_record
from SolidWorksReadbackWorker import BUILD, native_identity, record_collector_failure, record_timeout

root = Path(__file__).parent
output = root / 'readback'
output.mkdir()
exe = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
startup = win32process.STARTUPINFO()
def arguments(script):
    return [exe, '-NoProfile', '-NonInteractive', '-Command', script]

handle, thread, _, _ = win32process.CreateProcess(
    exe, subprocess.list2cmdline(arguments('Start-Sleep -Seconds 30')),
    None, None, False, subprocess.CREATE_NO_WINDOW, None, str(root), startup,
)
thread.Close()
try:
    listener = identity(os.getpid())
    request = {'version': 1, 'job_id': 'a' * 32, 'source_revision': 'b' * 40,
               'nonce': 'c' * 48, 'client': listener, 'installation': 'fixture:readback'}
    mode, fault = sys.argv[2:]
    if mode == 'failure':
        request['deadline'] = time.time() + (-1 if fault == 'deadline' else 25)
    launch = {'version': 1, 'request_sha256': sha256(encoded(request)),
              'source_revision': request['source_revision'], **native_identity(handle)}
    if fault == 'identity':
        launch['created'] = 'windows:1'
    if fault != 'missing':
        ticket = {**launch, 'build': BUILD, 'initial_documents': 0}
        if fault == 'ticket':
            ticket['request_sha256'] = 'd' * 64
        write_record(output / 'native-owner.json', ticket)
    if fault == 'exited':
        win32process.TerminateProcess(handle, 0)
        assert win32event.WaitForSingleObject(handle, 5000) == win32event.WAIT_OBJECT_0
    return_code = 17 if mode == 'failure' else 0
    with subprocess.Popen(arguments(f'exit {return_code}'), creationflags=subprocess.CREATE_NO_WINDOW) as collector:
        assert collector.wait(timeout=10) == return_code
        if mode == 'failure':
            record_collector_failure(root, request, listener, collector, handle, launch)
        else:
            record_timeout(root, request, listener, collector, handle, launch, True)
    if mode == 'failure':
        result = record(root / 'native-failure-recovery.json')
        assert result['trigger'] == 'collector_failure' and result['collector_return_code'] == 17
        assert not (root / 'native-timeout-request.json').exists()
        assert not (root / 'native-recovery.json').exists()
    else:
        result = record(root / 'native-recovery.json')
        assert result['trigger'] == 'collector_timeout'
        assert (root / 'native-timeout-request.json').read_bytes() == encoded(request)
    assert result['request_sha256'] == sha256(encoded(request)) and result['nonce'] == request['nonce']
    assert result['queue_job_id'] == request['job_id'] and result['listener'] == listener
    if fault == 'exited':
        assert result['status'] == 'already_exited'
        assert result['owner_ticket_sha256'] == sha256(encoded(ticket))
    elif fault == 'none':
        assert result['status'] == 'terminated_owned_process'
        assert result['owner_ticket_sha256'] == sha256(encoded(ticket))
        assert win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_OBJECT_0
    else:
        expected = {'missing': 'FileNotFoundError', 'ticket': 'did not ticket',
                    'identity': 'identity changed', 'deadline': 'deadline expired'}
        assert result['status'] == 'quarantined' and expected[fault] in result['reason'], result
        assert 'owner_ticket_sha256' not in result
        assert win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_TIMEOUT
finally:
    if win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_TIMEOUT:
        win32process.TerminateProcess(handle, 1)
        assert win32event.WaitForSingleObject(handle, 5000) == win32event.WAIT_OBJECT_0
    handle.Close()
""",
            encoding="utf-8",
        )
        Result = Subprocess.run(
            [
                System.executable,
                str(ScriptPath),
                str(KRepoRoot / "re/automation/ApplicationWorkers"),
                ModeName,
                FaultName,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
        assert Result.returncode == 0, Result.stdout + Result.stderr
