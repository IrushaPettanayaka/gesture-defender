"""Reproducible Windows executable, optional installer, and portable ZIP build."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--installer', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if not all((root / 'models' / name).is_file() for name in ('face_landmarker.task', 'hand_landmarker.task')):
        raise SystemExit('Run download_models.py before packaging.')
    for script in ('tools/make_icon.py', 'tools/collect_notices.py'):
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True)
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
        '--name', 'GestureDefender', '--collect-all', 'mediapipe',
        '--icon', str(root / 'art/game.ico'), '--version-file', str(root / 'packaging/version.txt'),
        '--add-data', f'{root / "models"};models', '--add-data', f'{root / "notices"};notices',
        '--add-data', f'{root / "THIRD_PARTY_NOTICES.md"};.',
        '--add-data', f'{root / "art"};art', str(root / 'main.py'),
    ], cwd=root, check=True)
    distribution = root / 'dist/GestureDefender'
    for name in ('README.md', 'HANDOFF.md', 'THIRD_PARTY_NOTICES.md', 'ART_ATTRIBUTION.md', 'DEPLOYMENT.md'):
        shutil.copy2(root / name, distribution / name)
    (root / 'release').mkdir(exist_ok=True)
    shutil.make_archive(str(root / 'release/GestureDefender-1.3.0-Windows-x64'), 'zip',
                        root_dir=root / 'dist', base_dir='GestureDefender')
    if args.installer:
        compiler = root / '.tools/innosetup/ISCC.exe'
        executable = str(compiler) if compiler.is_file() else shutil.which('ISCC')
        if not executable:
            raise SystemExit('Install Inno Setup 6.7.3 or put ISCC on PATH; portable ZIP already built.')
        subprocess.run([executable, '/Qp', str(root / 'packaging/installer.iss')], cwd=root, check=True)
    artifacts = sorted((root / 'release').glob('GestureDefender-1.3.0-*'))
    lines = []
    for artifact in artifacts:
        with artifact.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        lines.append(f'{digest}  {artifact.name}')
    (root / 'release/SHA256SUMS-1.3.0.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
