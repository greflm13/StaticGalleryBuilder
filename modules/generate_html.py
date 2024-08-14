import os
import urllib.parse
import fnmatch
import json
from typing import Any, Dict, List, Tuple

import numpy as np
from tqdm.auto import tqdm
from PIL import Image, ExifTags
from jinja2 import Environment, FileSystemLoader

import modules.cclicense as cclicense
from modules.argumentparser import Args

# Constants for file paths and exclusions
if __package__ is None:
    PACKAGE = ""
else:
    PACKAGE = __package__
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__).removesuffix(PACKAGE))
FAVICON_PATH = ".static/favicon.ico"
GLOBAL_CSS_PATH = ".static/global.css"
EXCLUDES = ["index.html", "manifest.json", "robots.txt"]

# Set the maximum image pixels to prevent decompression bomb DOS attacks
Image.MAX_IMAGE_PIXELS = 933120000

# Initialize Jinja2 environment for template rendering
env = Environment(loader=FileSystemLoader(os.path.join(SCRIPTDIR, "templates")))
thumbnails: List[Tuple[str, str]] = []
info: Dict[str, str] = {}
pbardict: Dict[str, tqdm] = {}


def initialize_sizelist(folder: str) -> Dict[str, Dict[str, int]]:
    """
    Initializes the size list JSON file if it doesn't exist.

    Args:
        folder (str): The folder in which the size list file is located.

    Returns:
        Dict[str, Dict[str, int]]: The size list dictionary.
    """
    sizelist = {}
    sizelist_path = os.path.join(folder, ".sizelist.json")
    if not os.path.exists(sizelist_path):
        with open(sizelist_path, "x", encoding="utf-8") as sizelistfile:
            sizelistfile.write("{}")
    with open(sizelist_path, "r+", encoding="utf-8") as sizelistfile:
        try:
            sizelist = json.loads(sizelistfile.read())
        except json.decoder.JSONDecodeError:
            sizelist = {}
    return sizelist


def update_sizelist(sizelist: Dict[str, Dict[str, int]], folder: str) -> None:
    """
    Updates the size list JSON file.

    Args:
        sizelist (Dict[str, Dict[str, int]]): The size list dictionary to be written to the file.
        folder (str): The folder in which the size list file is located.
    """
    sizelist_path = os.path.join(folder, ".sizelist.json")
    if sizelist != {}:
        with open(sizelist_path, "w", encoding="utf-8") as sizelistfile:
            sizelistfile.write(json.dumps(sizelist, indent=4))
    else:
        if os.path.exists(sizelist_path):
            os.remove(sizelist_path)


def get_image_info(item: str, folder: str) -> Dict[str, Any]:
    """
    Extracts image information and EXIF data.

    Args:
        item (str): The image file name.
        folder (str): The folder containing the image.

    Returns:
        Dict[str, Any]: A dictionary containing image width, height, and EXIF data.
    """
    with Image.open(os.path.join(folder, item)) as img:
        exif = img.getexif()
        width, height = img.size
    exifdata = {ExifTags.TAGS.get(key, key): val for key, val in exif.items()}
    if "Orientation" in exifdata and exifdata["Orientation"] in [6, 8]:
        width, height = height, width
    return {"width": width, "height": height}


def process_image(item: str, folder: str, _args: Args, baseurl: str, sizelist: Dict[str, Dict[str, int]], raw: List[str]) -> Dict[str, Any]:
    """
    Processes an image and prepares its data for the HTML template.

    Args:
        item (str): The image file name.
        folder (str): The folder containing the image.
        _args (Args): Parsed command line arguments.
        baseurl (str): Base URL for the web root.
        sizelist (Dict[str, Dict[str, int]]): Dictionary containing size information for images.
        raw (List[str]): List of raw image file extensions.

    Returns:
        Dict[str, Any]: Dictionary containing image details for HTML rendering.
    """
    extsplit = os.path.splitext(item)
    if item not in sizelist or _args.regenerate_thumbnails:
        sizelist[item] = get_image_info(item, folder)

    image = {
        "url": f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}",
        "thumbnail": f"{_args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(item)}.jpg",
        "name": item,
        "width": sizelist[item]["width"],
        "height": sizelist[item]["height"],
    }
    path = os.path.join(_args.root_directory, ".thumbnails", baseurl, item + ".jpg")
    if not os.path.exists(path) or _args.regenerate_thumbnails:
        if os.path.exists(path):
            os.remove(path)
        thumbnails.append((folder, item, _args.root_directory))

    for _raw in raw:
        if os.path.exists(os.path.join(folder, extsplit[0] + _raw)):
            url = urllib.parse.quote(extsplit[0]) + _raw
            if _raw in (".tif", ".tiff"):
                image["tiff"] = f"{_args.web_root_url}{baseurl}{url}"
            else:
                image["raw"] = f"{_args.web_root_url}{baseurl}{url}"
    return image


