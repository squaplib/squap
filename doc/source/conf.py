import sys
from os import path
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'squap'
copyright = '2026, R. Mulder'
author = 'R. Mulder'
release = '0.0.1'

sys.path.append(path.abspath(r"../../"))
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_design',
    'sphinx.ext.autodoc',
    "sphinx.ext.napoleon",  # has to be loaded before sphinx_autodoc_typehints
    "sphinx_autodoc_typehints",
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pyqtgraph": ("https://pyqtgraph.readthedocs.io/en/latest/", None),
    "PySide6": ("https://doc.qt.io/qtforpython-6/", None),
    "numpy": ("https://numpy.org/doc/stable/", None)
}

autodoc_mock_imports = ["pyqtgraph", "PySide6"]

exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']

napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True

# makes things far more legible
python_use_unqualified_type_names = True
python_display_short_literal_types = True
maximum_signature_line_length = 40

templates_path = ['_templates']

html_show_sourcelink = False

html_logo = r"images\logo_horizontal.png"

html_static_path = ['_static']

html_css_files = [
    "custom.css",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
