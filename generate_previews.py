import os
import re
import sys
import shutil
import base64
import fileinput
import urllib.parse
import urllib.request
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from modules.logger import consolelogger as logger
from modules.css_color import extract_colorscheme


def replace_all(file, search_exp, replace_exp):
    for line in fileinput.input(file, inplace=1):
        line = re.sub(search_exp, replace_exp, line)
        sys.stdout.write(line)


def take_screenshot(html_file_path: str, css_file: str, output_file: str, driver: webdriver.Chrome) -> None:
    """
    Takes a screenshot of the given HTML file with the specified CSS applied.

    Args:
        html_file_path (str): Path to the HTML file or URL.
        css_file (str): Path to the CSS file to be applied.
        output_file (str): Path where the screenshot will be saved.
        driver (webdriver.Chrome): The Chrome WebDriver instance.
    """
    logger.info("taking screenshot for %s", css_file)
    try:
        # Open the HTML file or URL
        if html_file_path.startswith(("http://", "https://")):
            logger.info("opening URL: %s", html_file_path)
            driver.get(html_file_path)
        else:
            logger.info("opening file: %s", html_file_path)
            driver.get(f"file://{os.path.abspath(html_file_path)}")

        # Remove current theme.css
        remove_css_script = """
            var links = document.querySelectorAll("link[rel='stylesheet']");
            links.forEach(link => {
                if (link.href.includes('theme.css')) {
                    link.parentNode.removeChild(link);
                }
            });
        """
        logger.info("removing current theme.css")
        driver.execute_script(remove_css_script)

        with open(css_file, "r", encoding="utf-8") as f:
            logger.info("reading CSS file: %s", css_file)
            css_content = f.read()

        # Extract folder icon content
        css_parts = css_content.split(".foldericon {")
        css_head = css_parts[0]
        css_tail = css_parts[1].split("}", maxsplit=1)[1]
        folder_icon_content = css_parts[1].split("}", maxsplit=1)[0].strip()
        folder_icon_content = re.sub(r"/\*.*\*/", "", folder_icon_content)

        for match in re.finditer(r"content: (.*);", folder_icon_content):
            logger.info("found foldericon", extra={"foldericon": folder_icon_content})
            folder_icon_content = match.group(1).replace('"', "")
            break

        if "url" not in folder_icon_content:
            logger.info("Reading foldericon svg")
            with open(folder_icon_content, "r", encoding="utf-8") as f:
                svg = f.read()
            if "svg.j2" in folder_icon_content:
                logger.info("foldericon in theme file is a jinja2 template")
                colorscheme = extract_colorscheme(css_file)
                for color_key, color_value in colorscheme.items():
                    svg = svg.replace(f"{{{{ {color_key} }}}}", color_value)
                logger.info("replaced colors in svg")
            svg = urllib.parse.quote(svg)

            css_content = f'{css_head}\n.foldericon {{\n  content: url("data:image/svg+xml,{svg}");\n}}\n{css_tail}'

        # Encode CSS content as Base64
        logger.info("encoding css content as base64")
        encoded_css = base64.b64encode(css_content.encode("utf-8")).decode("utf-8")

        # Inject CSS into HTML using JavaScript
        apply_css_script = f"""
            var style = document.createElement('style');
            style.innerHTML = atob('{encoded_css}');
            document.head.appendChild(style);
        """
        logger.info("injecting CSS into HTML")
        driver.execute_script(apply_css_script)

        # Wait for a while to ensure CSS is applied
        # time.sleep(1)

        # Move mouse to info
        logger.info("moving mouse to info")
        hoverable = driver.find_element(By.CLASS_NAME, "tooltip")
        webdriver.ActionChains(driver).move_to_element(hoverable).perform()

        # Capture screenshot
        logger.info("taking screenshot")
        driver.save_screenshot(output_file)
        logger.info("screenshot saved to %s", output_file)

    except Exception as e:
        logger.error("failed to take screenshot for %s: %s", css_file, e)


