#!/usr/bin/env python3
import sys
import os

"""
root and webroot must point to the same folder, one on filesystem and one on the webserver. Use absolut paths, e.g. /data/pictures/ and https://pictures.example.com/
"""

root = "/mnt/small-data/nfs/pictures/"
webroot = "https://pictures.sorogon.eu/"
imgext = [".jpg", ".jpeg", ".JPG", ".JPEG"]
rawext = [".ARW", ".tif", ".tiff", ".TIF", ".TIFF"]


def listfolder(folder: str):
    items: list[str] = os.listdir(folder)
    items.sort()
    for item in items:
        if item != "Galleries" and item != ".previews":
            if os.path.isdir(os.path.join(folder, item)):
                print(f'<b><a href="{webroot}{folder.removeprefix(root)}/{item}">{item}</a></b><br>')
                listfolder(os.path.join(folder, item))
            else:
                if os.path.splitext(item)[1] in imgext:
                    print(f'<img href="{webroot}{folder.removeprefix(root)}/{item}">{item}</img><br>')
                    for raw in rawext:
                        if os.path.exists(os.path.join(folder, os.path.splitext(item)[0] + raw)):
                            print(f'<a href="{webroot}{folder.removeprefix(root)}/{os.path.splitext(item)[0]}{raw}">RAW</a><br>')


def main():
    if not root.endswith("/"):
        root += "/"
    if not webroot.endswith("/"):
        webroot += "/"
    listfolder(root)
    # @TODO: write actual html files (and css 🙄)

if __name__ == "__main__":
    main()
