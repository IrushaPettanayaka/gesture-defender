"""Windows release acceptance: archive, isolated install, launch, models, camera.

Refuses to replace an existing registered installation. Camera diagnostics save
metadata only. This checks startup/capture, not human gesture correctness.
"""
import hashlib
import json
from pathlib import Path
import os
import subprocess
import time
import winreg
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
TEST_DIR = (ROOT / 'installer-test').resolve()
VERSION = '1.3.0'


def run(executable, *arguments, timeout=60):
    result = subprocess.run([str(executable), *map(str, arguments)],
                            cwd=os.environ['WINDIR'], timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError(f'{executable.name} returned {result.returncode}: {arguments}')
    return result.returncode


def main():
    ARTIFACTS.mkdir(exist_ok=True)
    report = {'version': VERSION, 'success': False, 'working_directory': os.environ['WINDIR']}
    uninstaller = TEST_DIR / 'unins000.exe'
    install_started = False
    try:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r'Software\Microsoft\Windows\CurrentVersion\Uninstall\GestureDefender.Desktop_is1'):
                raise RuntimeError('An installation is already registered; preserve it and skip this isolated installer test.')
        except FileNotFoundError:
            pass
        if TEST_DIR.parent != ROOT or TEST_DIR.exists():
            raise RuntimeError('Isolated install target must be a new project-local installer-test directory.')
        archive = ROOT / f'release/GestureDefender-{VERSION}-Windows-x64.zip'
        with zipfile.ZipFile(archive) as bundle:
            bad = bundle.testzip()
            if bad:
                raise RuntimeError(f'Archive CRC failure: {bad}')
            for required in ('GestureDefender.exe', '_internal/models/face_landmarker.task',
                             '_internal/models/hand_landmarker.task', '_internal/THIRD_PARTY_NOTICES.md',
                             'ART_ATTRIBUTION.md', '_internal/pygame/freesansbold.ttf'):
                if f'GestureDefender/{required}' not in bundle.namelist():
                    raise RuntimeError(f'Archive missing {required}')
            restricted = {'2377.jpg', '2377.eps', 'License free.txt', 'License premium.txt'}
            if any(Path(name).name in restricted or 'reference-space/' in name for name in bundle.namelist()):
                raise RuntimeError('Reference artwork must not be redistributed in the release.')
            report['restricted_reference_excluded'] = True
            report['archive_entries'] = len(bundle.namelist())
            report['archive_crc_and_required_assets'] = True
        executable = ROOT / 'dist/GestureDefender/GestureDefender.exe'
        report['portable_smoke_exit'] = run(executable, '--keyboard', '--smoke-frames', '120')
        model_report = ARTIFACTS / 'packaged-models-1.3.json'
        report['portable_models_exit'] = run(executable, '--diagnostics', model_report)
        report['portable_models'] = json.loads(model_report.read_text(encoding='utf-8'))
        installer = ROOT / f'release/GestureDefender-{VERSION}-Setup.exe'
        install_started = True
        report['install_exit'] = run(installer, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                                     '/NOICONS', f'/DIR={TEST_DIR}', f'/LOG={ARTIFACTS / "install-1.3.log"}')
        installed_exe = TEST_DIR / 'GestureDefender.exe'
        report['installed_hash_matches'] = hashlib.sha256(installed_exe.read_bytes()).digest() == hashlib.sha256(executable.read_bytes()).digest()
        if not report['installed_hash_matches']:
            raise RuntimeError('Installed executable differs from build.')
        report['installed_smoke_exit'] = run(installed_exe, '--keyboard', '--smoke-frames', '120')
        camera_report = ARTIFACTS / 'installed-camera-1.3.json'
        report['installed_camera_exit'] = run(installed_exe, '--diagnostics', camera_report, '--check-camera')
        report['installed_camera'] = json.loads(camera_report.read_text(encoding='utf-8'))
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
    finally:
        # Only uninstall this exact, verified project-local test target.
        if install_started and TEST_DIR.parent == ROOT and uninstaller.is_file():
            try:
                report['uninstall_exit'] = run(uninstaller, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART')
                deadline = time.monotonic() + 5
                while (TEST_DIR / 'GestureDefender.exe').exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                report['installed_executable_removed'] = not (TEST_DIR / 'GestureDefender.exe').exists()
            except Exception as error:
                report['success'] = False
                report['uninstall_error'] = str(error)
        if 'install_exit' in report:
            report['success'] = report['success'] and report.get('installed_executable_removed', False)
        (ARTIFACTS / 'release-verification-1.3.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
