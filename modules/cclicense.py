class License:
    """
    A class to represent a Creative Commons license.

    Attributes:
    -----------
    project : str
        The name of the project.
    author : str
        The author of the work.
    type : str
        The type of the license.
    url : str
        The URL of the license.
    pics : list of str
        A list of URLs to the license images.
    """

    project: str
    author: str
    type: str
    url: str
    pics: list[str]


def licenseurlswitch(cclicense: str) -> str:
    """
    Get the URL for a given Creative Commons license type.

    Parameters:
    -----------
    cclincense : str
        The license type identifier.

    Returns:
    --------
    str
        The URL associated with the specified license type.
    """
    switch = {
        "cc-zero": "https://creativecommons.org/publicdomain/zero/1.0/",
        "cc-by": "https://creativecommons.org/licenses/by/4.0/",
        "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
        "cc-by-nd": "https://creativecommons.org/licenses/by-nd/4.0/",
        "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/",
        "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "cc-by-nc-nd": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    }

    return switch.get(cclicense, "")


def licensenameswitch(cclicense: str) -> str:
    """
    Get the name for a given Creative Commons license type.

    Parameters:
    -----------
    cclincense : str
        The license type identifier.

    Returns:
    --------
    str
        The name associated with the specified license type.
    """
    switch = {
        "cc-zero": "CC0 1.0",
        "cc-by": "CC BY 4.0",
        "cc-by-sa": "CC BY-SA 4.0",
        "cc-by-nd": "CC BY-ND 4.0",
        "cc-by-nc": "CC BY-NC 4.0",
        "cc-by-nc-sa": "CC BY-NC-SA 4.0",
        "cc-by-nc-nd": "CC BY-NC-ND 4.0",
    }

    return switch.get(cclicense, "")


def licensepicswitch(cclicense: str) -> list[str]:
    """
    Get the list of image URLs for a given Creative Commons license type.

    Parameters:
    -----------
    cclincense : str
        The license type identifier.

    Returns:
    --------
    list of str
        A list of URLs to the license images.
    """
    switch = {
        "cc-zero": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/zero.svg",
        ],
        "cc-by": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
        ],
        "cc-by-sa": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/sa.svg",
        ],
        "cc-by-nd": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nd.svg",
        ],
        "cc-by-nc": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nc.svg",
        ],
        "cc-by-nc-sa": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/sa.svg",
        ],
        "cc-by-nc-nd": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nd.svg",
        ],
    }

    return switch.get(cclicense, [])
