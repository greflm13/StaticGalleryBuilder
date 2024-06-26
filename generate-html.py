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
    images: list[str] = []
    subfolders: list[str] = []

    if not os.path.exists(os.path.join(root, ".previews", folder.removeprefix(root))):
        os.mkdir(os.path.join(root, ".previews", folder.removeprefix(root)))

    with open(os.path.join(folder, "list.txt"), "w", encoding="utf-8") as f:
        for item in items:
            if item != "Galleries" and item != ".previews":
                if os.path.isdir(os.path.join(folder, item)):
                    subfolders.extend([f'<b><a href="{webroot}{folder.removeprefix(root)}/{item}">{item}</a></b><br>'])
                    listfolder(os.path.join(folder, item))
                else:
                    if os.path.splitext(item)[1] in imgext:
                        images.extend([f'<img href="{webroot}{folder.removeprefix(root)}/{item}">{item}</img><br>'])
                        if not os.path.exists(os.path.join(root, ".previews", folder.removeprefix(root), item)):
                            # os.system(f'magick {os.path.join(folder, item)} -resize 1024x768! {os.path.join(root, ".previews", folder.removeprefix(root), item)}')
                            print(f'magick {os.path.join(folder, item)} -resize 1024x768! {os.path.join(root, ".previews", folder.removeprefix(root), item)}')
                        for raw in rawext:
                            if os.path.exists(os.path.join(folder, os.path.splitext(item)[0] + raw)):
                                images.extend([f'<a href="{webroot}{folder.removeprefix(root)}/{os.path.splitext(item)[0]}{raw}">RAW</a><br>'])
        for image in images:
            f.write(image)
            f.write("\n")
        for subfolder in subfolders:
            f.write(subfolder)
            f.write("\n")
        f.close()


def main():
    global root
    global webroot
    if not root.endswith("/"):
        root += "/"
    if not webroot.endswith("/"):
        webroot += "/"
    listfolder(root)
    # @TODO: write actual html files (and css 🙄)


if __name__ == "__main__":
    main()
