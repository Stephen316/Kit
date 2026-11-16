import AppKit
import CryptoKit
import Darwin
import Foundation

func refuse(_ code: Int32, _ reason: String) -> Never {
    FileHandle.standardError.write(Data((reason + "\n").utf8))
    exit(code)
}

func boundedBytes(_ file: URL, maximum: Int) -> Data? {
    guard let size = try? file.resourceValues(forKeys: [.fileSizeKey]).fileSize,
          size > 0, size <= maximum,
          let bytes = try? Data(contentsOf: file, options: [.mappedIfSafe]),
          bytes.count == size else {
        return nil
    }
    return bytes
}

func digest(_ bytes: Data) -> String {
    return SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
}

func digest(_ file: URL, maximum: Int) -> String? {
    return boundedBytes(file, maximum: maximum).map(digest)
}

func matchesPhysicalPath(_ observed: String, _ expected: String) -> Bool {
    guard observed.hasPrefix("/"), !observed.utf8.contains(0),
          let resolved = observed.withCString({ Darwin.realpath($0, nil) }) else {
        return false
    }
    defer { Darwin.free(resolved) }
    let path = UnsafeRawBufferPointer(start: resolved, count: Darwin.strlen(resolved))
    return path.elementsEqual(expected.utf8)
}

func matchesPhysicalFileURL(_ observed: URL?, _ expected: String) -> Bool {
    guard let observed, observed.isFileURL else {
        return false
    }
    return matchesPhysicalPath(observed.path, expected)
}

func absent(_ path: String) -> Bool {
    var info = stat()
    return path.withCString { Darwin.lstat($0, &info) == -1 && errno == ENOENT }
}

func coldEndpointIsEmpty(_ root: String) -> Bool {
    let jobs = root + "/jobs"
    let clear = ["fence.json", "acceptance-journal.json", "fusion-lifecycle-active.json"].allSatisfy {
        absent(root + "/" + $0)
    }
    return clear && matchesPhysicalPath(jobs, jobs)
        && (try? FileManager.default.contentsOfDirectory(atPath: jobs)) == []
}

let arguments = CommandLine.arguments
let coldStart = arguments.count == 11 && arguments[10] == "cold-start"
guard [9, 10].contains(arguments.count) || coldStart,
      arguments[1].hasPrefix("/"),
      let wait = Double(arguments[6]),
      wait > 0, wait <= 300 else {
    refuse(1, "Expected an exact application bundle and bounded launch deadline")
}

let path = arguments[1]
let executable = arguments[2]
let identifier = arguments[3]
let target = URL(fileURLWithPath: path, isDirectory: true)
let infoPath = path + "/Contents/Info.plist"
let info = URL(fileURLWithPath: infoPath)
guard matchesPhysicalPath(path, path),
      matchesPhysicalPath(executable, executable),
      matchesPhysicalPath(infoPath, infoPath),
      let application = Bundle(url: target),
      application.bundleIdentifier == identifier,
      let entry = application.executableURL,
      matchesPhysicalFileURL(entry, executable),
      digest(info, maximum: 1_048_576) == arguments[4],
      digest(entry, maximum: 268_435_456) == arguments[5] else {
    refuse(5, "Application bundle does not match the reviewed launch profile")
}

