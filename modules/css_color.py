import re
import colorsys
from typing import Dict

from modules.logger import logger


def extract_colorscheme(theme_path: str) -> Dict[str, str]:
    """
    Extract color scheme from a CSS theme file.

    Parameters:
    -----------
    theme_path : str
        Path to the CSS theme file.

    Returns:
    --------
    Dict[str, str]
        Dictionary containing color scheme variables and their hexadecimal values.
    """
    logger.info("extracting color scheme from theme file", extra={"theme_path": theme_path})
    pattern = r"--(color[1-4]|bcolor1):\s*(#[0-9a-fA-F]+|rgba?\([^)]*\)|hsla?\([^)]*\)|[a-zA-Z]+);"
    colorscheme = {}

    with open(theme_path, "r", encoding="utf-8") as f:
        filecontent = f.read()

    matches = re.findall(pattern, filecontent)

    for match in matches:
        variable_name = match[0]
        color_value = match[1]
        hex_color_value = css_color_to_hex(color_value)
        colorscheme[variable_name] = hex_color_value
    logger.debug("extracted variable", extra={"variable": variable_name, "value": hex_color_value})
    logger.info("extracted color scheme", extra={"colorscheme": colorscheme})

    return colorscheme


def extract_theme_color(theme_path: str) -> str:
    """
    Extract the theme color from a CSS theme file.

    Parameters:
    -----------
    theme_path : str
        Path to the CSS theme file.

    Returns:
    --------
    str
        The theme color value in hexadecimal format.
    """
    pattern = r"--bcolor1:\s*(#[0-9a-fA-F]+);"
    with open(theme_path, "r", encoding="utf-8") as f:
        filecontent = f.read()
    match = re.search(pattern, filecontent)
    if match:
        color_value = match.group(1)
        hex_color_value = css_color_to_hex(color_value)
        return hex_color_value
    else:
        return ""


