import os
import shutil
from typing import List, Dict
from PIL import Image
from jinja2 import Environment, FileSystemLoader

# Attempt to import cairosvg for SVG support, set flag based on success
try:
    import cairosvg
    from io import BytesIO

    SVGSUPPORT = True
except ImportError:
    SVGSUPPORT = False

from modules.argumentparser import Args
from modules.css_color import css_color_to_hex, extract_theme_color, extract_colorscheme

# Define constants for static files directory and icon sizes
if __package__ == None:
    __package__ = ""
STATIC_FILES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__).removesuffix(__package__)), "files")
ICON_SIZES = ["36x36", "48x48", "72x72", "96x96", "144x144", "192x192", "512x512"]

# Initialize Jinja2 environment for template rendering
env = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__).removesuffix(__package__)), "templates")))


class Icon:
    src: str
    type: str
    sizes: str
    purpose: str


def render_svg_icon(colorscheme: Dict[str, str], iconspath: str) -> str:
    """
    Render an SVG icon using the provided color scheme.

    Parameters:
    -----------
    colorscheme : Dict[str, str]
        Dictionary containing color scheme variables and their values.
    iconspath : str
        Path to the directory where the icon will be saved.

    Returns:
    --------
    str
        The rendered SVG content.
    """
    svg = env.get_template("icon.svg.j2")
    content = svg.render(colorscheme=colorscheme)
    with open(os.path.join(iconspath, "icon.svg"), "w+", encoding="utf-8") as f:
        f.write(content)
    return content


def save_png_icon(content: str, iconspath: str) -> None:
    """
    Save the rendered SVG content as a PNG icon.

    Parameters:
    -----------
    content : str
        The rendered SVG content.
    iconspath : str
        Path to the directory where the PNG icon will be saved.
    """
    tmpimg = BytesIO()
    cairosvg.svg2png(bytestring=content, write_to=tmpimg)
    with Image.open(tmpimg) as iconfile:
        iconfile.save(os.path.join(iconspath, "icon.png"))


def generate_favicon(iconspath: str, root_directory: str) -> None:
    """
    Generate a favicon from a PNG icon using ImageMagick.

    Parameters:
    -----------
    iconspath : str
        Path to the directory containing the PNG icon.
    root_directory : str
        Root directory of the project where the favicon will be saved.
    """
    command = f'magick {os.path.join(iconspath, "icon.png")} -define icon:auto-resize=16,32,48,64,72,96,144,192 {os.path.join(root_directory, ".static", "favicon.ico")}'
    if not shutil.which("magick"):
        command = f'convert {os.path.join(iconspath, "icon.png")} -define icon:auto-resize=16,32,48,64,72,96,144,192 {os.path.join(root_directory, ".static", "favicon.ico")}'
    os.system(command)


def icons(_args: Args) -> None:
    """
    Generate icons and save them in the static directory.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    """
    print("Generating icons...")
    iconspath = os.path.join(_args.root_directory, ".static", "icons")
    colorscheme = extract_colorscheme(_args.theme_path)
    content = render_svg_icon(colorscheme, iconspath)
    if not SVGSUPPORT:
        print("Please install cairosvg to generate favicon from svg icon.")
        return
    save_png_icon(content, iconspath)
    generate_favicon(iconspath, _args.root_directory)


def render_manifest_json(_args: Args, icon_list: List[Icon], colors: Dict[str, str]) -> None:
    """
    Render the manifest.json file for the web application.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    icon_list : List[Icon]
        List of icons to be included in the manifest.
    colors : Dict[str, str]
        Dictionary containing color scheme and theme color.
    """
    manifest = env.get_template("manifest.json.j2")
    content = manifest.render(
        name=_args.web_root_url.replace("https://", "").replace("http://", "").replace("/", ""),
        short_name=_args.site_title,
        icons=icon_list,
        background_color=colors["bcolor1"],
        theme_color=colors["theme_color"],
    )
    with open(os.path.join(_args.root_directory, ".static", "manifest.json"), "w", encoding="utf-8") as f:
        f.write(content)


def create_icons_from_svg(files: List[str], iconspath: str, _args: Args) -> List[Icon]:
    """
    Create icons from an SVG file.

    Parameters:
    -----------
    files : List[str]
        List of files in the icons directory.
    iconspath : str
        Path to the directory where the icons will be saved.
    _args : Args
        Parsed command-line arguments.

    Returns:
    --------
    List[Icon]
        List of icons created from the SVG file.
    """
    svg = [file for file in files if file.endswith(".svg")][0]
    icon_list = [
        {"src": f"{_args.web_root_url}.static/icons/{svg}", "type": "image/svg+xml", "sizes": "512x512", "purpose": "maskable"},
        {"src": f"{_args.web_root_url}.static/icons/{svg}", "type": "image/svg+xml", "sizes": "512x512", "purpose": "any"},
    ]
    for size in ICON_SIZES:
        tmpimg = BytesIO()
        sizes = size.split("x")
        iconpath = os.path.join(iconspath, os.path.splitext(svg)[0] + "-" + size + ".png")
        cairosvg.svg2png(
            url=os.path.join(iconspath, svg),
            write_to=tmpimg,
            output_width=int(sizes[0]),
            output_height=int(sizes[1]),
            scale=1,
        )
        with Image.open(tmpimg) as iconfile:
            iconfile.save(iconpath, format="PNG")
        icon_list.append(
            {
                "src": f"{_args.web_root_url}.static/icons/{os.path.splitext(svg)[0]}-{size}.png",
                "sizes": size,
                "type": "image/png",
                "purpose": "maskable",
            }
        )
        icon_list.append(
            {
                "src": f"{_args.web_root_url}.static/icons/{os.path.splitext(svg)[0]}-{size}.png",
                "sizes": size,
                "type": "image/png",
                "purpose": "any",
            }
        )
    return icon_list


def create_icons_from_png(iconspath: str, web_root_url: str) -> List[Icon]:
    """
    Create icons from PNG files.

    Parameters:
    -----------
    iconspath : str
        Path to the directory containing the PNG icons.
    web_root_url : str
        Base URL of the web root for the image hosting site.

    Returns:
    --------
    List[Icon]
        List of icons created from PNG files.
    """
    icon_list = []
    for icon in os.listdir(iconspath):
        if not icon.endswith(".png"):
            continue
        with Image.open(os.path.join(iconspath, icon)) as iconfile:
            iconsize = f"{iconfile.size[0]}x{iconfile.size[1]}"
        icon_list.append({"src": f"{web_root_url}.static/icons/{icon}", "sizes": iconsize, "type": "image/png", "purpose": "maskable"})
        icon_list.append({"src": f"{web_root_url}.static/icons/{icon}", "sizes": iconsize, "type": "image/png", "purpose": "any"})
    return icon_list


def webmanifest(_args: Args) -> None:
    """
    Generate the web manifest file for the application.

    Parameters:
    -----------
    _args : Args
        Parsed command-line arguments.
    """
    iconspath = os.path.join(_args.root_directory, ".static", "icons")
    files = os.listdir(iconspath)
    icon_list = (
        create_icons_from_svg(files, iconspath, _args)
        if SVGSUPPORT and any(file.endswith(".svg") for file in files)
        else create_icons_from_png(iconspath, _args.web_root_url)
    )

    if not icon_list:
        print("No icons found in the static/icons folder!")
        return

    colorscheme = extract_colorscheme(os.path.join(_args.root_directory, ".static", "theme.css"))
    colorscheme["theme_color"] = extract_theme_color(os.path.join(_args.root_directory, ".static", "theme.css"))
    render_manifest_json(_args, icon_list, colorscheme)
