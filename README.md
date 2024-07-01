# generate_html.py

`generate_html.py` is a Python script designed to generate static HTML files for hosting images on a web server. It traverses a specified root directory, creates thumbnail previews for images, and generates corresponding HTML files to display the images and subfolders in a user-friendly format.

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

## Requirements

- Python 3.x
- `numpy` library
- `tqdm` library
- `Jinja2` library
- `ImageMagick`

## Installation

Install the required libraries using pip:

```sh
pip install numpy tqdm Jinja2
```

## Usage

The script supports several command-line options to customize its behavior. Below is the list of available options:

```sh
./generate_html.py [-h] -p ROOT -w WEBROOT -t TITLE [-i ICON] [-r] [-n] [--use-fancy-folders] [-l LICENSE] [-a AUTHOR] [-e EXTENSION] [--theme-path THEME] [--ignore-other-files] [--exclude-folders EXCLUDE]
```

### Options

- `-h, --help`: Show the help message and exit.
- `-p ROOT, --root-directory ROOT`: Specify the root folder where the images are stored. This option is required.
- `-w WEBROOT, --web-root-url WEBROOT`: Specify the web root URL where the images will be accessible. This option is required.
- `-t TITLE, --site-title TITLE`: Specify the title for the root directory HTML file. This option is required.
- `-i ICON, --folder-icon-url ICON`: Specify the URL for the folder icon. Default is `https://www.svgrepo.com/show/400249/folder.svg`.
- `-r, --regenerate-thumbnails`: Regenerate thumbnails even if they already exist.
- `-n, --non-interactive-mode`: Disable interactive mode, which is useful for automated workflows.
- `--use-fancy-folders`: Use fancy folders instead of the default Apache directory listing.
- `-l LICENSE, --license-type LICENSE`: Specify a license for the content. Options are `cc-zero`, `cc-by`, `cc-by-sa`, `cc-by-nd`, `cc-by-nc`, `cc-by-nc-sa`, and `cc-by-nc-nd`.
- `-a AUTHOR, --author-name AUTHOR`: Specify the author of the content. Default is "Author".
- `-e EXTENSION, --file-extensions EXTENSION`: Specify file extensions to include. This option can be used multiple times.
- `--theme-path THEME`: Specify the path to a custom CSS theme file. Default is `themes/default.css`.
- `--ignore-other-files`: Ignore files other than those specified by the included extensions.
- `--exclude-folder EXCLUDE`: Exclude folders from processing. Only provide the basename of the folders you want to exclude. This option can be used multiple times.

### Example

To generate HTML files and thumbnails for a directory `/data/pictures` and host them on `https://pictures.example.com`, run:

```sh
./generate_html.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery"
```

To regenerate thumbnails and run in non-interactive mode:

```sh
./generate_html.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" -r -n
```

To include a license and author:

```sh
./generate_html.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" -l cc-by -a "John Doe"
```

To specify a custom CSS theme:

```sh
./generate_html.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" --theme-path custom_theme.css
```

To exclude specific folders and specify file extensions:

```sh
./generate_html.py -p /data/pictures -w https://pictures.example.com -t "My Photo Gallery" --exclude-folder Archives --exclude-folders Temp -e .jpg -e .jpeg -e .png
```

## Notes

- The root and web root paths must point to the same folder, one on the filesystem and one on the web server. Use absolute paths.
- Ensure that ImageMagick is installed and accessible in your system for thumbnail generation.
- The script generates the preview thumbnails in a `.thumbnails` subdirectory within the root folder.
- The `.lock` file prevents multiple instances of the script from running simultaneously. Make sure to remove it if the script terminates unexpectedly.

## License

This project is licensed under the AGPL-3.0 License. See the [LICENSE](LICENSE) file for details.
