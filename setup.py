from setuptools import setup, find_packages
from os import path


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="VFLabel",
    version="1.0",
    description="A tool for generating labeled ground-truth data for Structured Light Laryngoscopy.",
    author="Jann-Ole Henningson",
    author_email="jann-ole.henningson@fau.de",
    url="https://github.com/Henningson/Fireflies",
    # packages=["VFLabel"],
    # install_requires=None,
    packages=find_packages(),
)
