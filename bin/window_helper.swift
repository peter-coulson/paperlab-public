/// Window helper for finding macOS window IDs by process ID.
///
/// Usage: window_helper <pid> [app_name]
/// Returns: Window ID on stdout, or exits with code 1 if not found.
import Cocoa

let args = CommandLine.arguments
guard args.count >= 2, let targetPid = Int(args[1]) else {
    fputs("Usage: window_helper <pid> [app_name]\n", stderr)
    exit(1)
}
let appName = args.count >= 3 ? args[2] : "paperlab"

let options = CGWindowListOption(arrayLiteral: .optionAll)
guard let windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
    exit(1)
}

// First try exact PID match
for window in windowList {
    if let wPid = window[kCGWindowOwnerPID as String] as? Int,
       let wid = window[kCGWindowNumber as String] as? Int,
       let layer = window[kCGWindowLayer as String] as? Int,
       wPid == targetPid && layer == 0 {
        let bounds = window[kCGWindowBounds as String] as? [String: Any] ?? [:]
        let w = bounds["Width"] as? Int ?? 0
        let h = bounds["Height"] as? Int ?? 0
        if w > 100 && h > 100 {
            print(wid)
            exit(0)
        }
    }
}

// Fallback: find by app name (for macOS desktop apps)
for window in windowList {
    if let name = window[kCGWindowOwnerName as String] as? String,
       let wid = window[kCGWindowNumber as String] as? Int,
       let layer = window[kCGWindowLayer as String] as? Int,
       name.lowercased() == appName.lowercased() && layer == 0 {
        let bounds = window[kCGWindowBounds as String] as? [String: Any] ?? [:]
        let w = bounds["Width"] as? Int ?? 0
        let h = bounds["Height"] as? Int ?? 0
        if w > 100 && h > 100 {
            print(wid)
            exit(0)
        }
    }
}

exit(1)
