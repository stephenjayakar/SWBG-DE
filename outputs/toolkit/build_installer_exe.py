"""Build the single-file Windows installer: <out>/SWGB-DE-Installer-<ver>-<label>.exe.

Embeds the verified installer ZIP from package_installer.py into the C# launcher
outputs/installer/exe/SwgbDeSetup.cs, compiled with the .NET Framework 4 csc.exe
that ships with Windows (also present on GitHub's windows-latest runners). The launcher extracts the ZIP to %TEMP%, runs
installer\\Install-SWGB-DE.ps1 in its console, passes arguments through and
returns the exit code. The icon is made from the SWBG-Logic Galactic Empire civ
emblem (part of the payload). No game media is added.

Normally called by package_installer.py. To rebuild only the exe:
    python outputs/toolkit/build_installer_exe.py [--build <commit>] [--label <name>] [--out DIR]
"""
from pathlib import Path
import argparse, hashlib, io, json, os, shutil, subprocess, tempfile, zipfile

ROOT = Path(__file__).resolve().parents[2]
from package_installer import VERSION
CSC = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
EMBLEM = 'payload/SWBG-Logic/resources/_common/wpfg/resources/civ_emblems/galacticempire.png'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_icon(png_bytes, dest):
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    side = max(img.size)
    square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    square = square.resize((256, 256), Image.LANCZOS)
    square.save(dest, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def build(commit, out=None, label=None):
    label = label or commit[:7]
    name = f'SWGB-DE-Installer-{VERSION}-{label}'
    releases = Path(out) if out else ROOT / 'outputs/releases'
    zpath = releases / (name + '.zip')
    exe = releases / (name + '.exe')
    assert zpath.is_file(), f'Run package_installer.py --build {commit[:7]} --label {label} first: {zpath}'
    assert not exe.exists(), f'Installer exe already exists: {exe}'
    zdata = zpath.read_bytes()
    zsha = sha(zdata)
    recorded = (releases / (name + '.zip.sha256')).read_text().split()[0]
    assert recorded == zsha, 'Installer ZIP does not match its .sha256'
    with zipfile.ZipFile(io.BytesIO(zdata)) as z:
        assert z.testzip() is None
        build_json = json.loads(z.read(f'{name}/BUILD.json'))
        assert build_json['commit'] == commit, (build_json['commit'], commit)
        emblem = z.read(f'{name}/{EMBLEM}')
        members = {n[len(name) + 1:]: z.read(n) for n in z.namelist() if not n.endswith('/')}

    work = ROOT / 'work/installer-exe' / label
    if work.exists():
        assert work.resolve().is_relative_to((ROOT / 'work').resolve())
        shutil.rmtree(work)
    work.mkdir(parents=True)
    icon = work / 'swgb-de.ico'
    make_icon(emblem, icon)
    info = work / 'BuildInfo.cs'
    info.write_text(f'''using System.Reflection;
[assembly: AssemblyTitle("SWGB in Age of Empires II: DE - installer")]
[assembly: AssemblyProduct("SWGB in Age of Empires II: DE")]
[assembly: AssemblyDescription("Builds the SWGB-DE mods from your own SWGB Saga + Expanding Fronts install")]
[assembly: AssemblyCompany("Stephen Jayakar")]
[assembly: AssemblyVersion("{VERSION.split('-')[0]}.0")]
[assembly: AssemblyFileVersion("{VERSION.split('-')[0]}.0")]
[assembly: AssemblyInformationalVersion("{VERSION}+{label}")]
namespace SwgbDeSetup {{
    internal static class BuildInfo {{
        public const string Version = "{VERSION}";
        public const string Commit = "{commit}";
        public const string PackageName = "{name}";
        public const string PayloadSha256 = "{zsha}";
    }}
}}
''', encoding='utf-8')
    fw = CSC.parent
    out = work / (name + '.exe')
    cmd = [str(CSC), '/nologo', '/target:exe', '/platform:anycpu', '/optimize+', '/utf8output',
           f'/out:{out}', f'/win32icon:{icon}', f'/resource:{zpath},payload.zip',
           f'/r:{fw / "System.IO.Compression.dll"}', f'/r:{fw / "System.IO.Compression.FileSystem.dll"}',
           str(ROOT / 'outputs/installer/exe/SwgbDeSetup.cs'), str(info)]
    subprocess.run(cmd, check=True)

    # Self-test: help exits 0 and -ExtractTo reproduces every ZIP member byte for byte.
    subprocess.run([str(out), '-?'], check=True, stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(dir=work) as tmp:
        subprocess.run([str(out), '-ExtractTo', tmp], check=True, stdout=subprocess.DEVNULL)
        got = {p.relative_to(tmp).as_posix(): p.read_bytes() for p in Path(tmp).rglob('*') if p.is_file()}
        assert got.keys() == members.keys(), sorted(set(got) ^ set(members))[:10]
        assert all(got[k] == v for k, v in members.items())

    shutil.copyfile(out, exe)
    digest = sha(exe.read_bytes())
    exe.with_suffix('.exe.sha256').write_text(f'{digest}  {exe.name}\n', newline='\n')
    return dict(exe=str(exe), bytes=exe.stat().st_size, sha256=digest, payload_zip_sha256=zsha,
                payload_files=len(members), commit=commit)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build', default='HEAD', help='Git commit the installer ZIP was packaged from')
    p.add_argument('--label', help='Build label used by package_installer.py (default: short commit hash)')
    p.add_argument('--out', type=Path, default=ROOT / 'outputs/releases', help='Folder holding the installer ZIP')
    args = p.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', args.build], text=True, cwd=ROOT).strip()
    print(json.dumps(build(commit, out=args.out, label=args.label)))


if __name__ == '__main__':
    main()
