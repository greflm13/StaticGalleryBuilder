#!/usr/bin/env python3
import os
import argparse
import urllib.parse
import shutil
import fnmatch
import json
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from jinja2 import Environment, FileSystemLoader
from tqdm.auto import tqdm
from PIL import Image, ImageOps, ExifTags
from rich_argparse import RichHelpFormatter, HelpPreviewAction

try:
    import cairosvg
    from io import BytesIO

    SVGSUPPORT = True
except ImportError:
    SVGSUPPORT = False

import cclicense

# fmt: off
# Constants
STATIC_FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
FAVICON_PATH = ".static/favicon.ico"
GLOBAL_CSS_PATH = ".static/global.css"
DEFAULT_THEME_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "themes", "default.css")
DEFAULT_AUTHOR = "Author"
VERSION = "1.9.13"
RAW_EXTENSIONS = [".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr", ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"]
IMG_EXTENSIONS = [".jpg", ".jpeg"]
EXCLUDES = [".lock", "index.html", "manifest.json", ".sizelist.json", ".thumbnails", ".static"]
NOT_LIST = ["*/Galleries/*", "Archives"]
ICON_SIZES = ["36x36", "48x48", "72x72", "96x96", "144x144", "192x192", "512x512"]
# fmt: on

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")))
thumbnails: List[Tuple[str, str]] = []
info: Dict[str, str] = {}
pbardict: Dict[str, tqdm] = {}


class Icon:
    src: str
    type: str
    sizes: str
    purpose: str


class Args:
    author_name: str
    exclude_folders: List[str]
    file_extensions: List[str]
    generate_webmanifest: bool
    ignore_other_files: bool
    license_type: Optional[str]
    non_interactive_mode: bool
    regenerate_thumbnails: bool
    root_directory: str
    site_title: str
    theme_path: str
    use_fancy_folders: bool
    web_root_url: str


# fmt: off
def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(description="Generate HTML files for a static image hosting website.", formatter_class=RichHelpFormatter)
    parser.add_argument("--exclude-folder", help="Folders to exclude from processing, globs supported (can be specified multiple times).", action="append", dest="exclude_folders", metavar="FOLDER")
    parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg")
    parser.add_argument("--ignore-other-files", help="Ignore files that do not match the specified extensions.", action="store_true", default=False, dest="ignore_other_files")
    parser.add_argument("--theme-path", help="Path to the CSS theme file.", default=DEFAULT_THEME_PATH, type=str, dest="theme_path", metavar="PATH")
    parser.add_argument("--use-fancy-folders", help="Enable fancy folder view instead of the default Apache directory listing.", action="store_true", default=False, dest="use_fancy_folders")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-a", "--author-name", help="Name of the author of the images.", default=DEFAULT_AUTHOR, type=str, dest="author_name", metavar="AUTHOR")
    parser.add_argument("-e", "--file-extensions", help="File extensions to include (can be specified multiple times).", action="append", dest="file_extensions", metavar="EXTENSION")
    parser.add_argument("-l", "--license-type", help="Specify the license type for the images.", choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], default=None, dest="license_type", metavar="LICENSE")
    parser.add_argument("-m", "--web-manifest", help="Generate a web manifest file.", action="store_true", default=False, dest="generate_webmanifest")
    parser.add_argument("-n", "--non-interactive-mode", help="Run in non-interactive mode, disabling progress bars.", action="store_true", default=False, dest="non_interactive_mode")
    parser.add_argument("-p", "--root-directory", help="Root directory containing the images.", required=True, type=str, dest="root_directory", metavar="ROOT")
    parser.add_argument("-r", "--regenerate-thumbnails", help="Regenerate thumbnails even if they already exist.", action="store_true", default=False, dest="regenerate_thumbnails")
    parser.add_argument("-t", "--site-title", help="Title of the image hosting site.", required=True, type=str, dest="site_title", metavar="TITLE")
    parser.add_argument("-w", "--web-root-url", help="Base URL of the web root for the image hosting site.", required=True, type=str, dest="web_root_url", metavar="URL")
    parsed_args = parser.parse_args()
    _args = Args()
    _args.author_name = parsed_args.author_name
    _args.exclude_folders = parsed_args.exclude_folders
    _args.file_extensions = parsed_args.file_extensions
    _args.generate_webmanifest = parsed_args.generate_webmanifest
    _args.ignore_other_files = parsed_args.ignore_other_files
    _args.license_type = parsed_args.license_type
    _args.non_interactive_mode = parsed_args.non_interactive_mode
    _args.regenerate_thumbnails = parsed_args.regenerate_thumbnails
    _args.root_directory = parsed_args.root_directory
    _args.site_title = parsed_args.site_title
    _args.theme_path = parsed_args.theme_path
    _args.use_fancy_folders = parsed_args.use_fancy_folders
    _args.web_root_url = parsed_args.web_root_url
    return _args
