#!/usr/bin/env python3
import os
import re
import sys
import shutil
import urllib.error
import urllib.parse
import urllib.request
from multiprocessing import Pool, freeze_support
from pathlib import Path

from tqdm.auto import tqdm
from PIL import Image, ImageOps
from jsmin import jsmin

from modules.argumentparser import parse_arguments, Args


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

args = parse_arguments(VERSION)

LOCKFILE = os.path.join(args.root_directory, ".lock")
if os.path.exists(LOCKFILE):
    print("Another instance of this program is running.")
    sys.exit()
else:
    from modules.logger import logger
    from modules.svg_handling import icons, webmanifest, extract_colorscheme
    from modules.generate_html import list_folder


def init_globals(_args: Args, raw: list[str]) -> tuple[Args, list[str]]:
    """
    Initialize global variables and set default values for arguments.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    raw : list[str]
        list of raw file extensions.

    Returns:
    --------
    tuple[Args, list[str]]
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
    logger.info("minifying javascript")
    with open(os.path.join(SCRIPTDIR, "templates", "functionality.js"), "r", encoding="utf-8") as js_file:
        with open(os.path.join(static_dir, "functionality.min.js"), "w+", encoding="utf-8") as min_file:
            min_file.write(jsmin(js_file.read()))


def generate_thumbnail(arguments: tuple[str, str, str]) -> None:
    """
    Generate a thumbnail for a given image.

    Parameters:
    -----------
    arguments : tuple[str, str, str, bool]
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


def main(args) -> None:
    """
    Main function to process images and generate a static image hosting website.
    """
    thumbnails: list[tuple[str, str, str]] = []

    args, raw = init_globals(args, RAW_EXTENSIONS)

    try:
        Path(LOCKFILE).touch()
        logger.info("starting builder", extra={"version": VERSION, "arguments": args})

        logger.info("getting logo from sorogon.eu")
        req = urllib.request.Request("https://files.sorogon.eu/logo.svg")
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                logo = res.read().decode()

            if logo.startswith("<?xml"):
                logo = re.sub(r"<\?xml.+\?>", "", logo).strip()
            if logo.startswith("<!--"):
                logo = re.sub(r"<!--.+-->", "", logo).strip()
            logo = logo.replace("\n", " ")
            logo = " ".join(logo.split())
        except urllib.error.URLError:
            logo = "&lt;/srgn&gt;"

        if args.reread_metadata:
            logger.warning("reread metadata flag is set to true, all image metadata will be reread")
        if args.regenerate_thumbnails:
            logger.warning("regenerate thumbnails flag is set to true, all thumbnails will be regenerated")
            thumbdir = os.path.join(args.root_directory, ".thumbnails")
            if os.path.exists(thumbdir):
                logger.info("removing old thumbnails folder")
                shutil.rmtree(thumbdir)
        os.makedirs(thumbdir, exist_ok=True)

        copy_static_files(args)
        icons(args)

        if args.generate_webmanifest:
            print("Generating webmanifest...")
            webmanifest(args)

        if args.non_interactive_mode:
            logger.info("generating HTML files")
            print("Generating HTML files...")
            thumbnails = list_folder(args.root_directory, args.site_title, args, raw, VERSION, logo)
            with Pool(os.cpu_count()) as pool:
                logger.info("generating thumbnails")
                print("Generating thumbnails...")
                pool.map(generate_thumbnail, thumbnails)
        else:
            thumbnails = list_folder(args.root_directory, args.site_title, args, raw, VERSION, logo)

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
        os.remove(LOCKFILE)
        logger.info("finished builder", extra={"version": VERSION})


if __name__ == "__main__":
    freeze_support()
    main(args)
