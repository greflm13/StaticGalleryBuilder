#!/usr/bin/env python3
import os
import argparse
import urllib.parse
import shutil
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from jinja2 import Environment, FileSystemLoader
from tqdm.auto import tqdm
from PIL import Image
from rich_argparse import RichHelpFormatter

import cclicense

# fmt: off
# Constants
STATIC_FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
FAVICON_PATH = ".static/favicon.ico"
GLOBAL_CSS_PATH = ".static/global.css"
DEFAULT_THEME_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "themes", "default.css")
DEFAULT_AUTHOR = "Author"
VERSION = "1.6.1"
RAW_EXTENSIONS = [".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr", ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"]
IMG_EXTENSIONS = [".jpg", ".jpeg"]
EXCLUDES = [".lock", "index.html", ".thumbnails", ".static"]
NOT_LIST = ["Galleries", "Archives"]
# fmt: on

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")))
thumbnails: List[Tuple[str, str]] = []


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


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(description="Generate HTML files for a static image hosting website.", formatter_class=RichHelpFormatter)
    parser.add_argument("-p", "--root-directory", help="Root directory containing the images.", required=True, type=str, dest="root_directory")
    parser.add_argument("-w", "--web-root-url", help="Base URL of the web root for the image hosting site.", required=True, type=str, dest="web_root_url")
    parser.add_argument("-t", "--site-title", help="Title of the image hosting site.", required=True, type=str, dest="site_title")
    parser.add_argument("-r", "--regenerate-thumbnails", help="Regenerate thumbnails even if they already exist.", action="store_true", default=False, dest="regenerate_thumbnails")
    parser.add_argument("-n", "--non-interactive-mode", help="Run in non-interactive mode, disabling progress bars.", action="store_true", default=False, dest="non_interactive_mode")
    parser.add_argument("-l", "--license-type", help="Specify the license type for the images.", choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], default=None, dest="license_type")
    parser.add_argument("-a", "--author-name", help="Name of the author of the images.", default=DEFAULT_AUTHOR, type=str, dest="author_name")
    parser.add_argument("-e", "--file-extensions", help="File extensions to include (can be specified multiple times).", action="append", dest="file_extensions")
    parser.add_argument("--theme-path", help="Path to the CSS theme file.", default=DEFAULT_THEME_PATH, type=str, dest="theme_path")
    parser.add_argument("--use-fancy-folders", help="Enable fancy folder view instead of the default Apache directory listing.", action="store_true", default=False, dest="use_fancy_folders")
    parser.add_argument("--ignore-other-files", help="Ignore files that do not match the specified extensions.", action="store_true", default=False, dest="ignore_other_files")
    parser.add_argument("--exclude-folder", help="Folders to exclude from processing (can be specified multiple times).", action="append", dest="exclude_folders")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    parsed_args = parser.parse_args()
    args = Args()
    args.root_directory = parsed_args.root_directory
    args.web_root_url = parsed_args.web_root_url
    args.site_title = parsed_args.site_title
    args.regenerate_thumbnails = parsed_args.regenerate_thumbnails
    args.non_interactive_mode = parsed_args.non_interactive_mode
    args.use_fancy_folders = parsed_args.use_fancy_folders
    args.license_type = parsed_args.license_type
    args.author_name = parsed_args.author_name
    args.file_extensions = parsed_args.file_extensions
    args.theme_path = parsed_args.theme_path
    args.ignore_other_files = parsed_args.ignore_other_files
    args.exclude_folders = parsed_args.exclude_folders
    return args


def init_globals(args: Args) -> None:
    global RAW_EXTENSIONS
    if not args.file_extensions:
        args.file_extensions = IMG_EXTENSIONS
    if not args.exclude_folders:
        args.exclude_folders = NOT_LIST
    args.root_directory = args.root_directory.rstrip("/") + "/"
    args.web_root_url = args.web_root_url.rstrip("/") + "/"

    RAW_EXTENSIONS = [ext.lower() for ext in RAW_EXTENSIONS] + [ext.upper() for ext in RAW_EXTENSIONS]


def copy_static_files(args: Args) -> None:
    shutil.copytree(STATIC_FILES_DIR, os.path.join(args.root_directory, ".static"), dirs_exist_ok=True)
    shutil.copyfile(args.theme_path, os.path.join(args.root_directory, ".static", "theme.css"))


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
            pass


def get_total_folders(folder: str) -> None:
    global total

    total += 1

    pbar.desc = f"Traversing filesystem - {folder}"
    pbar.update(1)

    items = os.listdir(folder)
    items.sort()
    for item in items:
        if item not in EXCLUDES:
            if os.path.isdir(os.path.join(folder, item)):
                if item not in args.exclude_folders:
                    get_total_folders(os.path.join(folder, item))


def list_folder(folder: str, title: str) -> None:
    if not args.non_interactive_mode:
        pbar.desc = f"Generating HTML files - {folder}"
        pbar.update(0)
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
    for item in items:
        if item not in EXCLUDES:
            if os.path.isdir(os.path.join(folder, item)):
                subfolder = {"url": f"{args.web_root_url}{baseurl}{urllib.parse.quote(item)}", "name": item}
                subfolders.append(subfolder)
                if item not in args.exclude_folders:
                    list_folder(os.path.join(folder, item), os.path.join(folder, item).removeprefix(args.root_directory))
            else:
                extsplit = os.path.splitext(item)
                contains_files = True
                if extsplit[1].lower() in args.file_extensions:
                    image = {
                        "url": f"{args.web_root_url}{baseurl}{urllib.parse.quote(item)}",
                        "thumbnail": f"{args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(extsplit[0])}.jpg",
                        "name": item,
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
    if not args.non_interactive_mode:
        pbar.desc = f"Generating HTML files - {folder}"
        pbar.update(0)
    if images or (args.use_fancy_folders and not contains_files) or (args.use_fancy_folders and args.ignore_other_files):
        image_chunks = np.array_split(images, 8) if images else []
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
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
            )
            f.write(content)
    else:
        if os.path.exists(os.path.join(folder, "index.html")):
            os.remove(os.path.join(folder, "index.html"))
    if not args.non_interactive_mode:
        pbar.update(1)


def main() -> None:
    global args, total, pbar, thumbnails
    total = 0

    args = parse_arguments()
    init_globals(args)

    if os.path.exists(os.path.join(args.root_directory, ".lock")):
        print("Another instance of this program is running.")
        exit()

    try:
        if not os.path.exists(os.path.join(args.root_directory, ".thumbnails")):
            os.mkdir(os.path.join(args.root_directory, ".thumbnails"))
        Path(os.path.join(args.root_directory, ".lock")).touch()

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
            get_total_folders(args.root_directory)
            pbar.desc = "Traversing filesystem"
            pbar.update(0)
            pbar.close()

            pbar = tqdm(total=total, desc="Generating HTML files", unit="files", ascii=True, dynamic_ncols=True)
            list_folder(args.root_directory, args.site_title)
            pbar.desc = "Generating html files"
            pbar.update(0)
            pbar.close()

            with Pool(os.cpu_count()) as pool:
                for _ in tqdm(pool.imap_unordered(generate_thumbnail, thumbnails), total=len(thumbnails), desc="Generating thumbnails", unit="files", ascii=True, dynamic_ncols=True):
                    pass
    finally:
        os.remove(os.path.join(args.root_directory, ".lock"))


if __name__ == "__main__":
    main()
