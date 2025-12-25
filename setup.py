"""Setup configuration for tgdl package."""
from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="tgdl",
    version="1.1.4",
    author="kavidu-dilhara",
    author_email="contact@kavidudilhara.eu.org",
    description="A high-performance CLI tool for downloading media from Telegram channels, groups, and messages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kavidu-dilhara/tgdl",
    project_urls={
        "Bug Reports": "https://github.com/kavidu-dilhara/tgdl/issues",
        "Source": "https://github.com/kavidu-dilhara/tgdl",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="telegram, downloader, media, cli, async, telethon",
    packages=find_packages(exclude=["tests", "docs"]),
    python_requires=">=3.7",
    install_requires=[
        "telethon>=1.42.0",
        "click>=8.3.0",
        "tqdm>=4.67.1",
        "aiofiles>=25.1.0",
        "cryptography>=43.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=9.0.0",
            "pytest-asyncio>=1.3.0",
            "black>=25.11.0",
            "flake8>=7.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tgdl=tgdl.cli:main",
        ],
    },
)
