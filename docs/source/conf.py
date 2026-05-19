import os
import sys
from datetime import datetime

from packaging import version as version_

_DOC_PATH = os.path.dirname(os.path.abspath(__file__))
_PROJ_PATH = os.path.abspath(os.path.join(_DOC_PATH, "..", ".."))
sys.path.insert(0, _PROJ_PATH)
os.chdir(_PROJ_PATH)

from pypindou.config.meta import __AUTHOR__, __TITLE__, __VERSION__

project = __TITLE__
copyright = f"{datetime.now().year}, {__AUTHOR__}"
author = __AUTHOR__
version = version_.parse(__VERSION__).base_version
release = __VERSION__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.githubpages",
]

templates_path = ["_templates"]
exclude_patterns = ["api_doc_en.rst", "api_doc_zh.rst"]
master_doc = "index"
language = "zh_CN"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_context = {
    "display_github": True,
    "github_user": "hansbug",
    "github_repo": "pypindou",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

autodoc_typehints = "description"
autosummary_generate = True
todo_include_todos = True
