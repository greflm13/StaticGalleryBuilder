#!/usr/bin/env python3
import os
import re
import shutil
import fnmatch
import urllib.parse
from multiprocessing import Pool, freeze_support
from pathlib import Path
from typing import Dict, List, Tuple

from tqdm.auto import tqdm
from PIL import Image, ImageOps

from modules.logger import logger
from modules.argumentparser import parse_arguments, Args
from modules.svg_handling import icons, webmanifest, extract_colorscheme
from modules.generate_html import list_folder, EXCLUDES


# fmt: off
# Constants
if __package__ is None:
    PACKAGE = ""
else:
    PACKAGE = __package__
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__).removesuffix(PACKAGE))
STATIC_FILES_DIR = os.path.join(os.path.abspath(SCRIPTDIR), "files")
VERSION = open(os.path.join(SCRIPTDIR, ".version"), "r", encoding="utf-8").read()
RAW_EXTENSIONS = [
    ".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr",
    ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos",
    ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl",
    ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"
]
IMG_EXTENSIONS = [".jpg", ".jpeg", ".png"]
NOT_LIST = ["*/Galleries/*", "Archives"]
# fmt: on

pbardict: Dict[str, tqdm] = {}


def init_globals(_args: Args, raw: List[str]) -> Tuple[Args, List[str]]:
    """
    Initialize global variables and set default values for arguments.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    raw : List[str]
        List of raw file extensions.

    Returns:
    --------
    Tuple[Args, List[str]]
        Updated arguments and raw file extensions.
    """
    if not _args.file_extensions:
        _args.file_extensions = IMG_EXTENSIONS
    if not _args.exclude_folders:
        _args.exclude_folders = NOT_LIST
    _args.root_directory = _args.root_directory.rstrip("/") + "/"
    _args.web_root_url = _args.web_root_url.rstrip("/") + "/"

    raw = [ext.lower() for ext in raw] + [ext.upper() for ext in raw]

    return _args, raw


def copy_static_files(_args: Args) -> None:
    """
    Copy static files to the root directory.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    """
    static_dir = os.path.join(_args.root_directory, ".static")
    if os.path.exists(static_dir):
        print("Removing existing .static folder...")
        logger.info("removing existing .static folder")
        shutil.rmtree(static_dir)

    print("Copying static files...")
    logger.info("copying static files")
    shutil.copytree(STATIC_FILES_DIR, static_dir, dirs_exist_ok=True)
    logger.info("reading theme file", extra={"theme": _args.theme_path})
    with open(_args.theme_path, "r", encoding="utf-8") as f:
        theme = f.read()
    split = theme.split(".foldericon {")
    split2 = split[1].split("}", maxsplit=1)
    themehead = split[0]
    themetail = split2[1]
    foldericon = split2[0].strip()
    foldericon = re.sub(r"/\*.*\*/", "", foldericon)
    for match in re.finditer(r"content: (.*);", foldericon):
        foldericon = match[1]
        foldericon = foldericon.replace('"', "")
        logger.info("found foldericon", extra={"foldericon": foldericon})
        break
    if "url" in foldericon:
        logger.info("foldericon in theme file, using it")
        shutil.copyfile(_args.theme_path, os.path.join(static_dir, "theme.css"))
        return
    with open(os.path.join(SCRIPTDIR, foldericon), "r", encoding="utf-8") as f:
        logger.info("Reading foldericon svg")
        svg = f.read()
    if "svg.j2" in foldericon:
        logger.info("foldericon in theme file is a jinja2 template")
        colorscheme = extract_colorscheme(_args.theme_path)
        for color_key, color_value in colorscheme.items():
            svg = svg.replace(f"{{{{ {color_key} }}}}", color_value)
        logger.info("replaced colors in svg")
    svg = urllib.parse.quote(svg)
    with open(os.path.join(static_dir, "theme.css"), "x", encoding="utf-8") as f:
        logger.info("writing theme file")
        f.write(themehead + '\n.foldericon {\n  content: url("data:image/svg+xml,' + svg + '");\n}\n' + themetail)


