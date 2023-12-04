import re
import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('extensions'))

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'guilded.py'
copyright = '2020-present, shay (shayypy)'
author = 'shay'

# The full version, including alpha/beta/rc tags
version = ''
with open('../guilded/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

release = version
branch = 'master' if version.endswith('a') else 'v' + version

# -- General configuration ---------------------------------------------------

# Links used for cross-referencing stuff in other documentation
intersphinx_mapping = {
  'py': ('https://docs.python.org/3', None),
  'aio': ('https://docs.aiohttp.org/en/stable/', None),
  'dpy': ('https://discordpy.readthedocs.io/en/latest/', None),
}

rst_prolog = """
.. |dpyattr| replace:: This exists for compatibility with discord.py bots. It may be removed in a later version.
.. |nestype| replace:: If you are using the :ref:`event style experiment <event-experiment>`, this event takes a single parameter:
.. |nesonly| replace:: This event will only be dispatched if the :ref:`event style experiment <event-experiment>` is enabled.
.. |nesnever| replace:: If the :ref:`event style experiment <event-experiment>` is enabled, this event will never be dispatched.
.. |coro| replace:: This function is a |coroutine_link|_.
.. |maybecoro| replace:: This function *could be a* |coroutine_link|_.
.. |coroutine_link| replace:: *coroutine*
.. _coroutine_link: https://docs.python.org/3/library/asyncio-task.html#coroutine
"""

# ^ "nes" = new event style
# This was formerly "experimental event style" but it should not be an experiment forever.
# Inherently, "new" will also become untrue in a sense, but I thought it was better than "experimental".

highlight_language = 'python3'
source_suffix = '.rst'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
  'sphinx.ext.autodoc',
  'sphinx.ext.extlinks',
  'sphinx.ext.intersphinx',
  'sphinx.ext.napoleon',
  'resourcelinks',
  'sphinxcontrib_trio'
]

autodoc_member_order = 'bysource'
autodoc_typehints = 'none'

extlinks = {
  'issue': ('https://github.com/shayypy/guilded.py/issues/%s', '#'),
  'dpyissue': ('https://github.com/Rapptz/discord.py/issues/%s', 'Rapptz/discord.py#'),
  'gdocs': ('https://www.guilded.gg/docs/api/%s', None),
  'ddocs': ('https://discord.com/developers/docs/%s', None),
  'ghelp': ('https://support.guilded.gg/hc/en-us/articles/', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_experimental_html5_writer = True
html_favicon = './images/guilded_py_logo.ico'
html_theme = 'alabaster'

html_context = {
  'guilded_extensions': [('guilded.ext.commands', 'ext/commands'), ('guilded.ext.tasks', 'ext/tasks')],
}

html_sidebars = {
  '**': [
    'localtoc.html',
    'searchbox.html'
  ]
}

resource_links = {
  'repository': 'https://github.com/shayypy/guilded.py',
  'issues': 'https://github.com/shayypy/guilded.py/issues',
  'examples': 'https://github.com/shayypy/guilded.py/tree/master/examples',
  'discussions': 'https://github.com/shayypy/guilded.py/discussions',
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['style.css']
#html_js_files = []
