#!/usr/bin/env python3
import os
import argparse
import urllib.parse
import shutil
import fnmatch
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from jinja2 import Environment, FileSystemLoader
from tqdm.auto import tqdm
from PIL import Image
from rich_argparse import RichHelpFormatter, HelpPreviewAction

import cclicense

# fmt: off
# Constants
STATIC_FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
FAVICON_PATH = ".static/favicon.ico"
GLOBAL_CSS_PATH = ".static/global.css"
DEFAULT_THEME_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "themes", "default.css")
DEFAULT_AUTHOR = "Author"
VERSION = "1.8.0"
RAW_EXTENSIONS = [".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr", ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"]
IMG_EXTENSIONS = [".jpg", ".jpeg"]
EXCLUDES = [".lock", "index.html", ".thumbnails", ".static"]
NOT_LIST = ["*/Galleries/*", "Archives"]
# fmt: on

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")))
thumbnails: List[Tuple[str, str]] = []
info: Dict[str, str] = {}


class Args:
    root_directory: str
    web_root_url: str
    site_title: str
    regenerate_thumbnails: bool
    non_interactive_mode: bool
    use_fancy_folders: bool
    license_type: Optional[str]
    author_name: str
    file_extensions: List[str]
    theme_path: str
    ignore_other_files: bool
    exclude_folders: List[str]


# fmt: off
def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(description="Generate HTML files for a static image hosting website.", formatter_class=RichHelpFormatter)
    parser.add_argument("-p", "--root-directory", help="Root directory containing the images.", required=True, type=str, dest="root_directory", metavar="ROOT")
    parser.add_argument("-w", "--web-root-url", help="Base URL of the web root for the image hosting site.", required=True, type=str, dest="web_root_url", metavar="URL")
    parser.add_argument("-t", "--site-title", help="Title of the image hosting site.", required=True, type=str, dest="site_title", metavar="TITLE")
    parser.add_argument("-r", "--regenerate-thumbnails", help="Regenerate thumbnails even if they already exist.", action="store_true", default=False, dest="regenerate_thumbnails")
    parser.add_argument("-n", "--non-interactive-mode", help="Run in non-interactive mode, disabling progress bars.", action="store_true", default=False, dest="non_interactive_mode")
    parser.add_argument("-l", "--license-type", help="Specify the license type for the images.", choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], default=None, dest="license_type", metavar="LICENSE")
    parser.add_argument("-a", "--author-name", help="Name of the author of the images.", default=DEFAULT_AUTHOR, type=str, dest="author_name", metavar="AUTHOR")
    parser.add_argument("-e", "--file-extensions", help="File extensions to include (can be specified multiple times).", action="append", dest="file_extensions", metavar="EXTENSION")
    parser.add_argument("--theme-path", help="Path to the CSS theme file.", default=DEFAULT_THEME_PATH, type=str, dest="theme_path", metavar="PATH")
    parser.add_argument("--use-fancy-folders", help="Enable fancy folder view instead of the default Apache directory listing.", action="store_true", default=False, dest="use_fancy_folders")
    parser.add_argument("--ignore-other-files", help="Ignore files that do not match the specified extensions.", action="store_true", default=False, dest="ignore_other_files")
    parser.add_argument("--exclude-folder", help="Folders to exclude from processing, globs supported (can be specified multiple times).", action="append", dest="exclude_folders", metavar="FOLDER")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg")
    parsed_args = parser.parse_args()
    _args = Args()
    _args.root_directory = parsed_args.root_directory
    _args.web_root_url = parsed_args.web_root_url
    _args.site_title = parsed_args.site_title
    _args.regenerate_thumbnails = parsed_args.regenerate_thumbnails
    _args.non_interactive_mode = parsed_args.non_interactive_mode
    _args.use_fancy_folders = parsed_args.use_fancy_folders
    _args.license_type = parsed_args.license_type
    _args.author_name = parsed_args.author_name
    _args.file_extensions = parsed_args.file_extensions
    _args.theme_path = parsed_args.theme_path
    _args.ignore_other_files = parsed_args.ignore_other_files
    _args.exclude_folders = parsed_args.exclude_folders
    return _args
# fmt: on


def init_globals(_args: Args) -> Args:
    global RAW_EXTENSIONS
    if not _args.file_extensions:
        _args.file_extensions = IMG_EXTENSIONS
    if not _args.exclude_folders:
        _args.exclude_folders = NOT_LIST
    _args.root_directory = _args.root_directory.rstrip("/") + "/"
    _args.web_root_url = _args.web_root_url.rstrip("/") + "/"

    RAW_EXTENSIONS = [ext.lower() for ext in RAW_EXTENSIONS] + [ext.upper() for ext in RAW_EXTENSIONS]

    return _args


def copy_static_files(_args: Args) -> None:
    shutil.copytree(STATIC_FILES_DIR, os.path.join(_args.root_directory, ".static"), dirs_exist_ok=True)
    shutil.copyfile(_args.theme_path, os.path.join(_args.root_directory, ".static", "theme.css"))


def generate_thumbnail(arguments: Tuple[str, str]) -> None:
    folder, item = arguments
    path = os.path.join(args.root_directory, ".thumbnails", folder.removeprefix(args.root_directory), os.path.splitext(item)[0]) + ".jpg"
    if not os.path.exists(path) or args.regenerate_thumbnails:
        try:
            with Image.open(os.path.join(folder, item)) as img:
                img.thumbnail((512, 512))
                img.save(path, "JPEG", quality=75, optimize=True)
        except OSError:
            print(f"Failed to generate thumbnail for {os.path.join(folder, item)}")


