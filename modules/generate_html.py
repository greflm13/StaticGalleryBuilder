import os
import re
import urllib.parse
import fnmatch
import json
import html
from typing import Any
from datetime import datetime
from collections import defaultdict

from tqdm.auto import tqdm
from PIL import Image, ExifTags, TiffImagePlugin, UnidentifiedImageError
from jinja2 import Environment, FileSystemLoader
from defusedxml import ElementTree
from bs4 import BeautifulSoup

from modules.logger import logger
from modules import cclicense
from modules.argumentparser import Args
from modules.datatypes.metadata import Metadata, ImageMetadata, SubfolderMetadata

# Constants for file paths and exclusions
if __package__ is None:
    PACKAGE = ""
else:
    PACKAGE = __package__
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__).removesuffix(PACKAGE))
FAVICON_PATH = ".static/favicon.ico"
GLOBAL_CSS_PATH = ".static/global.css"
EXCLUDES = ["index.html", "manifest.json", "robots.txt"]

# Set the maximum image pixels
Image.MAX_IMAGE_PIXELS = 933120000

# Initialize Jinja2 environment for template rendering
env = Environment(loader=FileSystemLoader(os.path.join(SCRIPTDIR, "templates")))
thumbnails: list[tuple[str, str, str]] = []
info: dict[str, str] = {}
licens: dict[str, str] = {}


def getxmp(strbuffer: str) -> dict[str, Any]:
    """
    Returns a dictionary containing the XMP tags.
    Requires defusedxml to be installed.

    :returns: XMP tags in a dictionary.
    """

    def get_name(tag: str) -> str:
        return re.sub("^{[^}]+}", "", tag)

    def get_value(element) -> str | dict[str, Any] | None:
        value: dict[str, Any] = {get_name(k): v for k, v in element.attrib.items()}
        children = list(element)
        if children:
            for child in children:
                name = get_name(child.tag)
                child_value = get_value(child)
                if name in value:
                    if not isinstance(value[name], list):
                        value[name] = [value[name]]
                    value[name].append(child_value)
                else:
                    value[name] = child_value
        elif value:
            if element.text:
                value["text"] = element.text
        else:
            return element.text
        return value

    root = ElementTree.fromstring(strbuffer)
    return {get_name(root.tag): get_value(root)}


def initialize_metadata(folder: str) -> Metadata:
    """
    Initializes the metadata JSON file if it doesn't exist.

    Args:
        folder (str): The folder in which the metadata file is located.

    Returns:
        dict[str, dict[str, int]]: The metadata dictionary.
    """
    metadata = {}
    metadata_path = os.path.join(folder, ".metadata.json")
    if not os.path.exists(metadata_path):
        logger.info("creating new metadata file", extra={"file": metadata_path})
        with open(metadata_path, "x", encoding="utf-8") as metadatafile:
            metadatafile.write("{}")
    with open(metadata_path, "r+", encoding="utf-8") as metadatafile:
        logger.info("reading metadata file", extra={"file": metadata_path})
        try:
            metadata = json.loads(metadatafile.read())
        except json.decoder.JSONDecodeError:
            logger.warning("invalid JSON in metadata file", extra={"file": metadata_path})
            metadata = {}

    # remove old sizelist if it exists
    sizelist_path = os.path.join(folder, ".sizelist.json")
    if os.path.exists(sizelist_path):
        with open(sizelist_path, "r") as sizelist:
            metadata = json.loads(sizelist.read())
        logger.warning("found old .sizelist.json, removing it...", extra={"path": sizelist_path})
        os.remove(sizelist_path)

    # convert from old metadata format
    if "images" not in metadata and "subfolders" not in metadata:
        images = metadata.copy()
        metadata = {}
        metadata["images"] = images
    elif "images" not in metadata:
        metadata["images"] = {}
    for k, v in metadata["images"].items():
        if "width" in v:
            metadata["images"][k]["w"] = v["width"]
            del metadata["images"][k]["width"]
        if "height" in v:
            metadata["images"][k]["h"] = v["height"]
            del metadata["images"][k]["height"]
        if "tags" not in v:
            metadata["images"][k]["tags"] = []
        if "exifdata" not in v:
            metadata["images"][k]["exifdata"] = None
        if "xmp" not in v:
            metadata["images"][k]["xmp"] = None
        if "title" not in v:
            metadata["images"][k]["title"] = v["name"]

    return Metadata.from_dict(metadata)


