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

## Requirements

- Python 3.x
- `numpy` library
- `tqdm` library

## Installation

Install the required libraries using pip:

```sh
pip install numpy tqdm
```

## Usage

The script supports several command-line options to customize its behavior. Below is the list of available options:

```sh
./generate_html.py [-h] [-f ROOT] [-w WEBROOT] [-i ICON] [-r] [-n] [--fancyfolders] [-l LICENSE] [-a AUTHOR] [-t TITLE]
```

### Options

- `-h, --help`: Show the help message and exit.
- `-p ROOT, --root ROOT`: Specify the root folder where the images are stored. Default is `/data/pictures/`.
- `-w WEBROOT, --webroot WEBROOT`: Specify the web root URL where the images will be accessible. Default is `https://pictures.example.com/`.
- `-i ICON, --foldericon ICON`: Specify the URL for the folder icon. Default is `https://www.svgrepo.com/show/400249/folder.svg`.
- `-r, --regenerate`: Regenerate thumbnails even if they already exist.
- `-n, --non-interactive`: Disable interactive mode, which is useful for automated workflows.
- `--fancyfolders`: Use fancy folders instead of the default Apache directory listing.
- `-l LICENSE, --license LICENSE`: Specify a license for the content. Options are `cc-zero`, `cc-by`, `cc-by-sa`, `cc-by-nd`, `cc-by-nc`, `cc-by-nc-sa`, and `cc-by-nc-nd`.
- `-a AUTHOR, --author AUTHOR`: Specify the author of the content.
- `-t TITLE, --title TITLE`: Specify the title for the root directory HTML file.

### Example

To generate HTML files and thumbnails for a directory `/data/pictures` and host them on `https://pictures.example.com`, run:

```sh
./generate_html.py -f /data/pictures -w https://pictures.example.com
```

To regenerate thumbnails and run in non-interactive mode:

```sh
./generate_html.py -f /data/pictures -w https://pictures.example.com -r -n
```

To include a license, author, and custom title:

```sh
./generate_html.py -f /data/pictures -w https://pictures.example.com -l cc-by -a "John Doe" -t "My Photo Gallery"
```

## Notes

- The root and webroot paths must point to the same folder, one on the filesystem and one on the webserver. Use absolute paths.
- Ensure that ImageMagick is installed and accessible in your system for thumbnail generation.
- The script assumes that the preview thumbnails will be stored in a `.previews` subdirectory within the root folder.

## License

This project is licensed under the AGPL-3.0 License. See the `LICENSE` file for details.