def generate_html(folder: str, title: str, _args: Args, raw: List[str], version: str) -> None:
    """
    Generates HTML content for a folder of images.

    Args:
        folder (str): The folder to generate HTML for.
        title (str): The title of the HTML page.
        _args (Args): Parsed command line arguments.
        raw (List[str]): Raw image file names.
    """
    sizelist = initialize_sizelist(folder)
    items = sorted(os.listdir(folder))

    contains_files = False
    images = []
    subfolders = []
    foldername = folder.removeprefix(_args.root_directory)
    foldername = f"{foldername}/" if foldername else ""
    baseurl = urllib.parse.quote(foldername)

    create_thumbnail_folder(foldername, _args.root_directory)

    if not _args.non_interactive_mode:
        pbardict[folder] = tqdm(total=len(items), desc=f"Getting image infos - {folder}", unit="files", ascii=True, dynamic_ncols=True)

    for item in items:
        if item not in EXCLUDES and not item.startswith("."):
            if os.path.isdir(os.path.join(folder, item)):
                process_subfolder(item, folder, baseurl, subfolders, _args, raw, version)
            else:
                contains_files = True
                if os.path.splitext(item)[1].lower() in _args.file_extensions:
                    images.append(process_image(item, folder, _args, baseurl, sizelist, raw))
                if item == "info":
                    process_info_file(folder, item)

        if not _args.non_interactive_mode:
            pbardict[folder].update(1)

    if not _args.non_interactive_mode:
        pbardict[folder].close()

    update_sizelist(sizelist, folder)

    if should_generate_html(images, contains_files, _args):
        create_html_file(folder, title, foldername, images, subfolders, _args, version)
    else:
        if os.path.exists(os.path.join(folder, "index.html")):
            os.remove(os.path.join(folder, "index.html"))

    if not _args.non_interactive_mode:
        pbardict["htmlbar"].update(1)


def create_thumbnail_folder(foldername: str, root_directory: str) -> None:
    """
    Creates a folder for thumbnails if it doesn't exist.

    Args:
        foldername (str): The name of the folder.
        root_directory (str): The root directory path.
    """
    thumbnails_path = os.path.join(root_directory, ".thumbnails", foldername)
    if not os.path.exists(thumbnails_path):
        os.mkdir(thumbnails_path)


def process_subfolder(item: str, folder: str, baseurl: str, subfolders: List[Dict[str, str]], _args: Args, raw: List[str], version: str) -> None:
    """
    Processes a subfolder.

    Args:
        item (str): The name of the subfolder.
        folder (str): The parent folder containing the subfolder.
        baseurl (str): Base URL for the web root.
        subfolders (List[Dict[str, str]]): List to store subfolder details.
        _args (Args): Parsed command line arguments.
        raw (List[str]): Raw image file extensions.
    """
    subfolder_url = f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}/index.html" if _args.web_root_url.startswith("file://") else f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}"
    subfolders.append({"url": subfolder_url, "name": item})
    if item not in _args.exclude_folders:
        if not any(fnmatch.fnmatchcase(os.path.join(folder, item), exclude) for exclude in _args.exclude_folders):
            generate_html(os.path.join(folder, item), os.path.join(folder, item).removeprefix(_args.root_directory), _args, raw, version)


def process_info_file(folder: str, item: str) -> None:
    """
    Processes an info file.

    Args:
        folder (str): The folder containing the info file.
        item (str): The info file name.
    """
    with open(os.path.join(folder, item), encoding="utf-8") as f:
        info[urllib.parse.quote(folder)] = f.read()


def should_generate_html(images: List[Dict[str, Any]], contains_files, _args: Args) -> bool:
    """
    Determines if HTML should be generated.

    Args:
        images (List[Dict[str, Any]]): List of images.
        _args (Args): Parsed command line arguments.

    Returns:
        bool: True if HTML should be generated, False otherwise.
    """
    return images or (_args.use_fancy_folders and not contains_files) or (_args.use_fancy_folders and _args.ignore_other_files)


def create_html_file(folder: str, title: str, foldername: str, images: List[Dict[str, Any]], subfolders: List[Dict[str, str]], _args: Args, version: str) -> None:
    """
    Creates the HTML file using the template.

    Args:
        folder (str): The folder to create the HTML file in.
        title (str): The title of the HTML page.
        foldername (str): The name of the folder.
        images (List[Dict[str, Any]]): A list of images to include in the HTML.
        subfolders (List[Dict[str, str]]): A list of subfolders to include in the HTML.
        _args (Args): Parsed command line arguments.
    """
    image_chunks = np.array_split(images, 8) if images else []
    header = os.path.basename(folder) or title
    parent = None if not foldername else f"{_args.web_root_url}{urllib.parse.quote(foldername.removesuffix(folder.split('/')[-1] + '/'))}"
    if parent and _args.web_root_url.startswith("file://"):
        parent += "index.html"

    license_info = (
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

    folder_info = info.get(urllib.parse.quote(folder), "").split("\n")
    _info = [i for i in folder_info if len(i) > 1] if folder_info else None

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
        version=version,
    )

    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(content)


def list_folder(total: int, folder: str, title: str, _args: Args, raw: List[str], version: str) -> List[Tuple[str, str]]:
    """
    Lists and processes a folder, generating HTML files.

    Args:
        total (int): Total number of folders to process.
        folder (str): The folder to process.
        title (str): The title of the HTML page.
        _args (Args): Parsed command line arguments.
        raw (List[str]): Raw image file names.

    Returns:
        List[Tuple[str, str]]: List of thumbnails generated.
    """
    if not _args.non_interactive_mode:
        pbardict["htmlbar"] = tqdm(total=total, desc="Generating HTML files", unit="folders", ascii=True, dynamic_ncols=True)
    generate_html(folder, title, _args, raw, version)
    return thumbnails
