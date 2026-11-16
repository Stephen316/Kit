// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed partial class SolidWorksCapture
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    static extern uint GetFinalPathNameByHandleW(SafeFileHandle file, StringBuilder path, uint capacity, uint flags);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern SafeProcessHandle OpenProcess(uint access, bool inherit, int pid);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetProcessTimes(SafeProcessHandle handle, out long created, out long exited,
        out long kernel, out long user);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern uint WaitForSingleObject(SafeProcessHandle handle, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetExitCodeProcess(SafeProcessHandle handle, out uint exitCode);

    // The checked path is the file Windows actually resolves through any path aliases.
    static string ResolveTwoPadImage(string path)
    {
        using (var file = File.Open(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        {
            var resolved = new StringBuilder(32768);
            uint length = GetFinalPathNameByHandleW(file.SafeFileHandle, resolved, (uint)resolved.Capacity, 0);
            if (length == 0) throw new Win32Exception(Marshal.GetLastWin32Error());
            Check(length < resolved.Capacity, "The resolved SOLIDWORKS image exceeds the Windows path limit");
            return resolved.ToString();
        }
    }

    // Each receipt is immutable and survives a subsequent close or shutdown failure.
    static string SealTwoPad(string path, Dictionary<string, object> evidence)
    {
        using (var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
        {
            var bytes = Encoding.UTF8.GetBytes(Json.Serialize(evidence) + "\n");
            file.Write(bytes, 0, bytes.Length);
            file.Flush(true);
        }
        return Hash(path);
    }

    static int[] TwoPadProcessIds()
    {
        return Process.GetProcessesByName("SLDWORKS").Select(process =>
        {
            using (process) return process.Id;
        }).ToArray();
    }

    // A retained native handle proves exit for the same COM process we measured.
    static SafeProcessHandle OpenTwoPadLifetime(Process process, long creation)
    {
        var handle = OpenProcess(0x00101000, false, process.Id);
        try
        {
            if (handle.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            long actual, exit, kernel, user;
            if (!GetProcessTimes(handle, out actual, out exit, out kernel, out user))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            Check(actual == creation && WaitForSingleObject(handle, 0) == 0x102,
                "The retained handle does not identify the live COM process");
            return handle;
        }
        catch
        {
            handle.Dispose();
            throw;
        }
    }

    // Observe the retained handle even if COM disconnected during shutdown.
    static void ExitTwoPad(ISldWorks application, SafeProcessHandle handle, Dictionary<string, object> exit)
    {
        Exception error = null;
        try
        {
            uint state = WaitForSingleObject(handle, 0);
            if (state == 0x102)
            {
                Check(application.GetDocumentCount() == 0, "The owned SOLIDWORKS process still has open documents");
                application.ExitApp();
            }
            else Check(state == 0, "Could not inspect the owned SOLIDWORKS process");
        }
        catch (Exception exception) { error = exception; }
        finally
        {
            Marshal.FinalReleaseComObject(application);
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }
        uint completed = WaitForSingleObject(handle, error == null ? 60000u : 0u);
        if (completed == 0)
        {
            exit["exited_observed"] = true;
            uint code;
            if (!GetExitCodeProcess(handle, out code)) throw new Win32Exception(Marshal.GetLastWin32Error());
            exit["exit_code"] = unchecked((int)code);
            exit["exit_hex"] = "0x" + code.ToString("X8", CultureInfo.InvariantCulture);
        }
        if (error != null) throw new InvalidOperationException("Owned SOLIDWORKS shutdown failed: " + error.Message, error);
        Check(completed == 0, "The owned SOLIDWORKS process did not exit");
    }

    // Keep discovery and exit separate so an abnormal shutdown cannot hide completed measurements.
    static string WithTwoPadCom(string executable, string output, string phase,
        Func<ISldWorks, Dictionary<string, object>, Dictionary<string, object>> collect)
    {
        Check(TwoPadProcessIds().Length == 0, "Use an isolated desktop with SOLIDWORKS stopped");
        var expectedPath = ResolveTwoPadImage(executable);
        var expectedHash = Hash(executable);
        int session;
        using (var caller = Process.GetCurrentProcess()) session = caller.SessionId;
        var requested = DateTime.UtcNow;
        var application = (ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application", true));
        SafeProcessHandle handle = null;
        bool owned = false;
        try
        {
            using (var process = Process.GetProcessById(application.GetProcessID()))
            {
                var started = process.StartTime.ToUniversalTime();
                var module = process.MainModule;
                var creation = started.ToFileTimeUtc();
                var runningPath = ResolveTwoPadImage(module.FileName);
                Check(process.SessionId == session && started >= requested
                    && TwoPadProcessIds().SequenceEqual(new[] { process.Id })
                    && String.Equals(expectedPath, runningPath, StringComparison.OrdinalIgnoreCase)
                    && Hash(module.FileName) == expectedHash,
                    "COM did not activate the unique fresh process for the registered SOLIDWORKS image");
                handle = OpenTwoPadLifetime(process, creation);
                Check(application.GetDocumentCount() == 0 && application.RevisionNumber() == "34.4.1"
                    && module.FileVersionInfo.FileVersion == "34.4.1.1011",
                    "The expected licensed SOLIDWORKS build did not start empty");
                owned = true;
                var row = Row("phase", phase, "pid", process.Id, "session_id", session,
                    "started_utc", started.ToString("O"), "created_filetime", creation.ToString(CultureInfo.InvariantCulture),
                    "resolved_executable", runningPath, "executable_sha256", expectedHash,
                    "application_build", module.FileVersionInfo.FileVersion, "initial_documents", 0);
                var exit = Row("phase", phase, "pid", process.Id, "exited_observed", false);
                Dictionary<string, object> result;
                try
                {
                    var ownerHash = SealTwoPad(Path.Combine(output, phase + "-owner.json"), row);
                    row["owner_sha256"] = ownerHash;
                    exit["owner_sha256"] = ownerHash;
                    result = collect(application, row);
                    var measurements = SealTwoPad(Path.Combine(output, phase + "-measurements.json"), result);
                    row["measurements_sha256"] = measurements;
                    exit["measurements_sha256"] = measurements;
                }
                finally
                {
                    try
                    {
                        ExitTwoPad(application, handle, exit);
                    }
                    catch (Exception exception)
                    {
                        exit["cleanup_type"] = exception.GetType().Name;
                        exit["cleanup_message"] = exception.Message;
                        throw;
                    }
                    finally
                    {
                        row["exit_receipt_sha256"] = SealTwoPad(Path.Combine(output, phase + "-exit.json"), exit);
                    }
                }
                row["exited_observed"] = (bool)exit["exited_observed"];
                row["exit_code"] = (int)exit["exit_code"];
                Check((int)row["exit_code"] == 0, "The owned SOLIDWORKS process exited with " + exit["exit_hex"]);
                return Json.Serialize(result);
            }
        }
        finally
        {
            if (!owned) Marshal.FinalReleaseComObject(application);
            if (handle != null) handle.Dispose();
        }
    }

    // Measure the same stock bytes from an isolated path and leave the original immutable.
    Dictionary<string, object> TwoPadStock(string phase, string position)
    {
        Check(app.GetDocumentCount() == 0, "Stock measurement requires an empty owned process");
        var original = Path.Combine(repo, "re", "solidworks", "examples", ".SLDPRT", "example.SLDPRT");
        var hash = Hash(original);
        var copy = Path.Combine(output, phase + "-" + position + "-stock.SLDPRT");
        File.Copy(original, copy, false);
        Check(Hash(copy) == hash, "Private stock control differs from the selected archive");
        object status;
        var document = Open(copy, out status, true);
        Dictionary<string, object> row;
        try
        {
            Check(document.IsOpenedReadOnly() && app.GetDocumentCount() == 1
                && String.Equals(document.GetPathName(), copy, StringComparison.OrdinalIgnoreCase),
                "SOLIDWORKS did not open the exact private stock control read-only");
            Rebuild(document);
            row = Measure(document, position + " " + phase, false);
            Check((int)row["body_count"] > 0 && (double)row["volume_mm3"] > 0, "Unhealthy stock control");
            row["native_sha256"] = hash;
            row["open_status"] = status;
            row["private_stock_file"] = Path.GetFileName(copy);
            SealTwoPad(Path.Combine(output, phase + "-" + position + "-stock-measured.json"), row);
        }
        finally
        {
            Close(document);
            Check(app.GetDocumentCount() == 0, "Closing the private stock control left an open document");
        }
        Check(Hash(original) == hash && Hash(copy) == hash, "Stock control bytes changed during measurement");
        row["closed_read_only"] = true;
        return row;
    }
}
