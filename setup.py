import os
import re

from setuptools import find_packages, setup

_MODULE_NAME = "pypindou"
_PACKAGE_NAME = "pypindou"

here = os.path.abspath(os.path.dirname(__file__))
meta = {}
with open(os.path.join(here, _MODULE_NAME, "config", "meta.py"), "r", encoding="utf-8") as f:
    exec(f.read(), meta)


def _load_req(file: str):
    items = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith("#"):
                continue
            if req.startswith("-r "):
                items.extend(_load_req(req[3:].strip()))
            else:
                items.append(req)
    return items


requirements = _load_req("requirements.txt")

_REQ_PATTERN = re.compile(r"^requirements-(\w+)\.txt$")
group_requirements = {
    item.group(1): _load_req(item.group(0))
    for item in [_REQ_PATTERN.fullmatch(reqpath) for reqpath in os.listdir()]
    if item
}

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name=_PACKAGE_NAME,
    version=meta["__VERSION__"],
    packages=find_packages(include=(_MODULE_NAME, f"{_MODULE_NAME}.*")),
    package_data={
        "pypindou.resources": ["*.json"],
    },
    include_package_data=True,
    description=meta["__DESCRIPTION__"],
    long_description=readme,
    long_description_content_type="text/markdown",
    author=meta["__AUTHOR__"],
    author_email=meta["__AUTHOR_EMAIL__"],
    license="Apache License, Version 2.0",
    keywords="fuse-beads, perler, hama, artkal, mard, image-processing, pixel-art, pattern-generation",
    url="https://github.com/hansbug/pypindou",
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require=group_requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    project_urls={
        "Homepage": "https://github.com/hansbug/pypindou",
        "Documentation": "https://pypindou.readthedocs.io/",
        "Source": "https://github.com/hansbug/pypindou",
        "Download": "https://pypi.org/project/pypindou/#files",
        "Bug Reports": "https://github.com/hansbug/pypindou/issues",
        "Contributing": "https://github.com/hansbug/pypindou/blob/main/CONTRIBUTING.md",
        "CI": "https://github.com/hansbug/pypindou/actions",
        "Coverage": "https://codecov.io/gh/hansbug/pypindou",
        "License": "https://github.com/hansbug/pypindou/blob/main/LICENSE",
    },
)
