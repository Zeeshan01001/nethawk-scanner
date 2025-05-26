#!/usr/bin/env python3
"""
Setup script for Advanced Port Scanner - NetHawk
"""

from setuptools import setup, find_packages
from pathlib import Path
import os

# Read README file if it exists
this_directory = Path(__file__).parent
readme_file = this_directory / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = "Enterprise-grade multi-threaded port scanner with stealth mode, banner grabbing, OS detection, and multiple export formats"

setup(
    name="nethawk-scanner",
    version="2.0.0",
    author="Zeeshan01001",
    author_email="",
    description="Enterprise-grade multi-threaded port scanner with stealth mode, banner grabbing, OS detection, and multiple export formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Zeeshan01001/nethawk-scanner",
    py_modules=["nethawk_scanner"],
    scripts=["nethawk_scanner.py"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Security",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "portscan=nethawk_scanner:main",
            "nethawk=nethawk_scanner:main",
            "advanced-portscan=nethawk_scanner:main",
        ],
    },
    install_requires=[
        # No external dependencies required - uses only Python standard library
    ],
    keywords="port scanner network security reconnaissance penetration testing nethawk",
    project_urls={
        "Bug Reports": "https://github.com/Zeeshan01001/nethawk-scanner/issues",
        "Source": "https://github.com/Zeeshan01001/nethawk-scanner",
        "Documentation": "https://github.com/Zeeshan01001/nethawk-scanner#readme",
    },
)