def create_preview(html_file_path: str, css_file: str, previews_folder: str):
    logger.info("creating preview for %s", css_file)
    out_file = os.path.basename(css_file).removesuffix(".css") + ".html"
    urllib.request.urlretrieve(html_file_path, os.path.join(previews_folder, out_file))
    basename = os.path.basename(css_file)
    path = css_file.removesuffix(basename)
    replace_all(
        os.path.join(previews_folder, out_file),
        r'^\s*?<link rel="stylesheet" href=".*theme.css">\s*?$',
        f'  <link rel="stylesheet" href="file://{path}previews/{basename}">',
    )
    with open(css_file, "r", encoding="utf-8") as f:
        theme = f.read()
    split = theme.split(".foldericon {")
    split2 = split[1].split("}", maxsplit=1)
    themehead = split[0]
    themetail = split2[1]
    foldericon = split2[0].strip()
    foldericon = re.sub(r"/\*.*\*/", "", foldericon)
    for match in re.finditer(r"content: (.*);", foldericon):
        foldericon = match[1]
        foldericon = foldericon.replace('"', "")
        break
    if "url" in foldericon:
        logger.info("foldericon in theme file, using it")
        shutil.copyfile(css_file, os.path.join(path, "previews", basename))
        return
    with open(os.path.join(path, foldericon.removeprefix("themes/")), "r", encoding="utf-8") as f:
        logger.info("Reading foldericon svg")
        svg = f.read()
    if "svg.j2" in foldericon:
        logger.info("foldericon in theme file is a jinja2 template")
        colorscheme = extract_colorscheme(css_file)
        for color_key, color_value in colorscheme.items():
            svg = svg.replace(f"{{{{ {color_key} }}}}", color_value)
        logger.info("replaced colors in svg")
    svg = urllib.parse.quote(svg)
    if os.path.exists(os.path.join(path, "previews", basename)):
        os.remove(os.path.join(path, "previews", basename))
    with open(os.path.join(path, "previews", basename), "x", encoding="utf-8") as f:
        logger.info("writing theme file")
        f.write(themehead + '\n.foldericon {\n  content: url("data:image/svg+xml,' + svg + '");\n}\n' + themetail)
    logger.info("preview created for %s", css_file)


def write_readme(directory_path: str, themes: List[str]) -> None:
    """
    Writes the README file with previews of included themes.

    Args:
        directory_path (str): Path to the folder containing the themes and README.md.
        themes (List[str]): List of theme names.
    """
    readme_path = os.path.join(directory_path, "README.md")
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            logger.info("reading README.md", extra={"file": readme_path})
            readme = f.read()

        readme_head = readme.split("## Previews of included themes")[0]
        readme_head += "## Previews of included themes\n"
        readme_head += "".join([f"\n### {theme}\n\n![{theme}](screenshots/{theme}.png)\n" for theme in themes])

        with open(readme_path, "w", encoding="utf-8") as f:
            logger.info("writing README.md", extra={"file": readme_path})
            f.write(readme_head)

        logger.info("README.md updated with previews of included themes.")

    except FileNotFoundError:
        logger.error("README.md not found in %s", directory_path)
    except Exception as e:
        logger.error("failed to write README.md: %s", e)


def write_index(directory_path: str, themes: List[str]) -> None:
    with open(os.path.join(directory_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(
            """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Themes</title>
</head>
<body>"""
        )
        for theme in themes:
            f.write(f'<a href="previews/{theme}.html">{theme}</a><br>\n')
        f.write("</body></html>")


def main(directory_path: str, html_file_path: str) -> None:
    """
    Main function to take screenshots for each CSS file in the folder and update the README.md.

    Args:
        directory_path (str): Path to the folder containing CSS files.
        html_file_path (str): Path to the HTML file or URL for rendering.
    """
    if not os.path.exists(directory_path):
        logger.error('Error: Folder path "%s" does not exist.', directory_path)
        return

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode, no GUI
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size to at least 1920x1080

    # Initialize Chrome WebDriver
    chromedriver_path = "/usr/bin/chromedriver"
    service = Service(chromedriver_path)
    logger.info("Using chromedriver at %s", chromedriver_path, extra={"chrome_options": chrome_options})
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        themes = []
        # Iterate over all files in the folder
        for filename in sorted(os.listdir(directory_path)):
            if filename.endswith(".css"):
                theme_name = os.path.splitext(filename)[0]
                themes.append(theme_name)
                css_file = os.path.join(directory_path, filename)
                output_file = os.path.join(directory_path, "screenshots", f"{theme_name}.png")
                previews_folder = os.path.join(directory_path, "previews")

                # Create screenshots folder if it doesn't exist
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                os.makedirs(previews_folder, exist_ok=True)

                # Take screenshot for this CSS file
                take_screenshot(html_file_path, css_file, output_file, driver)
                create_preview(html_file_path, css_file, previews_folder)

        # Write the README file with the new previews
        write_readme(directory_path, themes)
        write_index(directory_path, themes)

    finally:
        logger.info("closing chrome webdriver")
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error("Usage: python script_name.py directory_path html_file_path")
    else:
        dir_path = sys.argv[1]
        html_path = sys.argv[2]
        logger.info("Starting script", extra={"directory_path": dir_path, "html_file_path": html_path})
        main(dir_path, html_path)
        logger.info("Done!", extra={"directory_path": dir_path})
