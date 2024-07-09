# StaticGalleryBuilder (SGB)

`builder.py` is a Python script designed to generate static HTML files for hosting images on a web server. It traverses a specified root directory, creates thumbnail previews for images, and generates corresponding HTML files to display the images and subfolders in a user-friendly format.

## Features

- **Generate HTML Files:** The script creates HTML files for each folder in the specified root directory.
- **Thumbnail Creation:** It generates thumbnail previews for supported image formats.
- **Folder Navigation:** The HTML files include navigation links to subfolders.
- **Responsive Design:** The generated HTML uses responsive design techniques to ensure the gallery looks good on different screen sizes.
- **Non-Interactive Mode:** It can run in a non-interactive mode suitable for automated workflows.
- **License Information:** Optionally include license information in the HTML files.
- **Custom Author and Title:** Allows specifying a custom author and title for the HTML files.
- **CSS Theme Support:** Allows specifying a custom CSS theme file for the HTML files.
- **Folder Exclusion:** Ability to exclude specific folders from processing.
- **Selective File Extensions:** Ability to specify which file extensions to include in the gallery.
- **Ignore Other Files:** Option to ignore files other than those specified by the included extensions.
- **Info Tooltips:** Display additional information as tooltips for images if an `info` file is present in the directory.
- **Generate Web Manifest:** Ability to generate a web manifest file for PWA (Progressive Web App) support.

## Requirements

- Python 3.x
- `numpy` library
- `tqdm` library
- `Jinja2` library
- `Pillow` library
- `rich_argparse` library
- `cairosvg` library (for SVG to PNG icon conversion)

## Installation

Install the required libraries using pip:

```sh
pip install numpy tqdm Jinja2 Pillow rich-argparse cairosvg
```

## Usage

The script supports several command-line options to customize its behavior. Below is the list of available options:

![help-preview](help.svg)

### Options

- `-h, --help`: Show the help message and exit.
- `-p ROOT, --root-directory ROOT`: Specify the root folder where the images are stored. This option is required.
- `-w URL, --web-root-url URL`: Specify the base URL for the web root of the image hosting site. This option is required.
- `-t TITLE, --site-title TITLE`: Specify the title of the image hosting site. This option is required.
- `-r, --regenerate-thumbnails`: Regenerate thumbnails even if they already exist.
- `-n, --non-interactive-mode`: Run in non-interactive mode, disabling progress bars.
- `-l LICENSE, --license-type LICENSE`: Specify the license type for the images. Choices are `cc-zero`, `cc-by`, `cc-by-sa`, `cc-by-nd`, `cc-by-nc`, `cc-by-nc-sa`, and `cc-by-nc-nd`.
- `-a AUTHOR, --author-name AUTHOR`: Specify the name of the author of the images. Default is "Author".
- `-e EXTENSION, --file-extensions EXTENSION`: Specify the file extensions to include. This option can be specified multiple times.
- `--theme-path PATH`: Specify the path to the CSS theme file. Default is the provided default theme.
- `--use-fancy-folders`: Enable fancy folder view instead of the default Apache directory listing.
- `--ignore-other-files`: Ignore files that do not match the specified extensions.
- `--exclude-folder FOLDER`: Specify folders to exclude from processing. This option can be specified multiple times.
- `--version`: Show the version number of the script and exit.
- `-m, --web-manifest`: Generate a web manifest file.

### Examples

To generate HTML files and thumbnails for a directory `/data/pictures` and host them on `https://pictures.example.com`, run:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery"
```

To regenerate thumbnails and run in non-interactive mode:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" -r -n
```

To include a license and author:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" -l cc-by -a "John Doe"
```

To specify a custom CSS theme:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" --theme-path custom_theme.css
```

To exclude specific folders and specify file extensions:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" --exclude-folder Archives --exclude-folder Temp -e .jpg -e .jpeg -e .png
```

To generate a web manifest file:

```sh
./builder.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" -m
```

## Notes

- The root and web root paths must point to the same folder, one on the filesystem and one on the web server. Use absolute paths.
- The script generates the preview thumbnails in a `.thumbnails` subdirectory within the root folder.
- The `.lock` file prevents multiple instances of the script from running simultaneously. Make sure to remove it if the script terminates unexpectedly.

## License

This project is licensed under the AGPL-3.0 License. See the [LICENSE](LICENSE) file for details.
