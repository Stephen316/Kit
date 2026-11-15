import json
import subprocess
import sys
import time
from pathlib import Path
from plistlib import dumps

from ApplicationProtocol import MAC_REPLACEMENT_LAUNCH, sha256
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer
from MacBundleLaunch import launch_bundle
from MacProcessExit import observe_exit, watch_peer

ROOT = Path(__file__).resolve().parents[3]
APPLICATION = """
#import <Cocoa/Cocoa.h>
int main(void) {
    @autoreleasepool {
        NSApplication *application = [NSApplication sharedApplication];
        [application setActivationPolicy:NSApplicationActivationPolicyAccessory];
        NSString *directory = [[[NSBundle mainBundle] bundlePath] stringByDeletingLastPathComponent];
        NSString *stop = [directory stringByAppendingPathComponent:@"NaturalExit"];
        NSDate *deadline = [NSDate dateWithTimeIntervalSinceNow:100];
        [NSTimer scheduledTimerWithTimeInterval:0.05 repeats:YES block:^(NSTimer *timer) {
            if ([[NSFileManager defaultManager] fileExistsAtPath:stop] ||
                [deadline timeIntervalSinceNow] <= 0) {
                [application terminate:nil];
            }
        }];
        [application run];
    }
    return 0;
}
"""


def fixture_bundle(root):
    bundle = root / "Replacement.app"
    binary = bundle / "Contents/MacOS/Replacement"
    binary.parent.mkdir(parents=True)
    info = dumps(
        {
            "CFBundleIdentifier": "org.unicad.kit.replacementfixture",
            "CFBundleExecutable": "Replacement",
            "CFBundlePackageType": "APPL",
            "LSUIElement": True,
        }
    )
    (bundle / "Contents/Info.plist").write_bytes(info)
    compiled = subprocess.run(
        [
            "/usr/bin/clang",
            "-x",
            "objective-c",
            "-framework",
            "Cocoa",
            "-o",
            str(binary),
            "-",
        ],
        input=APPLICATION,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert compiled.returncode == 0, compiled.stderr
    return pinned_bundle(
        json.dumps(
            {
                "version": 1,
                "installation_sha256": "a" * 64,
                "bundle": str(bundle),
                "info_sha256": sha256(info),
                "executable_sha256": sha256(binary.read_bytes()),
            }
        ).encode(),
        "a" * 64,
    )


def prior_peer():
    with subprocess.Popen(
        [sys.executable, "-B", "-c", "import sys; sys.stdin.readline()"],
        stdin=subprocess.PIPE,
        text=True,
    ) as process:
        peer = process_peer(process.pid)
        process.communicate("\n", timeout=10)
        assert process.returncode == 0
    return {key: value for key, value in peer.items() if key != "executable"}


def exercise(root):
    bundle = fixture_bundle(root)
    source = (ROOT / MAC_REPLACEMENT_LAUNCH).read_bytes()
    old = prior_peer()
    fence = b"retained disposable restart fence\n"
    fence_path = root / "fence.json"
    fence_path.write_bytes(fence)
    request = root / "LaunchRequest.json"
    request_bytes = json.dumps({"fence_sha256": sha256(fence)}).encode()
    request.write_bytes(request_bytes)
    custody = (request, sha256(request_bytes))
    observed = None
    try:
        try:
            launch_bundle(
                source,
                {**bundle, "executable_sha256": "0" * 64},
                time.time(),
                old,
                30,
                *custody,
            )
        except ValueError as error:
            assert "did not return an exact process" in str(error)
        else:
            raise AssertionError("AppKit helper accepted changed bundle bytes")
        fence_path.write_bytes(b"changed disposable fence\n")
        try:
            launch_bundle(source, bundle, time.time(), old, 30, *custody)
        except ValueError as error:
            assert "did not return an exact process" in str(error)
        else:
            raise AssertionError("AppKit helper launched after the exact fence changed")
        fence_path.write_bytes(fence)
        observed = launch_bundle(source, bundle, time.time(), old, 30, *custody)
        assert (
            observed["peer"]["pid"] != old["pid"]
            and observed["peer"]["uid"] == old["uid"]
        )
        try:
            launch_bundle(source, bundle, time.time(), old, 30, *custody)
        except ValueError as error:
            assert "counterpart prevents replacement launch" in str(error)
        else:
            raise AssertionError("AppKit helper launched a duplicate counterpart")
        print(
            json.dumps(
                {
                    "peer": observed["peer"],
                    "source_pin_refused": True,
                    "fence_change_refused": True,
                    "duplicate_refused": True,
                }
            )
        )
    finally:
        stop = root / "NaturalExit"
        if observed is None:
            stop.touch()
        else:
            with watch_peer(observed["peer"], bundle["executable"]) as monitor:
                stop.touch()
                assert observe_exit(monitor, observed["peer"], 10) is not None


if __name__ == "__main__":
    exercise(Path(sys.argv[1]))
