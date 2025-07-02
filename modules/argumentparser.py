from dataclasses import dataclass
from typing import Optional
import os
import argparse

try:
    from rich_argparse import RichHelpFormatter, HelpPreviewAction

    RICH = True
except ModuleNotFoundError:
    RICH = False


if __package__ is None:
    PACKAGE = ""
else:
    PACKAGE = __package__
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__).removesuffix(PACKAGE))
DEFAULT_THEME_PATH = os.path.join(SCRIPTDIR, "templates", "default.css")
DEFAULT_AUTHOR = "Author"


@dataclass(init=True)
class Args:
    """
    A class to store command-line arguments for the script.

    Attributes:
    -----------
    author_name : str
        The name of the author of the images.
    exclude_folders : list[str]
        A list of folders to exclude from processing.
    file_extensions : list[str]
        A list of file extensions to include.
    folder_thumbs : bool
        Wether to generate subfolder thumbnails.
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
    exclude_folders: list[str]
    file_extensions: list[str]
    folder_thumbs: bool
    generate_webmanifest: bool
    ignore_other_files: bool
    license_type: Optional[str]
    non_interactive_mode: bool
    regenerate_thumbnails: bool
    reread_metadata: bool
    reread_sidecar: bool
    reverse_sort: bool
    root_directory: str
    site_title: str
    theme_path: str
    use_fancy_folders: bool
    web_root_url: str

    def to_dict(self) -> dict:
        result: dict = {}
        result["author_name"] = self.author_name
        result["exclude_folders"] = self.exclude_folders
        result["file_extensions"] = self.file_extensions
        result["folder_thumbs"] = self.folder_thumbs
        result["generate_webmanifest"] = self.generate_webmanifest
        result["ignore_other_files"] = self.ignore_other_files
        if self.license_type is not None:
            result["license_type"] = self.license_type
        result["non_interactive_mode"] = self.non_interactive_mode
        result["regenerate_thumbnails"] = self.regenerate_thumbnails
        result["reread_metadata"] = self.reread_metadata
        result["reread_sidecar"] = self.reread_sidecar
        result["reverse_sort"] = self.reverse_sort
        result["root_directory"] = self.root_directory
        result["site_title"] = self.site_title
        result["theme_path"] = self.theme_path
        result["use_fancy_folders"] = self.use_fancy_folders
        result["web_root_url"] = self.web_root_url
        return result


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
    # fmt: off
    if RICH:
        parser = argparse.ArgumentParser(description="generate HTML files for a static image hosting website", formatter_class=RichHelpFormatter)
    else:
        parser = argparse.ArgumentParser(description="generate HTML files for a static image hosting website")
    parser.add_argument("-a", "--author-name", help="name of the author of the images", default=DEFAULT_AUTHOR, type=str, dest="author_name", metavar="AUTHOR")
    parser.add_argument("-e", "--file-extensions", help="file extensions to include (can be specified multiple times)", action="append", dest="file_extensions", metavar="EXTENSION")
    parser.add_argument("-l", "--license-type", help="specify the license type for the images", choices=["cc-zero", "cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"], default=None, dest="license_type", metavar="LICENSE")
    parser.add_argument("-m", "--web-manifest", help="generate a web manifest file", action="store_true", default=False, dest="generate_webmanifest")
    parser.add_argument("-n", "--non-interactive-mode", help="run in non-interactive mode, disabling progress bars", action="store_true", default=False, dest="non_interactive_mode")
    parser.add_argument("-p", "--root-directory", help="root directory containing the images", required=True, type=str, dest="root_directory", metavar="ROOT")
    parser.add_argument("-t", "--site-title", help="title of the image hosting site", required=True, type=str, dest="site_title", metavar="TITLE")
    parser.add_argument("-w", "--web-root-url", help="base URL of the web root for the image hosting site", required=True, type=str, dest="web_root_url", metavar="URL")
    parser.add_argument("--exclude-folder", help="folders to exclude from processing, globs supported (can be specified multiple times)", action="append", dest="exclude_folders", metavar="FOLDER")
    parser.add_argument("--folderthumbnails", help="generate subfolder thumbnails (first image in folder will be shown)", action="store_true", default=False, dest="folder_thumbs")
    if RICH:
        parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg", )
    parser.add_argument("--ignore-other-files", help="ignore files that do not match the specified extensions", action="store_true", default=False, dest="ignore_other_files")
    parser.add_argument("--regenerate-thumbnails", help="regenerate thumbnails even if they already exist", action="store_true", default=False, dest="regenerate_thumbnails")
    parser.add_argument("--reread-metadata", help="reread image metadata", action="store_true", default=False, dest="reread_metadata")
    parser.add_argument("--reread-sidecar", help="reread sidecar files", action="store_true", default=False, dest="reread_sidecar")
    parser.add_argument("--reverse-sort", help="sort images in reverse order", action="store_true", default=False, dest="reverse_sort")
    parser.add_argument("--theme-path", help="path to the CSS theme file", default=DEFAULT_THEME_PATH, type=str, dest="theme_path", metavar="PATH")
    parser.add_argument("--use-fancy-folders", help="enable fancy folder view instead of the default Apache directory listing", action="store_true", default=False, dest="use_fancy_folders")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parsed_args = parser.parse_args()
    # fmt: on
    _args = Args(
        author_name=parsed_args.author_name,
        exclude_folders=parsed_args.exclude_folders,
        file_extensions=parsed_args.file_extensions,
        folder_thumbs=parsed_args.folder_thumbs,
        generate_webmanifest=parsed_args.generate_webmanifest,
        ignore_other_files=parsed_args.ignore_other_files,
        license_type=parsed_args.license_type,
        non_interactive_mode=parsed_args.non_interactive_mode,
        regenerate_thumbnails=parsed_args.regenerate_thumbnails,
        reread_metadata=parsed_args.reread_metadata,
        reread_sidecar=parsed_args.reread_sidecar,
        reverse_sort=parsed_args.reverse_sort,
        root_directory=parsed_args.root_directory,
        site_title=parsed_args.site_title,
        theme_path=parsed_args.theme_path,
        use_fancy_folders=parsed_args.use_fancy_folders,
        web_root_url=parsed_args.web_root_url,
    )
    return _args
