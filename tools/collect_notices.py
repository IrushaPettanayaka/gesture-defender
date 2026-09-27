"""Retain installed dependency license/notice files with the offline distribution."""
import importlib.metadata
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
destination = root / "notices"
destination.mkdir(exist_ok=True)
extra = root / "third_party"
if extra.exists():
    shutil.copytree(extra, destination / "additional", dirs_exist_ok=True)
for distribution in importlib.metadata.distributions():
    name = distribution.metadata.get("Name", "unknown")
    for item in distribution.files or []:
        if any(word in item.name.lower() for word in ("license", "copying", "notice", "lgpl", "gpl")):
            source = Path(distribution.locate_file(item))
            if source.is_file() and source.suffix.lower() not in (".py", ".pyc", ".pyd", ".dll"):
                target = destination / name / str(item).replace("../", "").replace("..\\", "")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    shutil.copy2(python_license, destination / "PYTHON-LICENSE.txt")
