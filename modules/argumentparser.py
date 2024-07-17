from typing import List, Optional
import os
import argparse
from rich_argparse import RichHelpFormatter, HelpPreviewAction


if __package__ == None:
    __package__ = ""
DEFAULT_THEME_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__).removesuffix(__package__)), "templates", "default.css")
DEFAULT_AUTHOR = "Author"


class Args:
    """
    A class to store command-line arguments for the script.

    Attributes:
    -----------
    author_name : str
        The name of the author of the images.
    exclude_folders : List[str]
        A list of folders to exclude from processing.
    file_extensions : List[str]
        A list of file extensions to include.
    generate_webmanifest : bool
        Whether to generate a web manifest file.
    ignore_other_files : bool
        Whether to ignore files that do not match the specified extensions.
    license_type : Optional[str]
        The type of license for the images.
    non_interactive_mode : bool
        Whether to run in non-interactive mode.
    regenerate_thumbnails : bool
        Whether to regenerate thumbnails even if they already exist.
    root_directory : str
        The root directory containing the images.
    site_title : str
        The title of the image hosting site.
    theme_path : str
        The path to the CSS theme file.
    use_fancy_folders : bool
        Whether to enable fancy folder view.
    web_root_url : str
        The base URL of the web root for the image hosting site.
    """

    author_name: str
    exclude_folders: List[str]
    file_extensions: List[str]
    generate_webmanifest: bool
    ignore_other_files: bool
    license_type: Optional[str]
    non_interactive_mode: bool
    regenerate_thumbnails: bool
    root_directory: str
    site_title: str
    theme_path: str
    use_fancy_folders: bool
    web_root_url: str


def parse_arguments(version: str) -> Args:
    """
    Parse command-line arguments.

    Parameters:
    -----------
    version : str
        The version of the program.

    Returns:
    --------
    Args
        An instance of the Args class containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate HTML files for a static image hosting website.", formatter_class=RichHelpFormatter)
    parser.add_argument("--exclude-folder", help="Folders to exclude from processing, globs supported (can be specified multiple times).", action="append", dest="exclude_folders", metavar="FOLDER")
    parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg")
    parser.add_argument("--ignore-other-files", help="Ignore files that do not match the specified extensions.", action="store_true", default=False, dest="ignore_other_files")
    parser.add_argument("--theme-path", help="Path to the CSS theme file.", default=DEFAULT_THEME_PATH, type=str, dest="theme_path", metavar="PATH")
    parser.add_argument("--use-fancy-folders", help="Enable fancy folder view instead of the default Apache directory listing.", action="store_true", default=False, dest="use_fancy_folders")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument("-a", "--author-name", help="Name of the author of the images.", default=DEFAULT_AUTHOR, type=str, dest="author_name", metavar="AUTHOR")
    parser.add_argument("-e", "--file-extensions", help="File extensions to include (can be specified multiple times).", action="append", dest="file_extensions", metavar="EXTENSION")
    parser.add_argument("-l", "--license-type", help="Specify the license type for the images.", choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], default=None, dest="license_type", metavar="LICENSE")
    parser.add_argument("-m", "--web-manifest", help="Generate a web manifest file.", action="store_true", default=False, dest="generate_webmanifest")
    parser.add_argument("-n", "--non-interactive-mode", help="Run in non-interactive mode, disabling progress bars.", action="store_true", default=False, dest="non_interactive_mode")
    parser.add_argument("-p", "--root-directory", help="Root directory containing the images.", required=True, type=str, dest="root_directory", metavar="ROOT")
    parser.add_argument("-r", "--regenerate-thumbnails", help="Regenerate thumbnails even if they already exist.", action="store_true", default=False, dest="regenerate_thumbnails")
    parser.add_argument("-t", "--site-title", help="Title of the image hosting site.", required=True, type=str, dest="site_title", metavar="TITLE")
    parser.add_argument("-w", "--web-root-url", help="Base URL of the web root for the image hosting site.", required=True, type=str, dest="web_root_url", metavar="URL")
    parsed_args = parser.parse_args()
    _args = Args()
    _args.author_name = parsed_args.author_name
    _args.exclude_folders = parsed_args.exclude_folders
    _args.file_extensions = parsed_args.file_extensions
    _args.generate_webmanifest = parsed_args.generate_webmanifest
    _args.ignore_other_files = parsed_args.ignore_other_files
    _args.license_type = parsed_args.license_type
    _args.non_interactive_mode = parsed_args.non_interactive_mode
    _args.regenerate_thumbnails = parsed_args.regenerate_thumbnails
    _args.root_directory = parsed_args.root_directory
    _args.site_title = parsed_args.site_title
    _args.theme_path = parsed_args.theme_path
    _args.use_fancy_folders = parsed_args.use_fancy_folders
    _args.web_root_url = parsed_args.web_root_url
    return _args
