import ctypes
import os
import sys


class QuitUnavailable(RuntimeError):
    pass


def request_quit():
    if sys.platform != "darwin":
        raise QuitUnavailable("normal Cocoa quit requires macOS")
    try:
        mode = os.RTLD_NOLOAD | os.RTLD_LOCAL
        system = ctypes.CDLL("/usr/lib/libSystem.B.dylib", mode=mode)
        is_main_thread = system.pthread_main_np
        is_main_thread.argtypes = ()
        is_main_thread.restype = ctypes.c_int
    except (AttributeError, OSError) as error:
        raise QuitUnavailable("macOS main-thread check is unavailable") from error
    if is_main_thread() != 1:
        raise QuitUnavailable("normal Cocoa quit requires the main thread")

    try:
        appkit = ctypes.CDLL(
            "/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit",
            mode=mode,
        )
        app = ctypes.c_void_p.in_dll(appkit, "NSApp").value
    except (OSError, ValueError) as error:
        raise QuitUnavailable(
            "the existing AppKit application is unavailable"
        ) from error
    if app is None:
        raise QuitUnavailable("the existing AppKit application is unavailable")

    try:
        objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib", mode=mode)
        selector_for = objc.sel_registerName
        selector_for.argtypes = (ctypes.c_char_p,)
        selector_for.restype = ctypes.c_void_p
        selector = selector_for(b"terminate:")
        send = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(("objc_msgSend", objc))
    except (AttributeError, OSError) as error:
        raise QuitUnavailable("normal Cocoa quit is unavailable") from error
    if selector is None:
        raise QuitUnavailable("normal Cocoa quit is unavailable")
    send(app, selector, None)
