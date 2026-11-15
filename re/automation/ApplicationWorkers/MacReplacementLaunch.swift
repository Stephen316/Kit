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

let arguments = CommandLine.arguments
guard arguments.count == 9,
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
let fencePath = (requestPath as NSString).deletingLastPathComponent + "/fence.json"
let request = URL(fileURLWithPath: requestPath)
let fence = URL(fileURLWithPath: fencePath)
guard matchesPhysicalPath(requestPath, requestPath),
      matchesPhysicalPath(fencePath, fencePath),
      let requestData = boundedBytes(request, maximum: 1_048_576),
      digest(requestData) == arguments[8],
      let decoded = try? JSONSerialization.jsonObject(with: requestData),
      let record = decoded as? [String: Any],
      let fenceDigest = record["fence_sha256"] as? String else {
    refuse(6, "Exact launch request custody is unavailable")
}

let workspace = NSWorkspace.shared
if workspace.runningApplications.contains(where: {
    !$0.isTerminated && ($0.bundleIdentifier == identifier ||
        matchesPhysicalFileURL($0.bundleURL, path))
}) {
    refuse(2, "An application counterpart is already running")
}

let configuration = NSWorkspace.OpenConfiguration()
configuration.createsNewApplicationInstance = false
configuration.allowsRunningApplicationSubstitution = false
configuration.activates = false
configuration.addsToRecentItems = false
configuration.promptsUserIfNeeded = false

guard digest(fence, maximum: 1_048_576) == fenceDigest else {
    refuse(7, "The retained restart fence changed before launch")
}
let dispatched = Date().timeIntervalSince1970
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