# fmt: on


def init_globals(_args: Args, raw: list[str]) -> Args:
    if not _args.file_extensions:
        _args.file_extensions = IMG_EXTENSIONS
    if not _args.exclude_folders:
        _args.exclude_folders = NOT_LIST
    _args.root_directory = _args.root_directory.rstrip("/") + "/"
    _args.web_root_url = _args.web_root_url.rstrip("/") + "/"

    raw = [ext.lower() for ext in raw] + [ext.upper() for ext in raw]

    return _args, raw


def copy_static_files(_args: Args) -> None:
    if os.path.exists(os.path.join(_args.root_directory, ".static")):
        print("Removing existing .static folder...")
        shutil.rmtree(os.path.join(_args.root_directory, ".static"))
    if not os.path.exists(os.path.join(_args.root_directory, ".static")):
        print("Copying static files...")
        shutil.copytree(STATIC_FILES_DIR, os.path.join(_args.root_directory, ".static"), dirs_exist_ok=True)
        shutil.copyfile(_args.theme_path, os.path.join(_args.root_directory, ".static", "theme.css"))


def webmanifest(_args: Args) -> None:
    icons: List[Icon] = []
    files = os.listdir(os.path.join(STATIC_FILES_DIR, "icons"))
    if SVGSUPPORT and any(file.endswith(".svg") for file in files):
        svg = [file for file in files if file.endswith(".svg")][0]
        icons.append(
            {"src": f"{_args.web_root_url}.static/icons/{svg}", "type": "image/svg+xml", "sizes": "512x512", "purpose": "maskable"}
        )
        icons.append({"src": f"{_args.web_root_url}.static/icons/{svg}", "type": "image/svg+xml", "sizes": "512x512", "purpose": "any"})
        for size in ICON_SIZES:
            tmpimg = BytesIO()
            sizes = size.split("x")
            iconpath = os.path.join(_args.root_directory, ".static", "icons", os.path.splitext(svg)[0] + "-" + size + ".png")
            cairosvg.svg2png(
                url=os.path.join(STATIC_FILES_DIR, "icons", svg),
                write_to=tmpimg,
                output_width=int(sizes[0]),
                output_height=int(sizes[1]),
                scale=1,
            )
            with Image.open(tmpimg) as iconfile:
                iconfile.save(iconpath, format="PNG")
            icons.append(
                {
                    "src": f"{_args.web_root_url}.static/icons/{os.path.splitext(svg)[0]}-{size}.png",
                    "sizes": size,
                    "type": "image/png",
                    "purpose": "maskable",
                }
            )
            icons.append(
                {
                    "src": f"{_args.web_root_url}.static/icons/{os.path.splitext(svg)[0]}-{size}.png",
                    "sizes": size,
                    "type": "image/png",
                    "purpose": "any",
                }
            )
    else:
        for icon in os.listdir(os.path.join(STATIC_FILES_DIR, "icons")):
            if not icon.endswith(".png"):
                continue
            with Image.open(os.path.join(STATIC_FILES_DIR, "icons", icon)) as iconfile:
                iconsize = f"{iconfile.size[0]}x{iconfile.size[1]}"
            icons.append(
                {"src": f"{_args.web_root_url}.static/icons/{icon}", "sizes": iconsize, "type": "image/png", "purpose": "maskable"}
            )
            icons.append({"src": f"{_args.web_root_url}.static/icons/{icon}", "sizes": iconsize, "type": "image/png", "purpose": "any"})
        if len(icons) == 0:
            print("No icons found in the static/icons folder!")
            return

    with open(os.path.join(_args.root_directory, ".static", "theme.css"), "r", encoding="utf-8") as f:
        content = f.read()
    background_color = (
        content.replace("body{", "body {").split("body {")[1].split("}")[0].split("background-color:")[1].split(";")[0].strip()
    )
    theme_color = (
        content.replace(".navbar{", "navbar {").split(".navbar {")[1].split("}")[0].split("background-color:")[1].split(";")[0].strip()
    )
    with open(os.path.join(_args.root_directory, ".static", "manifest.json"), "w", encoding="utf-8") as f:
        manifest = env.get_template("manifest.json.j2")
        content = manifest.render(
            name=_args.web_root_url.replace("https://", "").replace("http://", "").replace("/", ""),
            short_name=_args.site_title,
            icons=icons,
            background_color=background_color,
            theme_color=theme_color,
        )
        f.write(content)


