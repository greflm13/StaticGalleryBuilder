import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def take_screenshot(html_file, css_file, output_file):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode, no GUI

    # Set window size to at least 1920x1080
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize Chrome WebDriver with the specified service and options
    chromedriver_path = "/usr/bin/chromedriver"  # Replace with your actual path
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open the HTML file
        driver.get(f"file://{os.path.abspath(html_file)}")

        # Apply the CSS file to the HTML
        apply_css_script = f"""
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = '{os.path.abspath(css_file)}';
            document.head.appendChild(link);
        """
        driver.execute_script(apply_css_script)

        # Wait for a while to ensure CSS is applied (adjust as needed)
        time.sleep(2)

        # Capture screenshot
        driver.save_screenshot(output_file)
        print(f"Screenshot saved to {output_file}")

    finally:
        driver.quit()


def main(_folder_path):
    html_file = "/mnt/nfs/pictures/Analog/Example/index.html"

    # Check if the folder path exists
    if not os.path.exists(_folder_path):
        print(f'Error: Folder path "{_folder_path}" does not exist.')
        return

    # Iterate over all files in the folder
    for filename in sorted(os.listdir(_folder_path)):
        if filename.endswith(".css"):
            css_file = os.path.join(_folder_path, filename)
            output_file = os.path.join(_folder_path, "screenshots", f"{os.path.splitext(filename)[0]}.png")

            # Take screenshot for this CSS file
            take_screenshot(html_file, css_file, output_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py folder_path")
    else:
        folder_path = sys.argv[1]
        main(folder_path)
