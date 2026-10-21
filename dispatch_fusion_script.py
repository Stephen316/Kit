"""Dispatch an owned study generator to Fusion without global keyboard input.

Uses macOS accessibility for the known command field, and CGEventPostToPid for
Return directed only to Fusion. Never activates Fusion or uses a global key tap.
A successful dispatch is not proof that the generator ran: inspect its actual
output/ground_truth/complete files separately. Requires existing accessibility
and event-posting permissions; never opens a permission request.
"""

import argparse
import ctypes
import json
from pathlib import Path
import subprocess


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
    if hold.exists():
        state = json.loads(hold.read_text())
        if state.get('active', True):
            raise RuntimeError('Live Fusion captures are suspended after repeated native trim-cleanup crashes. '
                               'Continue offline; review fusion-trim-crash-investigation.json and obtain '
                               'explicit user authorization before clearing fusion-live-capture-hold.json.')
    if any(character in str(path) for character in ('"', "\\", "\r", "\n")):
        raise ValueError("Unsupported generator path quoting")
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
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
                "global_keyboard_events": False,
                "next_evidence": "Actual generator output and terminal complete/error records"}
    finally:
        for event in events:
            if event:
                cf.CFRelease(event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generator", type=Path)
    args = parser.parse_args()
    print(json.dumps(dispatch(args.generator)))
