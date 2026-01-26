import re
from pathlib import Path
from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent
PACKAGE_VERSION = BASE_DIR / "src" / "ptm" / "version.py"

def read_version() -> str:
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", PACKAGE_VERSION.read_text())
    if not match:
        raise RuntimeError("Unable to determine package version")
    return match.group(1) 

setup(
    name="phantom-make",
    version=read_version(), 
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'ptm=ptm:main',
        ],
    },
    author="Phantom1003",
    author_email="phantom@zju.edu.cn",
    description="A python-based traceable make system",
    long_description=(BASE_DIR / "README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/Phantom1003/ptm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