let requestPath = arguments[7]
let root = (requestPath as NSString).deletingLastPathComponent
let fencePath = root + "/fence.json"
let request = URL(fileURLWithPath: requestPath)
let fence = URL(fileURLWithPath: fencePath)
guard matchesPhysicalPath(requestPath, requestPath),
      let requestData = boundedBytes(request, maximum: 1_048_576),
      digest(requestData) == arguments[8],
      let decoded = try? JSONSerialization.jsonObject(with: requestData),
      let record = decoded as? [String: Any] else {
    refuse(6, "Exact launch request custody is unavailable")
}
let coldChallenge: String?
let fenceDigest: String?
if coldStart {
    let draftPath = root + "/cold-start-request.json"
    guard (requestPath as NSString).lastPathComponent == "cold-start-launch.json",
          record["scope"] as? String == "owner_fusion_cold_start_launch",
          let challenge = record["launch_challenge"] as? String,
          challenge.utf8.count == 48,
          challenge.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }),
          let draftDigest = record["owner_request_sha256"] as? String,
          matchesPhysicalPath(draftPath, draftPath),
          digest(URL(fileURLWithPath: draftPath), maximum: 1_048_576) == draftDigest else {
        refuse(6, "Exact launch request custody is unavailable")
    }
    coldChallenge = challenge
    fenceDigest = nil
} else {
    guard matchesPhysicalPath(fencePath, fencePath),
          let expected = record["fence_sha256"] as? String else {
        refuse(6, "Exact launch request custody is unavailable")
    }
    coldChallenge = nil
    fenceDigest = expected
}
let dispatchDeadline: Double?
if arguments.count >= 10 {
    guard let deadline = Double(arguments[9]), deadline.isFinite,
          let sealedDeadline = record["dispatch_before"] as? Double,
          sealedDeadline == deadline else {
        refuse(6, "Exact launch deadline custody is unavailable")
    }
    dispatchDeadline = deadline
} else {
    guard record["dispatch_before"] == nil else {
        refuse(6, "The sealed launch deadline is missing from the invocation")
    }
    dispatchDeadline = nil
}

let workspace = NSWorkspace.shared
func hasCounterpart() -> Bool {
    return workspace.runningApplications.contains(where: {
        !$0.isTerminated && ($0.bundleIdentifier == identifier ||
            matchesPhysicalFileURL($0.bundleURL, path))
    })
}
if hasCounterpart() {
    refuse(2, "An application counterpart is already running")
}

let configuration = NSWorkspace.OpenConfiguration()
configuration.createsNewApplicationInstance = false
configuration.allowsRunningApplicationSubstitution = false
configuration.activates = false
configuration.addsToRecentItems = false
configuration.promptsUserIfNeeded = false

if let coldChallenge {
    configuration.environment = ["KIT_FUSION_OWNER_COLD_START": coldChallenge]
    guard coldEndpointIsEmpty(root), digest(request, maximum: 1_048_576) == arguments[8] else {
        refuse(7, "The initial application endpoint changed before launch")
    }
    if hasCounterpart() {
        refuse(2, "An application counterpart is already running")
    }
} else if digest(fence, maximum: 1_048_576) != fenceDigest {
    refuse(7, "The retained restart fence changed before launch")
}
let dispatched = Date().timeIntervalSince1970
if let deadline = dispatchDeadline, dispatched >= deadline {
    refuse(8, "The reviewed launch admission expired before dispatch")
}
workspace.openApplication(at: target, configuration: configuration) { app, error in
    if let error {
        let failure = error as NSError
        refuse(3, "LaunchServices error \(failure.domain):\(failure.code)")
    }
    guard let app, !app.isTerminated,
          app.processIdentifier > 0,
          app.bundleIdentifier == identifier,
          matchesPhysicalFileURL(app.bundleURL, path),
          matchesPhysicalFileURL(app.executableURL, executable) else {
        refuse(3, "LaunchServices did not return the exact requested application")
    }
    let result: [String: Any] = [
        "pid": app.processIdentifier,
        "bundle": path,
        "bundle_identifier": identifier,
        "executable": executable,
        "dispatched_at": dispatched,
    ]
    guard let response = try? JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]) else {
        refuse(3, "LaunchServices result could not be recorded")
    }
    FileHandle.standardOutput.write(response)
    exit(0)
}

_ = Timer.scheduledTimer(withTimeInterval: wait, repeats: false) { _ in
    refuse(4, "LaunchServices response was not observed before the deadline")
}
RunLoop.main.run()
