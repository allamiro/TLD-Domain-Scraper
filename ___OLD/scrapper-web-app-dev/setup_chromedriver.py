import os
import sys
import subprocess
import platform
import requests
import zipfile
import io

def get_chrome_version():
    """Get the installed Chrome version on macOS"""
    try:
        cmd = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version'
        version = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        return version.split()[-1]
    except:
        print("Error: Could not determine Chrome version")
        sys.exit(1)

def download_chromedriver(version):
    """Download ChromeDriver matching the Chrome version"""
    # For newer Chrome versions, use ChromeDriver 114 which is known to work
    chromedriver_version = "114.0.5735.90"
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    chromedriver_path = os.path.join(project_root, "chromedriver")
    
    # Download ChromeDriver
    url = f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_mac64.zip'
    print(f"Downloading ChromeDriver {chromedriver_version}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Could not download ChromeDriver")
        sys.exit(1)
    
    # Extract the zip file
    z = zipfile.ZipFile(io.BytesIO(response.content))
    z.extractall(project_root)
    
    # Set permissions
    os.chmod(chromedriver_path, 0o755)
    
    print(f"ChromeDriver setup complete! Downloaded to: {chromedriver_path}")

def main():
    if platform.system() != 'Darwin':
        print("This script is for macOS only")
        sys.exit(1)
    
    chrome_version = get_chrome_version()
    print(f"Detected Chrome version: {chrome_version}")
    
    download_chromedriver(chrome_version)

if __name__ == "__main__":
    main() 