def generate_thumbnail(arguments: Tuple[str, str, str]) -> None:
    """
    Generate a thumbnail for a given image.

    Parameters:
    -----------
    arguments : Tuple[str, str, str, bool]
        A tuple containing the folder, item, root directory, and regenerate thumbnails flag.
    """
    folder, item, root_directory = arguments
    image = os.path.join(folder, item)
    path = os.path.join(root_directory, ".thumbnails", folder.removeprefix(root_directory), item) + ".jpg"
    oldpath = os.path.join(root_directory, ".thumbnails", folder.removeprefix(root_directory), os.path.splitext(item)[0]) + ".jpg"
    if os.path.exists(oldpath):
        try:
            shutil.move(oldpath, path)
        except FileNotFoundError:
            pass
    if not os.path.exists(path):
        logger.info("generating thumbnail for %s", item, extra={"path": image})
        try:
            with Image.open(image) as imgfile:
                imgrgb = imgfile.convert("RGB")
                img = ImageOps.exif_transpose(imgrgb)
                img.thumbnail((512, 512))
                img.save(path, "JPEG", quality=75, optimize=True, mode="RGB")
        except OSError:
            logger.error("Failed to generate thumbnail for %s", item, extra={"path": image})
            print(f"Failed to generate thumbnail for {image}")
            return
    else:
        logger.debug("thumbnail already exists for %s", item, extra={"path": image})


def get_total_folders(folder: str, _args: Args, _total: int = 0) -> int:
    """
    Recursively count the total number of folders to be processed.

    Parameters:
    -----------
    folder : str
        The current folder being processed.
    _args : Args
        Parsed command-line arguments.
    _total : int, optional
        The running total of folders, default is 0.

    Returns:
    --------
    int
        The total number of folders.
    """
    _total += 1
    pbardict["traversingbar"].desc = f"Traversing filesystem - {folder}"
    pbardict["traversingbar"].update(1)

    items = sorted(os.listdir(folder))
    for item in items:
        if item not in EXCLUDES and os.path.isdir(os.path.join(folder, item)) and not item.startswith("."):
            if item not in _args.exclude_folders and not any(fnmatch.fnmatchcase(os.path.join(folder, item), exclude) for exclude in _args.exclude_folders):
                logger.debug("Found folder %s in %s", item, folder)
                _total = get_total_folders(os.path.join(folder, item), _args, _total)
    return _total


def main() -> None:
    """
    Main function to process images and generate a static image hosting website.
    """
    logger.info("starting builder", extra={"version": VERSION})
    thumbnails: List[Tuple[str, str, str, bool]] = []

    args = parse_arguments(VERSION)
    args, raw = init_globals(args, RAW_EXTENSIONS)

    lock_file = os.path.join(args.root_directory, ".lock")
    if os.path.exists(lock_file):
        print("Another instance of this program is running.")
        logger.error("another instance of this program is running")
        exit()

    try:
        Path(lock_file).touch()
        if args.reread_metadata:
            logger.warning("reread metadata flag is set to true, all image metadata will be reread")
        if args.regenerate_thumbnails:
            logger.warning("regenerate thumbnails flag is set to true, all thumbnails will be regenerated")
            if os.path.exists(os.path.join(args.root_directory, ".thumbnails")):
                logger.info("removing old thumbnails folder")
                shutil.rmtree(os.path.join(args.root_directory, ".thumbnails"))
        os.makedirs(os.path.join(args.root_directory, ".thumbnails"), exist_ok=True)

        copy_static_files(args)
        icons(args)

        if args.generate_webmanifest:
            print("Generating webmanifest...")
            webmanifest(args)

        if args.non_interactive_mode:
            logger.info("generating HTML files")
            print("Generating HTML files...")
            thumbnails = list_folder(0, args.root_directory, args.site_title, args, raw, VERSION)
            with Pool(os.cpu_count()) as pool:
                logger.info("generating thumbnails")
                print("Generating thumbnails...")
                pool.map(generate_thumbnail, thumbnails)
        else:
            pbardict["traversingbar"] = tqdm(desc="Traversing filesystem", unit="folders", ascii=True, dynamic_ncols=True)
            logger.info("getting total number of folders to process")
            total = get_total_folders(args.root_directory, args)
            pbardict["traversingbar"].desc = "Traversing filesystem"
            pbardict["traversingbar"].update(0)
            pbardict["traversingbar"].close()

            thumbnails = list_folder(total, args.root_directory, args.site_title, args, raw, VERSION)

            with Pool(os.cpu_count()) as pool:
                logger.info("generating thumbnails")
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
        os.remove(lock_file)
        logger.info("finished builder", extra={"version": VERSION})
    return


if __name__ == "__main__":
    freeze_support()
    main()