def update_metadata(metadata: Metadata, folder: str) -> None:
    """
    Updates the metadata JSON file.

    Args:
        metadata (dict[str, dict[str, int]]): The metadata dictionary to be written to the file.
        folder (str): The folder in which the metadata file is located.
    """
    metadata_path = os.path.join(folder, ".metadata.json")
    if metadata:
        with open(metadata_path, "w", encoding="utf-8") as metadatafile:
            logger.info("writing metadata file", extra={"file": metadata_path})
            metadatafile.write(json.dumps(metadata.to_dict(), indent=4))
    else:
        if os.path.exists(metadata_path):
            logger.info("deleting empty metadata file", extra={"file": metadata_path})
            os.remove(metadata_path)


def get_image_info(item: str, folder: str) -> ImageMetadata:
    """
    Extracts image information and EXIF data.

    Args:
        item (str): The image file name.
        folder (str): The folder containing the image.

    Returns:
        dict[str, Any]: A dictionary containing image width, height, and EXIF data.
    """
    file = os.path.join(folder, item)
    try:
        with Image.open(file) as img:
            logger.info("extracting image information", extra={"file": file})
            width, height = img.size
            exif = img.getexif()
            xmpdata = img.getxmp()

    except UnidentifiedImageError:
        logger.error("cannot identify image file", extra={"file": file})
        print(f"cannot identify image file: {file}")
        return ImageMetadata(w=None, h=None, tags=[], exifdata=None, xmp=None, src="", msrc="", name="", title="")
    if exif:
        logger.info("extracting EXIF data", extra={"file": file})
        ifd = exif.get_ifd(ExifTags.IFD.Exif)
        exifdatas = dict(exif.items()) | ifd
        exifdata = {}
        for tag_id in exifdatas:
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            content = exifdatas.get(tag_id)
            if isinstance(content, bytes):
                content = "0x" + content.hex()
            if isinstance(content, TiffImagePlugin.IFDRational):
                content = content.limit_rational(1000000)
            if isinstance(content, tuple):
                newtuple = ()
                for i in content:
                    if isinstance(i, TiffImagePlugin.IFDRational):
                        newtuple = (*newtuple, i.limit_rational(1000000))
                if newtuple:
                    content = newtuple
            if tag in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                epr = r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}"
                if re.match(epr, str(content)):
                    try:
                        content = datetime.strptime(str(content), "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        content = None
                else:
                    content = None
            exifdata[tag] = content
        if "Orientation" in exifdata and exifdata["Orientation"] in [6, 8]:
            logger.info("image is rotated", extra={"file": file})
            width, height = height, width
        for key in ["PrintImageMatching", "UserComment", "MakerNote"]:
            if key in exifdata:
                del exifdata[key]
    else:
        exifdata = None
    tags = []
    xmp = None
    if xmpdata:
        logger.info("extracting XMP data", extra={"file": file})
        try:
            tags = xmpdata["xmpmeta"]["RDF"]["Description"]["subject"]["Bag"]["li"]
            if isinstance(tags, str):
                tags = [tags]
        except TypeError:
            pass
        except KeyError:
            pass
        try:
            tags = xmpdata["xapmeta"]["RDF"]["Description"]["subject"]["Bag"]["li"]
            if isinstance(tags, str):
                tags = [tags]
        except TypeError:
            pass
        except KeyError:
            pass
        try:
            tags = xmpdata["xmpmeta"]["RDF"]["Description"]["hierarchicalSubject"]["Bag"]["li"]
            if isinstance(tags, str):
                tags = [tags]
        except TypeError:
            pass
        except KeyError:
            pass
        try:
            tags = xmpdata["xapmeta"]["RDF"]["Description"]["hierarchicalSubject"]["Bag"]["li"]
            if isinstance(tags, str):
                tags = [tags]
        except TypeError:
            pass
        except KeyError:
            pass
    sidecarfile = os.path.join(folder, item + ".xmp")
    if os.path.exists(sidecarfile):
        logger.info("xmp sidecar file found", extra={"file": sidecarfile})
        try:
            tags = get_tags(sidecarfile)
        except Exception as e:
            logger.error(e)
    if None in tags:  # type: ignore
        tags.remove(None)  # type: ignore
    if not isinstance(tags, list):
        tags = []
    return ImageMetadata(w=width, h=height, tags=tags, exifdata=exifdata, xmp=xmp, src="", msrc="", name="", title="")


def nested_dict():
    return defaultdict(nested_dict)


def insert_path(d, path):
    for part in path[:-1]:
        d = d[part]
    last = path[-1]
    if not isinstance(d[last], dict):
        d[last] = {}


def finalize(d):
    if isinstance(d, defaultdict):
        return {k: finalize(d[k]) for k in sorted(d)}
    return d or []


def parse_hierarchical_tags(tags, delimiter="|"):
    tree = nested_dict()
    for tag in tags:
        parts = tag.split(delimiter)
        insert_path(tree, parts)
    return finalize(tree)


def get_tags(sidecarfile: str) -> list[str]:
    """
    Extracts Tags from XMP sidecar file

    Args:
        sidecarfile (str): The path to the XMP sidecar file.

    Returns:
        list[str]: List containing image tags.
    """
    logger.info("extracting XMP sidecar file data", extra={"file": sidecarfile})
    with open(sidecarfile) as sidecar:
        strbuffer = sidecar.read()
    xmpdata = getxmp(strbuffer)
    tags = []
    try:
        tags = xmpdata["xmpmeta"]["RDF"]["Description"]["subject"]["Bag"]["li"]
        if isinstance(tags, str):
            tags = [tags]
    except TypeError:
        pass
    except KeyError:
        pass
    try:
        tags = xmpdata["xapmeta"]["RDF"]["Description"]["subject"]["Bag"]["li"]
        if isinstance(tags, str):
            tags = [tags]
    except TypeError:
        pass
    except KeyError:
        pass
    try:
        tags = xmpdata["xmpmeta"]["RDF"]["Description"]["hierarchicalSubject"]["Bag"]["li"]
        if isinstance(tags, str):
            tags = [tags]
    except TypeError:
        pass
    except KeyError:
        pass
    try:
        tags = xmpdata["xapmeta"]["RDF"]["Description"]["hierarchicalSubject"]["Bag"]["li"]
        if isinstance(tags, str):
            tags = [tags]
    except TypeError:
        pass
    except KeyError:
        pass
    if None in tags:  # type: ignore
        tags.remove(None)  # type: ignore
    return tags  # type: ignore


def process_image(item: str, folder: str, _args: Args, baseurl: str, metadata: Metadata, raw: list[str]) -> tuple[ImageMetadata, Metadata]:
    """
    Processes an image and prepares its data for the HTML template.

    Args:
        item (str): The image file name.
        folder (str): The folder containing the image.
        _args (Args): Parsed command line arguments.
        baseurl (str): Base URL for the web root.
        metadata (dict[str, dict[str, int]]): dictionary containing size information for images.
        raw (list[str]): list of raw image file extensions.

    Returns:
        dict[str, Any]: dictionary containing image details for HTML rendering.
    """
    extsplit = os.path.splitext(item)
    sidecarfile = os.path.join(folder, item + ".xmp")
    if item not in metadata.images or _args.reread_metadata:
        metadata.images[item] = get_image_info(item, folder)
    if _args.reread_sidecar and os.path.exists(sidecarfile):
        logger.info("xmp sidecar file found", extra={"file": sidecarfile})
        try:
            metadata.images[item].tags = get_tags(sidecarfile)
        except Exception as e:
            logger.error(e)

    image = metadata.images[item]
    image.src = f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}"
    image.msrc = f"{_args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(item)}.jpg"
    image.name = item
    image.title = item

    path = os.path.join(_args.root_directory, ".thumbnails", baseurl, item + ".jpg")
    if not os.path.exists(path) or _args.regenerate_thumbnails:
        if os.path.exists(path):
            os.remove(path)
        thumbnails.append((folder, item, _args.root_directory))

    for _raw in raw:
        file = os.path.join(folder, extsplit[0] + _raw)
        if os.path.exists(file):
            url = f"{_args.web_root_url}{baseurl}{urllib.parse.quote(extsplit[0])}{_raw}"
            if _raw in (".tif", ".tiff"):
                logger.info("tiff file found", extra={"file": file})
                image.tiff = url
            else:
                logger.info("raw file found", extra={"file": file, "extension": _raw})
                image.raw = url

    metadata.images[item] = image

    return image, metadata