def generate_thumbnail(arguments: Tuple[str, str, str, bool]) -> None:
    folder, item, root_directory, regenerate_thumbnails = arguments
    path = os.path.join(root_directory, ".thumbnails", folder.removeprefix(root_directory), os.path.splitext(item)[0]) + ".jpg"
    if not os.path.exists(path) or regenerate_thumbnails:
        if os.path.exists(path):
            os.remove(path)
        try:
            with Image.open(os.path.join(folder, item)) as imgfile:
                img = ImageOps.exif_transpose(imgfile)
                img.thumbnail((512, 512))
                img.save(path, "JPEG", quality=75, optimize=True)
        except OSError:
            print(f"Failed to generate thumbnail for {os.path.join(folder, item)}")


def get_total_folders(folder: str, _args: Args, _total: int = 0) -> int:

    _total += 1

    pbardict["traversingbar"].desc = f"Traversing filesystem - {folder}"
    pbardict["traversingbar"].update(1)

    items = os.listdir(folder)
    items.sort()
    for item in items:
        if item not in EXCLUDES:
            if os.path.isdir(os.path.join(folder, item)):
                if item not in _args.exclude_folders:
                    skip = False
                    for exclude in _args.exclude_folders:
                        if fnmatch.fnmatchcase(os.path.join(folder, item), exclude):
                            skip = True
                    if not skip:
                        _total = get_total_folders(os.path.join(folder, item), _args, _total)
    return _total


def list_folder(folder: str, title: str, _args: Args, raw: list[str]) -> None:
    sizelist: Dict[Dict[str, int], Dict[str, int]] = {}
    if not os.path.exists(os.path.join(folder, ".sizelist.json")):
        sizelistfile = open(os.path.join(folder, ".sizelist.json"), "x", encoding="utf-8")
        sizelistfile.write("{}")
        sizelistfile.close()
    with open(os.path.join(folder, ".sizelist.json"), "r+", encoding="utf-8") as sizelistfile:
        sizelist = json.loads(sizelistfile.read())
        items = os.listdir(folder)
        items.sort()
        images: List[Dict[str, Any]] = []
        subfolders: List[Dict[str, str]] = []
        foldername = folder.removeprefix(_args.root_directory)
        foldername = f"{foldername}/" if foldername else ""
        baseurl = urllib.parse.quote(foldername)
        if not os.path.exists(os.path.join(_args.root_directory, ".thumbnails", foldername)):
            os.mkdir(os.path.join(_args.root_directory, ".thumbnails", foldername))
        contains_files = False
        if not _args.non_interactive_mode:
            pbardict[folder] = tqdm(total=len(items), desc=f"Getting image infos - {folder}", unit="files", ascii=True, dynamic_ncols=True)
        for item in items:
            if item not in EXCLUDES:
                if os.path.isdir(os.path.join(folder, item)):
                    subfolder = {"url": f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}", "name": item}
                    subfolders.append(subfolder)
                    if item not in _args.exclude_folders:
                        skip = False
                        for exclude in _args.exclude_folders:
                            if fnmatch.fnmatchcase(os.path.join(folder, item), exclude):
                                skip = True
                        if not skip:
                            list_folder(
                                os.path.join(folder, item), os.path.join(folder, item).removeprefix(_args.root_directory), _args, raw
                            )
                else:
                    extsplit = os.path.splitext(item)
                    contains_files = True
                    if extsplit[1].lower() in _args.file_extensions:
                        if not sizelist.get(item) or _args.regenerate_thumbnails:
                            exifdata = {}
                            with Image.open(os.path.join(folder, item)) as img:
                                exif = img.getexif()
                                width, height = img.size

                            for key, val in exif.items():
                                if key in ExifTags.TAGS:
                                    exifdata[ExifTags.TAGS[key]] = val
                                else:
                                    exifdata[key] = val
                            if "Orientation" in exifdata and (exifdata["Orientation"] == 6 or exifdata["Orientation"] == 8):
                                sizelist[item] = {"width": height, "height": width}
                            else:
                                sizelist[item] = {"width": width, "height": height}

                        image = {
                            "url": f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}",
                            "thumbnail": f"{_args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(extsplit[0])}.jpg",
                            "name": item,
                            "width": sizelist[item]["width"],
                            "height": sizelist[item]["height"],
                        }
                        if not os.path.exists(os.path.join(_args.root_directory, ".thumbnails", foldername, item)):
                            thumbnails.append((folder, item, _args.root_directory, _args.regenerate_thumbnails))
                        for _raw in raw:
                            if os.path.exists(os.path.join(folder, extsplit[0] + _raw)):
                                url = urllib.parse.quote(extsplit[0]) + _raw
                                if _raw in (".tif", ".tiff"):
                                    image["tiff"] = f"{_args.web_root_url}{baseurl}{url}"
                                else:
                                    image["raw"] = f"{_args.web_root_url}{baseurl}{url}"
                        images.append(image)
                    if item == "info":
                        with open(os.path.join(folder, item), encoding="utf-8") as f:
                            _info = f.read()
                            info[urllib.parse.quote(folder)] = _info
            if not _args.non_interactive_mode:
                pbardict[folder].update(1)
                pbardict["htmlbar"].update(0)
        if not _args.non_interactive_mode:
            pbardict[folder].close()
        sizelistfile.seek(0)
        sizelistfile.write(json.dumps(sizelist, indent=4))
        sizelistfile.truncate()
        if os.path.exists(os.path.join(folder, ".sizelist.json")) and sizelist == {}:
            os.remove(os.path.join(folder, ".sizelist.json"))
        if not contains_files and not _args.use_fancy_folders:
            return
        if images or (_args.use_fancy_folders and not contains_files) or (_args.use_fancy_folders and _args.ignore_other_files):
            image_chunks = np.array_split(images, 8) if images else []
            with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
                _info: List[str] = None
                header = os.path.basename(folder) or title
                parent = (
                    None
                    if not foldername
                    else f"{_args.web_root_url}{urllib.parse.quote(foldername.removesuffix(folder.split('/')[-1] + '/'))}"
                )
                license_info: cclicense.License = (
                    {
                        "project": _args.site_title,
                        "author": _args.author_name,
                        "type": cclicense.licensenameswitch(_args.license_type),
                        "url": cclicense.licenseurlswitch(_args.license_type),
                        "pics": cclicense.licensepicswitch(_args.license_type),
                    }
                    if _args.license_type
                    else None
                )
                if urllib.parse.quote(folder) in info:
                    _info = []
                    _infolst = info[urllib.parse.quote(folder)].split("\n")
                    for i in _infolst:
                        if len(i) > 1:
                            _info.append(i)
                html = env.get_template("index.html.j2")
                content = html.render(
                    title=title,
                    favicon=f"{_args.web_root_url}{FAVICON_PATH}",
                    stylesheet=f"{_args.web_root_url}{GLOBAL_CSS_PATH}",
                    theme=f"{_args.web_root_url}.static/theme.css",
                    root=_args.web_root_url,
                    parent=parent,
                    header=header,
                    license=license_info,
                    subdirectories=subfolders,
                    images=image_chunks,
                    info=_info,
                    allimages=images,
                    webmanifest=_args.generate_webmanifest,
                )
                f.write(content)
        else:
            if os.path.exists(os.path.join(folder, "index.html")):
                os.remove(os.path.join(folder, "index.html"))
            if os.path.exists(os.path.join(folder, ".sizelist.json")):
                os.remove(os.path.join(folder, ".sizelist.json"))
        if not _args.non_interactive_mode:
            pbardict["htmlbar"].update(1)


