import os
import platform

os_name = platform.system()

packages = [
    "pyqt6"
]

if os_name == "Windows":
    for package in packages:
        os.system(f"py -3 -m pip install {package}")

if os_name == "Linux" or os_name == "Darwin":
    for package in packages:
        os.system(f"python3 -m pip install {package}")