def generate_html(folder: str, title: str, _args: Args, raw: list[str], version: str, logo: str) -> set[str]:
    """
    Generates HTML content for a folder of images.

    Args:
        folder (str): The folder to generate HTML for.
        title (str): The title of the HTML page.
        _args (Args): Parsed command line arguments.
        raw (list[str]): Raw image file names.
    """
    logger.info("processing folder", extra={"folder": folder})
    if _args.regenerate_thumbnails:
        if os.path.exists(os.path.join(folder, ".metadata.json")):
            logger.info("removing .metadata.json", extra={"folder": folder})
            os.remove(os.path.join(folder, ".metadata.json"))
    metadata = initialize_metadata(folder)
    items = sorted(os.listdir(folder))

    contains_files = False
    images: list[ImageMetadata] = []
    subfolders: list[SubfolderMetadata] = []
    subfoldertags: set[str] = set()
    foldername = folder.removeprefix(_args.root_directory)
    foldername = f"{foldername}/" if foldername else ""
    baseurl = urllib.parse.quote(foldername)

    gone = [item for item in metadata.images if item not in items]
    for gon in gone:
        del metadata.images[gon]

    create_thumbnail_folder(foldername, _args.root_directory)

    logger.info("processing contents", extra={"folder": folder})
    if not _args.non_interactive_mode:
        for item in tqdm(items, total=len(items), desc=f"Getting image infos - {folder}", unit="files", ascii=True, dynamic_ncols=True):
            if item not in EXCLUDES and not item.startswith(".") and os.path.splitext(item)[1][1:].lower() not in _args.ignore_extensions:
                if os.path.isdir(os.path.join(folder, item)):
                    subfoldertags.update(process_subfolder(item, folder, baseurl, subfolders, _args, raw, version, logo))
                else:
                    contains_files = True
                    if os.path.splitext(item)[1].lower() in _args.file_extensions:
                        img, metadata = process_image(item, folder, _args, baseurl, metadata, raw)
                        images.append(img)
                    if item == "info":
                        process_info_file(folder, item)
                    if item == "LICENSE":
                        process_license(folder, item)
    else:
        for item in items:
            if item not in EXCLUDES and not item.startswith(".") and os.path.splitext(item)[1][1:].lower() not in _args.ignore_extensions:
                if os.path.isdir(os.path.join(folder, item)):
                    subfoldertags.update(process_subfolder(item, folder, baseurl, subfolders, _args, raw, version, logo))
                else:
                    contains_files = True
                    if os.path.splitext(item)[1].lower() in _args.file_extensions:
                        img, metadata = process_image(item, folder, _args, baseurl, metadata, raw)
                        images.append(img)
                    if item == "info":
                        process_info_file(folder, item)
                    if item == "LICENSE":
                        process_license(folder, item)

    metadata.subfolders = subfolders
    if _args.reverse_sort:
        metadata.sort(reverse=True)
    else:
        metadata.sort()
    update_metadata(metadata, folder)

    if should_generate_html(images, contains_files, _args):
        subfoldertags = create_html_file(folder, title, foldername, images, subfolders, _args, version, logo, subfoldertags)
    else:
        if os.path.exists(os.path.join(folder, "index.html")):
            logger.info("removing existing index.html", extra={"folder": folder})
            os.remove(os.path.join(folder, "index.html"))
    return subfoldertags