def get_total_folders(folder: str, _total: int = 0) -> int:

    _total += 1

    pbar.desc = f"Traversing filesystem - {folder}"
    pbar.update(1)

    items = os.listdir(folder)
    items.sort()
    for item in items:
        if item not in EXCLUDES:
            if os.path.isdir(os.path.join(folder, item)):
                if item not in args.exclude_folders:
                    skip = False
                    for exclude in args.exclude_folders:
                        if fnmatch.fnmatchcase(os.path.join(folder, item), exclude):
                            skip = True
                    if not skip:
                        _total = get_total_folders(os.path.join(folder, item), _total)
    return _total


def list_folder(folder: str, title: str) -> None:
    items = os.listdir(folder)
    items.sort()
    images: List[Dict[str, Any]] = []
    subfolders: List[Dict[str, str]] = []
    foldername = folder.removeprefix(args.root_directory)
    foldername = f"{foldername}/" if foldername else ""
    baseurl = urllib.parse.quote(foldername)
    if not os.path.exists(os.path.join(args.root_directory, ".thumbnails", foldername)):
        os.mkdir(os.path.join(args.root_directory, ".thumbnails", foldername))
    contains_files = False
    imgpbar = tqdm(total=len(items), desc=f"Getting image info - {folder}", unit="files", ascii=True, dynamic_ncols=True)
    for item in items:
        if item not in EXCLUDES:
            if os.path.isdir(os.path.join(folder, item)):
                subfolder = {"url": f"{args.web_root_url}{baseurl}{urllib.parse.quote(item)}", "name": item}
                subfolders.append(subfolder)
                if item not in args.exclude_folders:
                    skip = False
                    for exclude in args.exclude_folders:
                        if fnmatch.fnmatchcase(os.path.join(folder, item), exclude):
                            skip = True
                    if not skip:
                        list_folder(os.path.join(folder, item), os.path.join(folder, item).removeprefix(args.root_directory))
            else:
                extsplit = os.path.splitext(item)
                contains_files = True
                if extsplit[1].lower() in args.file_extensions:
                    with Image.open(os.path.join(folder, item)) as img:
                        width, height = img.size
                    image = {
                        "url": f"{args.web_root_url}{baseurl}{urllib.parse.quote(item)}",
                        "thumbnail": f"{args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(extsplit[0])}.jpg",
                        "name": item,
                        "width": width,
                        "height": height,
                    }
                    if not os.path.exists(os.path.join(args.root_directory, ".thumbnails", foldername, item)):
                        thumbnails.append((folder, item))
                    for raw in RAW_EXTENSIONS:
                        if os.path.exists(os.path.join(folder, extsplit[0] + raw)):
                            url = urllib.parse.quote(extsplit[0]) + raw
                            if raw in (".tif", ".tiff"):
                                image["tiff"] = f"{args.web_root_url}{baseurl}{url}"
                            else:
                                image["raw"] = f"{args.web_root_url}{baseurl}{url}"
                    images.append(image)
                if item == "info":
                    with open(os.path.join(folder, item), encoding="utf-8") as f:
                        _info = f.read()
                        info[urllib.parse.quote(folder)] = _info
        if not args.non_interactive_mode:
            imgpbar.update(1)
            pbar.update(0)
    if not contains_files and not args.use_fancy_folders:
        return
    if images or (args.use_fancy_folders and not contains_files) or (args.use_fancy_folders and args.ignore_other_files):
        image_chunks = np.array_split(images, 8) if images else []
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
            _info: List[str] = None
            header = os.path.basename(folder) or title
            parent = None if not foldername else f"{args.web_root_url}{urllib.parse.quote(foldername.removesuffix(folder.split('/')[-1] + '/'))}"
            license_info: cclicense.License = (
                {
                    "project": args.site_title,
                    "author": args.author_name,
                    "type": cclicense.licensenameswitch(args.license_type),
                    "url": cclicense.licenseurlswitch(args.license_type),
                    "pics": cclicense.licensepicswitch(args.license_type),
                }
                if args.license_type
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
                favicon=f"{args.web_root_url}{FAVICON_PATH}",
                stylesheet=f"{args.web_root_url}{GLOBAL_CSS_PATH}",
                theme=f"{args.web_root_url}.static/theme.css",
                root=args.web_root_url,
                parent=parent,
                header=header,
                license=license_info,
                subdirectories=subfolders,
                images=image_chunks,
                info=_info,
                allimages=images,
            )
            f.write(content)
    else:
        if os.path.exists(os.path.join(folder, "index.html")):
            os.remove(os.path.join(folder, "index.html"))
    if not args.non_interactive_mode:
        pbar.update(1)


def main() -> None:
    global args, pbar

    args = parse_arguments()
    args = init_globals(args)

    if os.path.exists(os.path.join(args.root_directory, ".lock")):
        print("Another instance of this program is running.")
        exit()

    try:
        Path(os.path.join(args.root_directory, ".lock")).touch()
        if not os.path.exists(os.path.join(args.root_directory, ".thumbnails")):
            os.mkdir(os.path.join(args.root_directory, ".thumbnails"))

        print("Copying static files...")
        copy_static_files(args)

        if args.non_interactive_mode:
            print("Generating HTML files...")
            list_folder(args.root_directory, args.site_title)
            with Pool(os.cpu_count()) as pool:
                print("Generating thumbnails...")
                pool.map(generate_thumbnail, thumbnails)
        else:
            pbar = tqdm(desc="Traversing filesystem", unit="folders", ascii=True, dynamic_ncols=True)
            total = get_total_folders(args.root_directory)
            pbar.desc = "Traversing filesystem"
            pbar.update(0)
            pbar.close()

            pbar = tqdm(total=total, desc="Generating HTML files", unit="folders", ascii=True, dynamic_ncols=True)
            list_folder(args.root_directory, args.site_title)
            pbar.close()

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