def main() -> None:
    args = parse_arguments()
    args, raw = init_globals(args, RAW_EXTENSIONS)

    if os.path.exists(os.path.join(args.root_directory, ".lock")):
        print("Another instance of this program is running.")
        exit()

    try:
        Path(os.path.join(args.root_directory, ".lock")).touch()
        if not os.path.exists(os.path.join(args.root_directory, ".thumbnails")):
            os.mkdir(os.path.join(args.root_directory, ".thumbnails"))

        copy_static_files(args)

        if args.generate_webmanifest:
            print("Generating webmanifest...")
            webmanifest(args)

        if args.non_interactive_mode:
            print("Generating HTML files...")
            list_folder(args.root_directory, args.site_title, args, raw)
            with Pool(os.cpu_count()) as pool:
                print("Generating thumbnails...")
                pool.map(generate_thumbnail, thumbnails)
        else:
            pbardict["traversingbar"] = tqdm(desc="Traversing filesystem", unit="folders", ascii=True, dynamic_ncols=True)
            total = get_total_folders(args.root_directory, args)
            pbardict["traversingbar"].desc = "Traversing filesystem"
            pbardict["traversingbar"].update(0)
            pbardict["traversingbar"].close()

            pbardict["htmlbar"] = tqdm(total=total, desc="Generating HTML files", unit="folders", ascii=True, dynamic_ncols=True)
            list_folder(args.root_directory, args.site_title, args, raw)
            pbardict["htmlbar"].close()

            with Pool(os.cpu_count()) as pool:
                for _ in tqdm(
                    pool.imap_unordered(generate_thumbnail, thumbnails),
                    total=len(thumbnails),
                    desc="Generating thumbnails",
                    unit="files",
                    ascii=True,
                    dynamic_ncols=True,
                ):
                    pass
    finally:
        os.remove(os.path.join(args.root_directory, ".lock"))


if __name__ == "__main__":
    main()
