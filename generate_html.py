#!/usr/bin/env python3
import os
import argparse
import urllib.parse
import shutil
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from jinja2 import Environment, FileSystemLoader
from tqdm.auto import tqdm

import cclicense

environment = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates/")))

_FOLDERICON = "https://www.svgrepo.com/show/400249/folder.svg"
_STATICFILES = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
_FAVICON = ".static/favicon.ico"
_STYLE = ".static/global.css"
_THEME = os.path.join(os.path.abspath(os.path.dirname(__file__)), "themes", "default.css")
_AUTHOR = "Author"
VERSION = "1.3"
# fmt: off
rawext = [".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr", ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"]
imgext = [".jpg", ".jpeg"]
excludes = [".lock", "index.html", ".thumbnails", ".static"]
notlist = ["Galleries", "Archives"]
# fmt: on

thumbnails: list[tuple[str, str]] = []


def thumbnail_convert(arguments: tuple[str, str]):
    folder, item = arguments
    path = os.path.join(args.root, ".thumbnails", folder.removeprefix(args.root), os.path.splitext(item)[0]) + ".jpg"
    if not os.path.exists(path) or args.regenerate:
        if shutil.which("magick"):
            os.system(
                f'magick "{os.path.join(folder, item)}" -quality 75% -define jpeg:size=1024x1024 -define jpeg:extent=100kb -thumbnail 512x512 -auto-orient "{path}"'
            )
        else:
            os.system(
                f'convert "{os.path.join(folder, item)}" -quality 75% -define jpeg:size=1024x1024 -define jpeg:extent=100kb -thumbnail 512x512 -auto-orient "{path}"'
            )


def listfolder(folder: str, title: str):
    if not args.non_interactive:
        pbar.desc = f"Generating html files - {folder}"
        pbar.update(0)
    items: list[str] = os.listdir(folder)
    items.sort()
    images: list[dict] = []
    subfolders: list[dict] = []

    foldername = folder.removeprefix(args.root)
    if foldername != "":
        foldername += "/"
    baseurl = urllib.parse.quote(foldername)

    if not os.path.exists(os.path.join(args.root, ".thumbnails", foldername)):
        os.mkdir(os.path.join(args.root, ".thumbnails", foldername))

    contains_files = False
    for item in items:
        if item not in excludes:
            if os.path.isdir(os.path.join(folder, item)):
                subfolder = {"url": f"{args.webroot}{baseurl}{urllib.parse.quote(item)}", "name": item}
                subfolders.extend([subfolder])
                if item not in args.exclude:
                    listfolder(os.path.join(folder, item), os.path.join(folder, item).removeprefix(args.root))
            else:
                extsplit = os.path.splitext(item)
                if not args.non_interactive:
                    pbar.desc = f"Generating html files - {folder}"
                    pbar.update(0)
                contains_files = True
                if extsplit[1].lower() in args.extensions:
                    image = {
                        "url": f"{args.webroot}{baseurl}{urllib.parse.quote(item)}",
                        "thumbnail": f"{args.webroot}.thumbnails/{baseurl}{urllib.parse.quote(extsplit[0])}.jpg",
                        "name": item,
                    }
                    if not os.path.exists(os.path.join(args.root, ".thumbnails", foldername, item)):
                        thumbnails.append((folder, item))
                    for raw in rawext:
                        if os.path.exists(os.path.join(folder, extsplit[0] + raw)):
                            url = urllib.parse.quote(extsplit[0]) + raw
                            if raw in (".tif", ".tiff"):
                                image["tiff"] = f"{args.webroot}{baseurl}{url}"
                            else:
                                image["raw"] = f"{args.webroot}{baseurl}{url}"
                    images.extend([image])
    if not args.non_interactive:
        pbar.desc = f"Generating html files - {folder}"
        pbar.update(0)
    if len(images) > 0 or (args.fancyfolders and not contains_files) or (args.fancyfolders and args.ignoreotherfiles):
        imagechunks = []
        if len(images) > 0:
            for chunk in np.array_split(images, 8):
                imagechunks.append(chunk)
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
            header = os.path.basename(folder)
            if header == "":
                header = title
            if foldername == "":
                parent = None
            else:
                parent = f"{args.webroot}{urllib.parse.quote(foldername.removesuffix(folder.split('/')[-1] + '/'))}"
            if args.license:
                _license = {
                    "project": args.title,
                    "author": args.author,
                    "type": cclicense.licensenameswitch(args.license),
                    "url": cclicense.licenseurlswitch(args.license),
                    "pics": cclicense.licensepicswitch(args.license),
                }
            else:
                _license = None

            html = environment.get_template("index.html.j2")
            content = html.render(
                title=title,
                favicon=f"{args.webroot}{_FAVICON}",
                stylesheet=f"{args.webroot}{_STYLE}",
                theme=f"{args.webroot}.static/theme.css",
                root=args.webroot,
                parent=parent,
                header=header,
                foldericon=args.foldericon,
                license=_license,
                subdirectories=subfolders,
                images=imagechunks,
            )
            f.write(content)
            f.close()
    else:
        if os.path.exists(os.path.join(folder, "index.html")):
            os.remove(os.path.join(folder, "index.html"))
    if not args.non_interactive:
        pbar.update(1)


def gettotal(folder):
    global total

    if not args.non_interactive:
        pbar.desc = f"Traversing filesystem - {folder}"
        pbar.update(0)

    items: list[str] = os.listdir(folder)
    items.sort()

    for item in items:
        if item not in excludes:
            if os.path.isdir(os.path.join(folder, item)):
                total += 1
                if not args.non_interactive:
                    pbar.update(1)
                if item not in args.exclude:
                    gettotal(os.path.join(folder, item))


def main():
    global rawext
    global total
    global args
    global pbar
    global _cclicense

    total = 0
    # fmt: off
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate html files for static image host.")
    parser.add_argument("-p", "--root", help="Root folder", required=True, type=str, dest="root")
    parser.add_argument("-w", "--webroot", help="Webroot url", required=True, type=str, dest="webroot")
    parser.add_argument("-t", "--title", help="Title", required=True, type=str, dest="title")
    parser.add_argument("-i", "--foldericon", help="Foldericon url", default=_FOLDERICON, required=False, type=str, dest="foldericon", metavar="ICON")
    parser.add_argument("-r", "--regenerate", help="Regenerate thumbnails", action="store_true", default=False, required=False, dest="regenerate")
    parser.add_argument("-n", "--non-interactive", help="Disable interactive mode", action="store_true", default=False, required=False, dest="non_interactive")
    parser.add_argument("-l", "--license", help="License", default=None, required=False, choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], dest="license")
    parser.add_argument("-a", "--author", help="Author", default=_AUTHOR, required=False, type=str, dest="author")
    parser.add_argument("-e", "--extension", help="Extensions to include (multiple --extension are allowed)", required=False, action="append", dest="extensions")
    parser.add_argument("--theme", help="Path to CSS theme file", default=_THEME, required=False, type=str, dest="theme")
    parser.add_argument("--fancyfolders", help="Use fancy folders instead of default apache ones", action="store_true", default=False, required=False, dest="fancyfolders")
    parser.add_argument("--ignore-other-files", help="Ignore other files than the ones specified with the specified extensions -e", action="store_true", default=False, required=False, dest="ignoreotherfiles")
    parser.add_argument("--exclude", help="Exclude folders, only provide the basename of the folders you want to exclude (multiple --exclude are allowed)", required=False, action="append", dest="exclude")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    args = parser.parse_args()
    # fmt: on

    if not args.extensions:
        args.extensions = imgext
    if not args.exclude:
        args.exclude = notlist
    if not args.root.endswith("/"):
        args.root += "/"
    if not args.webroot.endswith("/"):
        args.webroot += "/"
    if not os.path.exists(os.path.join(args.root, ".thumbnails")):
        os.mkdir(os.path.join(args.root, ".thumbnails"))
    tmprawext = []
    for raw in rawext:
        tmprawext.append(raw)
        tmprawext.append(raw.upper())
    rawext = tmprawext

    if os.path.exists(os.path.join(args.root, ".lock")):
        print("Another instance of this program is running.")
        exit()
    try:
        Path(os.path.join(args.root, ".lock")).touch()

        print("Copying static files...")
        shutil.copytree(_STATICFILES, os.path.join(args.root, ".static"), dirs_exist_ok=True)
        shutil.copyfile(args.theme, os.path.join(args.root, ".static", "theme.css"))

        if args.non_interactive:
            print("Generating html files...")
            listfolder(args.root, args.title)

            with Pool(os.cpu_count()) as p:
                print("Generating thumbnails...")
                p.map(thumbnail_convert, thumbnails)
        else:
            pbar = tqdm(desc="Traversing filesystem", unit=" folders", ascii=True, dynamic_ncols=True)
            gettotal(args.root)
            pbar.desc = "Traversing filesystem"
            pbar.update(0)
            pbar.close()

            pbar = tqdm(total=total + 1, desc="Generating html files", unit=" files", ascii=True, dynamic_ncols=True)
            listfolder(args.root, args.title)
            pbar.desc = "Generating html files"
            pbar.update(0)
            pbar.close()

            with Pool(os.cpu_count()) as p:
                for r in tqdm(
                    p.imap_unordered(thumbnail_convert, thumbnails),
                    total=len(thumbnails),
                    desc="Generating thumbnails",
                    unit=" files",
                    ascii=True,
                    dynamic_ncols=True,
                ):
                    pass
    finally:
        os.remove(os.path.join(args.root, ".lock"))


if __name__ == "__main__":
    main()