def create_thumbnail_folder(foldername: str, root_directory: str) -> None:
    """
    Creates a folder for thumbnails if it doesn't exist.

    Args:
        foldername (str): The name of the folder.
        root_directory (str): The root directory path.
    """
    thumbnails_path = os.path.join(root_directory, ".thumbnails", foldername)
    if not os.path.exists(thumbnails_path):
        logger.info("creating thumbnail folder", extra={"path": thumbnails_path})
        os.mkdir(thumbnails_path)


def process_subfolder(item: str, folder: str, baseurl: str, subfolders: list[SubfolderMetadata], _args: Args, raw: list[str], version: str, logo: str) -> set[str]:
    """
    Processes a subfolder.

    Args:
        item (str): The name of the subfolder.
        folder (str): The parent folder containing the subfolder.
        baseurl (str): Base URL for the web root.
        subfolders (list[dict[str, str]]): list to store subfolder details.
        _args (Args): Parsed command line arguments.
        raw (list[str]): Raw image file extensions.
    """
    subfolder_url = (
        f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}/index.html"
        if _args.web_root_url.startswith("file://")
        else f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}"
    )
    thumb = None
    if _args.folder_thumbs:
        thumbitems = [i for i in sorted(os.listdir(os.path.join(folder, item))) if os.path.splitext(i)[1].lower() in _args.file_extensions]
        if len(thumbitems) > 0:
            if _args.reverse_sort:
                thumb = f"{_args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(item)}/{urllib.parse.quote(thumbitems[-1])}.jpg"
            else:
                thumb = f"{_args.web_root_url}.thumbnails/{baseurl}{urllib.parse.quote(item)}/{urllib.parse.quote(thumbitems[0])}.jpg"

    if item not in _args.exclude_folders:
        if not any(fnmatch.fnmatchcase(os.path.join(folder, item), exclude) for exclude in _args.exclude_folders):
            subfolders.append(SubfolderMetadata(url=subfolder_url, name=item, thumb=thumb, metadata=f"{_args.web_root_url}{baseurl}{urllib.parse.quote(item)}/.metadata.json"))
            return generate_html(os.path.join(folder, item), os.path.join(folder, item).removeprefix(_args.root_directory), _args, raw, version, logo)
    subfolders.append(SubfolderMetadata(url=subfolder_url, name=item, thumb=thumb))
    return set()


