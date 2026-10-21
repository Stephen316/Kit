"""Dispatch an owned study generator to Fusion without global keyboard input.

Uses macOS accessibility for the known command field, and CGEventPostToPid for
Return directed only to Fusion. Never activates Fusion or uses a global key tap.
A successful dispatch is not proof that the generator ran: inspect its actual
output/ground_truth/complete files separately. Requires existing accessibility
and event-posting permissions; never opens a permission request.
"""

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess


def read_session_lock_state(cg=None, cf=None):
    """Read the explicit macOS lock Boolean, or None when unavailable.

    Missing keys never imply an unlocked session. Only this Boolean is read;
    no session identities, window contents, permission prompts or input events.
    """
    session = key = None
    try:
        cg = cg or ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        cf = cf or ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        cg.CGSessionCopyCurrentDictionary.argtypes = []
        cg.CGSessionCopyCurrentDictionary.restype = ctypes.c_void_p
        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint]
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p
        cf.CFDictionaryGetValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cf.CFDictionaryGetValue.restype = ctypes.c_void_p
        cf.CFGetTypeID.argtypes = [ctypes.c_void_p]
        cf.CFGetTypeID.restype = ctypes.c_ulong
        cf.CFBooleanGetTypeID.argtypes = []
        cf.CFBooleanGetTypeID.restype = ctypes.c_ulong
        cf.CFBooleanGetValue.argtypes = [ctypes.c_void_p]
        cf.CFBooleanGetValue.restype = ctypes.c_bool
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None
        session = cg.CGSessionCopyCurrentDictionary()
        if not session:
            return None
        key = cf.CFStringCreateWithCString(None, b'CGSSessionScreenIsLocked', 0x08000100)
        if not key:
            return None
        value = cf.CFDictionaryGetValue(session, key)
        if not value or cf.CFGetTypeID(value) != cf.CFBooleanGetTypeID():
            return None
        return bool(cf.CFBooleanGetValue(value))
    except (OSError, AttributeError):
        return None
    finally:
        if key:
            cf.CFRelease(key)
        if session:
            cf.CFRelease(session)


PREPARE = r'''
on run argv
 set commandText to item 1 of argv
 tell application "System Events"
  set frontBefore to unix id of first application process whose frontmost is true
  tell process "Autodesk Fusion"
   set targetPid to unix id
   set mainWindow to first window whose name contains "Autodesk Fusion (Education License)"
   if value of radio button "Txt" of mainWindow is not 1 then
    perform action "AXPress" of radio button "Txt" of mainWindow
   end if
   set value of text field 1 of mainWindow to commandText
   set value of attribute "AXFocused" of text field 1 of mainWindow to true
   set fieldReady to ((value of text field 1 of mainWindow is commandText) and (value of attribute "AXFocused" of text field 1 of mainWindow is true) and (value of radio button "Txt" of mainWindow is 1))
  end tell
  set frontAfter to unix id of first application process whose frontmost is true
  if frontBefore is not frontAfter then
   if frontAfter is targetPid then
    set frontmost of first application process whose unix id is frontBefore to true
   end if
   error "Command-field preparation changed foreground focus; no event posted"
  end if
  if fieldReady is not true then error "Fusion text command field could not be verified; no event posted"
  return (frontBefore as text) & "|" & (targetPid as text)
 end tell
end run
'''


def dispatch(path):
    path = Path(path).resolve(strict=True)
    if path.parent != Path(__file__).resolve().parent or not path.name.startswith("Generate") or path.suffix != ".py":
        raise ValueError("Only an existing generator in this study directory can be dispatched")
    hold = Path(__file__).with_name('fusion-live-capture-hold.json')
    validation_only = False
    if hold.exists():
        state = json.loads(hold.read_text())
        if state.get('active', True):
            validation = state.get('authorized_validation', {})
            dependencies = validation.get('dependency_sha256', {})
            validation_only = (validation.get('generator') == path.name
                and validation.get('sha256') == hashlib.sha256(path.read_bytes()).hexdigest()
                and bool(validation.get('user_authorization'))
                and isinstance(dependencies, dict) and bool(dependencies)
                and all(Path(name).name == name and (path.parent/name).is_file()
                        and hashlib.sha256((path.parent/name).read_bytes()).hexdigest() == digest
                        for name, digest in dependencies.items()))
            if not validation_only:
                raise RuntimeError('Live Fusion captures are suspended after repeated native trim-cleanup crashes. '
                                   'Only an explicitly authorized validation with matching source hashes may run '
                                   'before the capture hold is cleared.')
    if any(character in str(path) for character in ('"', "\\", "\r", "\n")):
        raise ValueError("Unsupported generator path quoting")
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    if read_session_lock_state(cg, cf) is True:
        raise RuntimeError('macOS session is locked; no Fusion command prepared or keyboard event created. '
                           'Unlock the Mac and leave Fusion visible before resuming captures.')
    cg.CGPreflightPostEventAccess.argtypes = []
    cg.CGPreflightPostEventAccess.restype = ctypes.c_bool
    if not cg.CGPreflightPostEventAccess():
        raise RuntimeError("Event-posting access is not already authorized; no permission prompt opened")
    cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_ushort, ctypes.c_bool]
    cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
    cg.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
    cg.CGEventSetFlags.restype = None
    cg.CGEventPostToPid.argtypes = [ctypes.c_int, ctypes.c_void_p]
    cg.CGEventPostToPid.restype = None
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    cf.CFRelease.restype = None
    events = [cg.CGEventCreateKeyboardEvent(None, 36, down) for down in (True, False)]
    try:
        if not all(events):
            raise RuntimeError("Could not create both target-only Return events")
        for event in events:
            cg.CGEventSetFlags(event, 0)
        command = 'Python.RunScript "'+str(path)+'"'
        try:
            prepared = subprocess.run(["/usr/bin/osascript", "-", command], input=PREPARE,
                                      text=True, capture_output=True, check=True, timeout=20)
        except subprocess.CalledProcessError as error:
            raise RuntimeError('Fusion command-field preparation failed before Return was posted: '
                               + error.stderr.strip()) from error
        foreground_pid, target_pid = map(int, prepared.stdout.strip().split("|"))
        if target_pid <= 0:
            raise RuntimeError("Invalid Fusion PID; no event posted")
        for event in events:
            cg.CGEventPostToPid(target_pid, event)
        return {"status": "Targeted command dispatched; execution unverified", "generator": path.name,
                "target_pid": target_pid, "foreground_pid_during_preparation": foreground_pid,
                "authorized_lifecycle_validation_only": validation_only,
                "global_keyboard_events": False,
                "next_evidence": "Actual generator output and terminal complete/error records"}
    finally:
        for event in events:
            if event:
                cf.CFRelease(event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generator", type=Path, nargs='?')
    parser.add_argument('--session-state', action='store_true',
                        help='Read only the explicit macOS lock flag; never prepare or dispatch a command')
    args = parser.parse_args()
    if args.session_state:
        if args.generator is not None:
            parser.error('--session-state does not accept a generator')
        print(json.dumps(dict(session_locked=read_session_lock_state(), no_ui_events=True,
                              scope='Explicit lock Boolean only; null means unavailable, not unlocked')))
    else:
        if args.generator is None:
            parser.error('a generator is required unless --session-state is used')
        print(json.dumps(dispatch(args.generator)))
