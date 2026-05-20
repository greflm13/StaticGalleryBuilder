import sys
from importlib.resources import as_file, files
from pathlib import Path


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).joinpath(*parts)  # type: ignore

    res = files("staticgallerybuilder").joinpath(*parts)

    with as_file(res) as actual_path:
        return actual_path
