// Single-file Windows launcher for the SWGB-in-AoE2-DE installer.
//
// The installer ZIP (scripts, recipe, vgmstream, project-authored payload; no game
// media) is embedded as a resource. The launcher checks its SHA-256, extracts it to
// a temporary folder, runs installer\Install-SWGB-DE.ps1 with Windows PowerShell in
// this console window, passes every argument through and returns the script's exit
// code. Built by outputs/toolkit/build_installer_exe.py with the .NET Framework csc.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

namespace SwgbDeSetup
{
    internal static class Program
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint GetConsoleProcessList(uint[] processList, uint processCount);

        private static bool OwnsConsole()
        {
            // 1 process attached = the console was created for us (double-click from Explorer).
            try { return GetConsoleProcessList(new uint[16], 16) <= 1; } catch { return false; }
        }

        private static void Say(string text, ConsoleColor color = ConsoleColor.Gray)
        {
            ConsoleColor old = Console.ForegroundColor;
            Console.ForegroundColor = color;
            Console.WriteLine(text);
            Console.ForegroundColor = old;
        }

        private static int Main(string[] args)
        {
            bool interactive = OwnsConsole() && !Console.IsInputRedirected && !Console.IsOutputRedirected;
            int rc = Run(args, interactive);
            if (interactive)
            {
                Console.WriteLine();
                Console.Write("Press any key to close this window . . .");
                try { Console.ReadKey(true); } catch { }
            }
            return rc;
        }

        private static string Quote(string arg)
        {
            if (arg.Length > 0 && arg.IndexOfAny(new[] { ' ', '\t', '"' }) < 0) return arg;
            var sb = new StringBuilder("\"");
            int slashes = 0;
            foreach (char c in arg)
            {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') sb.Append('\\', slashes * 2 + 1);
                else sb.Append('\\', slashes);
                slashes = 0;
                sb.Append(c);
            }
            sb.Append('\\', slashes * 2);
            return sb.Append('"').ToString();
        }

