#!/usr/bin/env python3
import os
import argparse
import urllib.parse
from multiprocessing import Pool
from string import Template
import numpy as np

"""
root and webroot must point to the same folder, one on filesystem and one on the webserver. Use absolut paths, e.g. /data/pictures/ and https://pictures.example.com/
"""

_ROOT = "/mnt/nfs/pictures/"
_WEBROOT = "https://pictures.sorogon.eu/"
_FOLDERICON = "https://www.svgrepo.com/show/400249/folder.svg"
_ROOTTITLE = "Pictures"
imgext = [".jpg", ".jpeg"]
rawext = [".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".data", ".dcs", ".dcr", ".dng", ".drf", ".eip", ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf", ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".tif", ".tiff", ".x3f"]

thumbnails: list[tuple[str, str]] = []

HTMLHEADER = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <style>
      * {
        box-sizing: border-box;
      }
      
      body {
        margin: 0;
        font-family: Arial;
      }
      
      .folders {
        text-align: center;
        display: -ms-flexbox; /* IE10 */
        display: flex;
        -ms-flex-wrap: wrap; /* IE10 */
        flex-wrap: wrap;
        justify-content: space-evenly;
      }

      .folders figure {
        margin-bottom: 32px;
      }

      .header h1 {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
      }

      .folders img {
        width: 100px;
        vertical-align: middle;
      }
      
      .row {
        display: -ms-flexbox; /* IE10 */
        display: flex;
        -ms-flex-wrap: wrap; /* IE10 */
        flex-wrap: wrap;
        padding: 0 2px;
      }

      figure {
        margin: 0;
      }
      
      /* Create four equal columns that sits next to each other */
      .column {
        -ms-flex: 12.5%; /* IE10 */
        flex: 12.5%;
        max-width: 12.5%;
        padding: 0 4px;
      }
      
      .column img {
        margin-top: 20px;
        vertical-align: middle;
        width: 100%;
      }
      
      /* Responsive layout - makes a four column-layout instead of eight columns */
      @media screen and (max-width: 1000px) {
        .column {
          -ms-flex: 25%;
          flex: 25%;
          max-width: 25%;
        }
        .folders img {
          width: 80px;
        }
      }
      
      /* Responsive layout - makes a two column-layout instead of four columns */
      @media screen and (max-width: 800px) {
        .column {
          -ms-flex: 50%;
          flex: 50%;
          max-width: 50%;
        }
        .folders img {
          width: 60px;
        }
      }
      
      /* Responsive layout - makes the two columns stack on top of each other instead of next to each other */
      @media screen and (max-width: 600px) {
        .column {
          -ms-flex: 100%;
          flex: 100%;
          max-width: 100%;
        }
        .folders img {
          width: 50px;
        }
      }

      .caption {
        padding-top: 4px;
        text-align: center;
        font-style: italic;
        font-size: 12px;
        width: 100%;
        display: block;
      }
    </style>
  </head>
  <body>
"""


def thumbnail_convert(arguments: tuple[str, str]):
    folder, item = arguments
    if not os.path.exists(os.path.join(args.root, ".previews", folder.removeprefix(args.root), item)) and args.regenerate is False:
        os.system(f'magick "{os.path.join(folder, item)}" -quality 75% -define jpeg:size=1024x1024 -define jpeg:extent=100kb -thumbnail 512x512 -auto-orient "{os.path.join(args.root, ".previews", folder.removeprefix(args.root), item)}"')


def listfolder(folder: str, title: str):
    items: list[str] = os.listdir(folder)
    items.sort()
    images: list[str] = []
    subfolders: list[str] = []

    if not os.path.exists(os.path.join(args.root, ".previews", folder.removeprefix(args.root))):
        os.mkdir(os.path.join(args.root, ".previews", folder.removeprefix(args.root)))

    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        temp_obj = Template(HTMLHEADER)
        f.write(temp_obj.substitute(title=title))
        for item in items:
            if item != "Galleries" and item != ".previews":
                if os.path.isdir(os.path.join(folder, item)):
                    subfolders.extend([f'<figure><a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(item)}"><img src="{args.foldericon}" alt="Folder icon"/></a><figcaption><a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(item)}">{item}</a></figcaption></figure>'])
                    listfolder(os.path.join(folder, item), item)
                else:
                    if os.path.splitext(item)[1].lower() in imgext:
                        image = f'<figure><a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(item)}"><img src="{args.webroot}.previews/{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(item)}" alt="{item}"/></a><figcaption class="caption">{item}'
                        if not os.path.exists(os.path.join(args.root, ".previews", folder.removeprefix(args.root), item)):
                            thumbnails.append((folder, item))
                        for raw in rawext:
                            if os.path.exists(os.path.join(folder, os.path.splitext(item)[0] + raw)):
                                if raw == ".tif" or raw == ".tiff":
                                    image += f': <a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">TIFF</a>'
                                else:
                                    image += f': <a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">RAW</a>'
                            elif os.path.exists(os.path.join(folder, os.path.splitext(item)[0] + raw.upper())):
                                if raw == ".tif" or raw == ".tiff":
                                    image += f': <a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">TIFF</a>'
                                else:
                                    image += f': <a href="{args.webroot}{urllib.parse.quote(folder.removeprefix(args.root))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">RAW</a>'
                        image += "</figcaption></figure>"
                        images.extend([image])
        f.write('    <div class="header">\n')
        f.write(f"      <h1>{title}</h1>\n")
        f.write('      <div class="folders">\n')
        for subfolder in subfolders:
            f.write(subfolder)
            f.write("\n")
        f.write("      </div>\n")
        f.write("    </div>\n")
        f.write('    <div class="row">\n')
        for chunk in np.array_split(images, 8):
            f.write('      <div class="column">\n')
            for image in chunk:
                f.write(f"        {image}\n")
            f.write("      </div>\n")
        f.write("    </div>\n")
        f.write("  </body>\n</html>")
        f.close()


def main():
    global args
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate html files for static image host.")
    parser.add_argument("-f", "--root", help="Root folder", default=_ROOT, required=False, type=str, dest="root")
    parser.add_argument("-w", "--webroot", help="Webroot url", default=_WEBROOT, required=False, type=str, dest="webroot")
    parser.add_argument("-i", "--foldericon", help="Foldericon url", default=_FOLDERICON, required=False, type=str, dest="foldericon", metavar="ICON")
    parser.add_argument("-r", "--regenerate", help="Regenerate thumbnails", action="store_true", default=False, required=False, dest="regenerate")
    args = parser.parse_args()

    if not args.root.endswith("/"):
        args.root += "/"
    if not args.webroot.endswith("/"):
        args.webroot += "/"
    if not os.path.exists(os.path.join(args.root, ".previews")):
        os.mkdir(os.path.join(args.root, ".previews"))
    print("Generating html files...")
    listfolder(args.root, _ROOTTITLE)

    with Pool(os.cpu_count()) as p:
        print("Generating thumbnails...")
        p.map(thumbnail_convert, thumbnails)


if __name__ == "__main__":
    main()