def css_color_to_hex(css_color: str) -> str:
    """
    Converts a CSS color string to its hexadecimal representation.

    Args:
        css_color (str): The CSS color string to convert.

    Returns:
        str: The hexadecimal representation of the CSS color.

    Raises:
        ValueError: If the input CSS color string is invalid or unrecognized.

    Example:
        >>> css_color_to_hex('#ff0000')
        '#ff0000'
        >>> css_color_to_hex('rgb(255, 0, 0)')
        '#ff0000'
        >>> css_color_to_hex('hsl(0, 100%, 50%)')
        '#ff0000'
        >>> css_color_to_hex('blue')
        '#0000ff'
    """

    # Helper function to convert RGB tuple to hexadecimal string
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        logger.debug("converting rgb tuple to hex string", extra={"rgb": rgb})
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    # Helper function to convert HSL tuple to RGB tuple
    def hsl_to_rgb(hsl: tuple[int, float, float]) -> tuple[int, int, int]:
        logger.debug("converting hsl tuple to rgb tuple", extra={"hsl": hsl})
        return tuple(round(c * 255) for c in colorsys.hls_to_rgb(hsl[0] / 360, hsl[1] / 100, hsl[2] / 100))

    # Regular expression pattern to match CSS colors
    color_pattern = re.compile(
        r"^(?:(?P<hex>#(?:[0-9a-fA-F]{3}){1,2})|"  # Hexadecimal colors
        r"(?P<rgb>rgba?\((?P<r>\d+%?),\s*(?P<g>\d+%?),\s*(?P<b>\d+%?)(?:,\s*(?P<a>\d*\.?\d+)?)?\))|"  # RGB(a) colors
        r"(?P<hsl>hsla?\((?P<h>\d+),\s*(?P<s>\d+)%,\s*(?P<l>\d+)%(?:,\s*(?P<alpha>\d*\.?\d+)?)?\))|"  # HSL(a) colors
        r"(?P<name>[a-zA-Z]+))$"  # Named colors
    )

    match = color_pattern.match(css_color.strip())

    if not match:
        logger.error("invalid CSS color format", extra={"css_color": css_color})
        raise ValueError("Invalid CSS color format")

    groups = match.groupdict()

    if groups["hex"]:
        hex_color = groups["hex"]
        if len(hex_color) == 4:  # Convert short hex to full hex
            hex_color = "".join([c * 2 for c in hex_color[1:]])
        return hex_color.lower()

    elif groups["rgb"]:
        r = int(groups["r"].rstrip("%")) * 255 // 100 if "%" in groups["r"] else int(groups["r"])
        g = int(groups["g"].rstrip("%")) * 255 // 100 if "%" in groups["g"] else int(groups["g"])
        b = int(groups["b"].rstrip("%")) * 255 // 100 if "%" in groups["b"] else int(groups["b"])
        a = float(groups["a"]) if groups["a"] else 1.0
        if a < 1.0:
            logger.debug("converting rgba color to hex", extra={"color": css_color, "r": r, "g": g, "b": b, "a": a})
            return rgb_to_hex((r, g, b)) + "{:02x}".format(round(a * 255))
        else:
            logger.debug("converting rgb color to hex", extra={"color": css_color, "r": r, "g": g, "b": b})
            return rgb_to_hex((r, g, b))

    elif groups["hsl"]:
        h = int(groups["h"])
        s = int(groups["s"])
        l = int(groups["l"])
        a = float(groups["a"]) if groups["a"] else 1.0
        rgb_color = hsl_to_rgb((h, s, l))
        if a < 1.0:
            logger.debug("converting hsla color to hex", extra={"color": css_color, "hsl": (h, s, l), "a": a})
            return rgb_to_hex(rgb_color) + "{:02x}".format(round(a * 255))
        else:
            logger.debug("converting hsl color to hex", extra={"color": css_color, "hsl": (h, s, l)})
            return rgb_to_hex(rgb_color)

    # fmt: off
    elif groups['name']:
        named_colors = {
            'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aqua': '#00ffff',
            'aquamarine': '#7fffd4', 'azure': '#f0ffff', 'beige': '#f5f5dc',
            'bisque': '#ffe4c4', 'black': '#000000', 'blanchedalmond': '#ffebcd',
            'blue': '#0000ff', 'blueviolet': '#8a2be2', 'brown': '#a52a2a',
            'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00',
            'chocolate': '#d2691e', 'coral': '#ff7f50', 'cornflowerblue': '#6495ed',
            'cornsilk': '#fff8dc', 'crimson': '#dc143c', 'cyan': '#00ffff',
            'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b',
            'darkgray': '#a9a9a9', 'darkgreen': '#006400', 'darkkhaki': '#bdb76b',
            'darkmagenta': '#8b008b', 'darkolivegreen': '#556b2f', 'darkorange': '#ff8c00',
            'darkorchid': '#9932cc', 'darkred': '#8b0000', 'darksalmon': '#e9967a',
            'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b', 'darkslategray': '#2f4f4f',
            'darkturquoise': '#00ced1', 'darkviolet': '#9400d3', 'deeppink': '#ff1493',
            'deepskyblue': '#00bfff', 'dimgray': '#696969', 'dodgerblue': '#1e90ff',
            'firebrick': '#b22222', 'floralwhite': '#fffaf0', 'forestgreen': '#228b22',
            'fuchsia': '#ff00ff', 'gainsboro': '#dcdcdc', 'ghostwhite': '#f8f8ff',
            'gold': '#ffd700', 'goldenrod': '#daa520', 'gray': '#808080', 'green': '#008000',
            'greenyellow': '#adff2f', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4',
            'indianred': '#cd5c5c', 'indigo': '#4b0082', 'ivory': '#fffff0',
            'khaki': '#f0e68c', 'lavender': '#e6e6fa', 'lavenderblush': '#fff0f5',
            'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6',
            'lightcoral': '#f08080', 'lightcyan': '#e0ffff', 'lightgoldenrodyellow': '#fafad2',
            'lightgray': '#d3d3d3', 'lightgreen': '#90ee90', 'lightpink': '#ffb6c1',
            'lightsalmon': '#ffa07a', 'lightseagreen': '#20b2aa', 'lightskyblue': '#87cefa',
            'lightslategray': '#778899', 'lightsteelblue': '#b0c4de', 'lightyellow': '#ffffe0',
            'lime': '#00ff00', 'limegreen': '#32cd32', 'linen': '#faf0e6', 'magenta': '#ff00ff',
            'maroon': '#800000', 'mediumaquamarine': '#66cdaa', 'mediumblue': '#0000cd',
            'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db', 'mediumseagreen': '#3cb371',
            'mediumslateblue': '#7b68ee', 'mediumspringgreen': '#00fa9a',
            'mediumturquoise': '#48d1cc', 'mediumvioletred': '#c71585', 'midnightblue': '#191970',
            'mintcream': '#f5fffa', 'mistyrose': '#ffe4e1', 'moccasin': '#ffe4b5',
            'navajowhite': '#ffdead', 'navy': '#000080', 'oldlace': '#fdf5e6', 'olive': '#808000',
            'olivedrab': '#6b8e23', 'orange': '#ffa500', 'orangered': '#ff4500',
            'orchid': '#da70d6', 'palegoldenrod': '#eee8aa', 'palegreen': '#98fb98',
            'paleturquoise': '#afeeee', 'palevioletred': '#db7093', 'papayawhip': '#ffefd5',
            'peachpuff': '#ffdab9', 'peru': '#cd853f', 'pink': '#ffc0cb', 'plum': '#dda0dd',
            'powderblue': '#b0e0e6', 'purple': '#800080', 'rebeccapurple': '#663399',
            'red': '#ff0000', 'rosybrown': '#bc8f8f', 'royalblue': '#4169e1', 'saddlebrown': '#8b4513',
            'salmon': '#fa8072', 'sandybrown': '#f4a460', 'seagreen': '#2e8b57', 'seashell': '#fff5ee',
            'sienna': '#a0522d', 'silver': '#c0c0c0', 'skyblue': '#87ceeb', 'slateblue': '#6a5acd',
            'slategray': '#708090', 'snow': '#fffafa', 'springgreen': '#00ff7f', 'steelblue': '#4682b4',
            'tan': '#d2b48c', 'teal': '#008080', 'thistle': '#d8bfd8', 'tomato': '#ff6347',
            'turquoise': '#40e0d0', 'violet': '#ee82ee', 'wheat': '#f5deb3', 'white': '#ffffff',
            'whitesmoke': '#f5f5f5', 'yellow': '#ffff00', 'yellowgreen': '#9acd32'
        }
        logger.debug("parsing css color string", extra={"css_color": css_color})
        return named_colors[groups['name'].lower()]
    # fmt: on

    logger.error("invalid CSS color format", extra={"css_color": css_color})
    raise ValueError("Invalid CSS color format")