        private static int Run(string[] args, bool interactive)
        {
            Console.Title = "SWGB in Age of Empires II: DE - installer " + BuildInfo.Version;
            Say("SWGB in Age of Empires II: DE - installer " + BuildInfo.Version + " (build " + BuildInfo.Commit.Substring(0, 7) + ")", ConsoleColor.Cyan);

            if (args.Any(a => a == "/?" || a == "-?" || a == "-h" || a == "--help" || a == "-Help"))
            {
                Console.WriteLine();
                Console.WriteLine("Usage: " + Path.GetFileName(Process.GetCurrentProcess().MainModule.FileName) + " [options]");
                Console.WriteLine("  (no options)        Install or update; asks Install / Repair / Uninstall when double-clicked");
                Console.WriteLine("  -Repair             Only fix mod-status.json: enable SWBG-Data again and fix stale entries");
                Console.WriteLine("                      (after a crash or an update of mod 549437); no regeneration");
                Console.WriteLine("  -Uninstall          Remove the SWBG mods and restore anything the installer backed up");
                Console.WriteLine("  -SwgbPath <folder>  Star Wars Galactic Battlegrounds Saga folder, if not found automatically");
                Console.WriteLine("  -DePath <folder>    Age of Empires II: DE folder, if not found automatically");
                Console.WriteLine("  -ProfileId <id>     DE profile to install into");
                Console.WriteLine("  -NoEnable           Do not edit DE's mod-status.json");
                Console.WriteLine("  -Yes                No prompts (uses the most recently used profile)");
                Console.WriteLine("  -ExtractTo <folder> Only extract the installer files (scripts + payload) and exit");
                return 0;
            }

            string extractTo = null;
            var pass = new System.Collections.Generic.List<string>();
            for (int i = 0; i < args.Length; i++)
            {
                if (string.Equals(args[i], "-ExtractTo", StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length) { extractTo = args[++i]; continue; }
                pass.Add(args[i]);
            }

            if (extractTo == null && interactive && pass.Count == 0)
            {
                Console.WriteLine();
                Console.WriteLine("  [I] Install or update (default)");
                Console.WriteLine("  [R] Repair: enable SWBG-Data again and fix stale mod entries (after a crash or");
                Console.WriteLine("      an update of mod 549437); close DE first");
                Console.WriteLine("  [U] Uninstall");
                Console.WriteLine("  [Q] Quit");
                Console.Write("Choose I, R, U or Q: ");
                ConsoleKeyInfo key = Console.ReadKey(true);
                Console.WriteLine(key.KeyChar);
                char k = char.ToUpperInvariant(key.KeyChar);
                if (k == 'Q' || key.Key == ConsoleKey.Escape) return 0;
                if (k == 'U') pass.Add("-Uninstall");
                if (k == 'R') pass.Add("-Repair");
            }

            byte[] zip;
            using (Stream s = typeof(Program).Assembly.GetManifestResourceStream("payload.zip"))
            {
                if (s == null) { Say("This installer is damaged (embedded files missing). Download it again.", ConsoleColor.Red); return 2; }
                zip = new byte[s.Length];
                int off = 0;
                while (off < zip.Length) { int n = s.Read(zip, off, zip.Length - off); if (n <= 0) break; off += n; }
            }
            string digest;
            using (var sha = SHA256.Create()) digest = BitConverter.ToString(sha.ComputeHash(zip)).Replace("-", "").ToLowerInvariant();
            if (digest != BuildInfo.PayloadSha256)
            {
                Say("This installer is damaged (checksum mismatch). Download it again.", ConsoleColor.Red);
                return 2;
            }

            bool temporary = extractTo == null;
            string dir = temporary
                ? Path.Combine(Path.GetTempPath(), "SWGB-DE-Installer-" + BuildInfo.Commit.Substring(0, 7) + "-" + Guid.NewGuid().ToString("N").Substring(0, 8))
                : Path.GetFullPath(extractTo);
            try
            {
                Directory.CreateDirectory(dir);
                string root = Path.GetFullPath(dir).TrimEnd('\\') + "\\";
                string prefix = BuildInfo.PackageName + "/";
                using (var archive = new ZipArchive(new MemoryStream(zip), ZipArchiveMode.Read))
                {
                    foreach (ZipArchiveEntry e in archive.Entries)
                    {
                        string rel = e.FullName.StartsWith(prefix) ? e.FullName.Substring(prefix.Length) : e.FullName;
                        if (rel.Length == 0) continue;
                        string target = Path.GetFullPath(Path.Combine(root, rel.Replace('/', '\\')));
                        if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Bad path in payload: " + e.FullName);
                        if (rel.EndsWith("/")) { Directory.CreateDirectory(target); continue; }
                        Directory.CreateDirectory(Path.GetDirectoryName(target));
                        e.ExtractToFile(target, true);
                    }
                }
                if (!temporary)
                {
                    Say("Extracted the installer files to " + dir + ". Run Install-SWGB-DE.cmd there.", ConsoleColor.Green);
                    return 0;
                }

                string script = Path.Combine(dir, "installer", "Install-SWGB-DE.ps1");
                string ps = Path.Combine(Environment.SystemDirectory, "WindowsPowerShell", "v1.0", "powershell.exe");
                if (!File.Exists(ps)) ps = "powershell.exe";
                var psi = new ProcessStartInfo(ps)
                {
                    Arguments = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(script) + " " + string.Join(" ", pass.Select(Quote)),
                    UseShellExecute = false,
                    WorkingDirectory = dir,
                };
                psi.EnvironmentVariables["SWGB_DE_LAUNCHER"] = Path.GetFileName(Process.GetCurrentProcess().MainModule.FileName);
                // Ctrl+C goes to PowerShell too; keep the launcher alive so it can clean up and report.
                Console.CancelKeyPress += (o, e) => { e.Cancel = true; };
                using (Process p = Process.Start(psi))
                {
                    p.WaitForExit();
                    int rc = p.ExitCode;
                    Console.WriteLine();
                    if (rc == 0) Say("Finished (exit code 0).", ConsoleColor.Green);
                    else Say("The installer stopped with exit code " + rc + ". Logs: " + Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SWGB-DE-Installer", "logs"), ConsoleColor.Red);
                    return rc;
                }
            }
            catch (Exception ex)
            {
                Say("Installer launcher error: " + ex.Message, ConsoleColor.Red);
                return 3;
            }
            finally
            {
                if (temporary)
                {
                    try { if (Directory.Exists(dir)) Directory.Delete(dir, true); } catch { }
                }
            }
        }
    }
}