def process_license(folder: str, item: str) -> None:
    """
    Processes a LICENSE file, preserving formatting in HTML.

    Args:
        folder (str): The folder containing the LICENSE file.
        item (str): The LICENSE file name.
    """
    path = os.path.join(folder, item)
    with open(path, encoding="utf-8") as f:
        logger.info("processing LICENSE", extra={"path": path})
        raw_text = f.read()
        escaped_text = html.escape(raw_text)
        licens[urllib.parse.quote(folder)] = f"<pre>{escaped_text}</pre>"


def process_info_file(folder: str, item: str) -> None:
    """
    Processes an info file.

    Args:
        folder (str): The folder containing the info file.
        item (str): The info file name.
    """
    with open(os.path.join(folder, item), encoding="utf-8") as f:
        logger.info("processing info file", extra={"path": os.path.join(folder, item)})
        info[urllib.parse.quote(folder)] = f.read()


def should_generate_html(images: list[ImageMetadata], contains_files, _args: Args) -> bool:
    """
    Determines if HTML should be generated.

    Args:
        images (list[dict[str, Any]]): list of images.
        _args (Args): Parsed command line arguments.

    Returns:
        bool: True if HTML should be generated, False otherwise.
    """
    return bool(images) or (_args.use_fancy_folders and not contains_files) or (_args.use_fancy_folders and _args.ignore_other_files)


def format_html(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    return soup.prettify()


def create_html_file(
    folder: str, title: str, foldername: str, images: list[ImageMetadata], subfolders: list[SubfolderMetadata], _args: Args, version: str, logo: str, subfoldertags: set[str]
) -> set[str]:
    """
    Creates the HTML file using the template.

    Args:
        folder (str): The folder to create the HTML file in.
        title (str): The title of the HTML page.
        foldername (str): The name of the folder.
        images (list[dict[str, Any]]): A list of images to include in the HTML.
        subfolders (list[dict[str, str]]): A list of subfolders to include in the HTML.
        _args (Args): Parsed command line arguments.
    """
    html_file = os.path.join(folder, "index.html")
    logger.info("generating html file with jinja2", extra={"path": html_file})
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

    alltags = set()
    for img in images:
        if img.tags:
            alltags.update(img.tags)

    alltags.update(subfoldertags)

    folder_info = info.get(urllib.parse.quote(folder), "").split("\n")
    _info = [i for i in folder_info if len(i) > 1] if folder_info else None

    folder_license = licens.get(urllib.parse.quote(folder), False)

    license_url = ""

    if folder_license:
        license_html = os.path.join(folder, "license.html")
        license_url = _args.web_root_url + urllib.parse.quote(foldername) + "license.html"
        with open(license_html, "w+", encoding="utf-8") as f:
            logger.info("writing license html file", extra={"path": license_html})
            gtml = env.get_template("license.html.j2")
            content = gtml.render(
                title=f"{title} - LICENSE",
                favicon=f"{_args.web_root_url}{FAVICON_PATH}",
                stylesheet=f"{_args.web_root_url}{GLOBAL_CSS_PATH}",
                theme=f"{_args.web_root_url}.static/theme.css",
                root=_args.web_root_url,
                parent=f"{_args.web_root_url}{urllib.parse.quote(foldername)}",
                header=f"{header} - LICENSE",
                license=license_info,
                webmanifest=_args.generate_webmanifest,
                version=version,
                logo=logo,
                licensefile=folder_license,
            )
            f.write(format_html(content))

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
        info=_info,
        webmanifest=_args.generate_webmanifest,
        version=version,
        logo=logo,
        licensefile=license_url,
        tags=parse_hierarchical_tags(alltags),
    )

    with open(html_file, "w", encoding="utf-8") as f:
        logger.info("writing formatted html file", extra={"path": html_file})
        f.write(format_html(content))

    return set(sorted(alltags))


def list_folder(folder: str, title: str, _args: Args, raw: list[str], version: str, logo: str) -> list[tuple[str, str, str]]:
    """
    lists and processes a folder, generating HTML files.

    Args:
        total (int): Total number of folders to process.
        folder (str): The folder to process.
        title (str): The title of the HTML page.
        _args (Args): Parsed command line arguments.
        raw (list[str]): Raw image file names.

    Returns:
        list[tuple[str, str]]: list of thumbnails generated.
    """
    generate_html(folder, title, _args, raw, version, logo)
    return thumbnails
