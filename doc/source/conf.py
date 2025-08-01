#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# KIWI NG documentation build configuration file
#
from datetime import datetime
import sys
from os.path import abspath, dirname, join, normpath
import shlex

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
_path = normpath(join(dirname(__file__), "../.."))
sys.path.insert(0, _path)


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.extlinks',
    'sphinx.ext.todo',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme'
]

docopt_ignore = [
    'kiwi.cli',
    'kiwi.tasks.system_build',
    'kiwi.tasks.system_prepare',
    'kiwi.tasks.system_update',
    'kiwi.tasks.system_create',
    'kiwi.tasks.result_list',
    'kiwi.tasks.result_bundle',
    'kiwi.tasks.image_resize',
    'kiwi.tasks.image_info'
]

def remove_module_docstring(app, what, name, obj, options, lines):
    if what == "module" and name in docopt_ignore:
        del lines[:]

def prologReplace(app, docname, source):
    result = source[0]
    for key in app.config.prolog_replacements:
        result = result.replace(key, app.config.prolog_replacements[key])
    source[0] = result

def setup(app):
    app.add_config_value('prolog_replacements', {}, True)
    app.connect('source-read', prologReplace)
    app.connect("autodoc-process-docstring", remove_module_docstring)


prolog_replacements = {
    '{exc_image_base_name_pxe}': 'kiwi-test-image-pxe',
    '{exc_image_base_name_vagrant}': 'kiwi-test-image-vagrant',
    '{exc_image_base_name_disk}': 'kiwi-test-image-disk',
    '{exc_image_base_name_disk_simple}': 'kiwi-test-image-disk-simple',
    '{exc_image_base_name_live}': 'kiwi-test-image-live',
    '{exc_image_base_name_docker}': 'kiwi-test-image-docker',
    '{exc_image_base_name_enclave}': 'kiwi-test-image-nitro-enclave',
    '{exc_netboot}': 'netboot/suse-tumbleweed',
    '{exc_description_pxe}': 'x86/tumbleweed/test-image-pxe',
    '{exc_description_vagrant}': 'x86/leap/test-image-vagrant',
    '{exc_description_disk}': 'x86/leap/test-image-disk',
    '{exc_description_disk_simple}': 'x86/leap/test-image-disk-simple',
    '{exc_description_live}': 'x86/leap/test-image-live',
    '{exc_description_wsl}': 'x86/tumbleweed/test-image-wsl',
    '{exc_description_docker}': 'x86/leap/test-image-docker',
    '{exc_description_enclave}': 'x86/rawhide/test-image-nitro-enclave',
    '{exc_os_version}': '15.6',
    '{exc_image_version}': '1.15.6',
    '{exc_repo_leap}': 'https://download.opensuse.org/distribution/leap/15.6/repo/oss',
    '{exc_repo_tumbleweed}': 'https://download.opensuse.org/tumbleweed/repo/oss',
    '{exc_repo_rawhide}': 'https://mirrors.fedoraproject.org/metalink?repo=rawhide&arch=x86_64',
    '{exc_kiwi_repo}':
        'obs://Virtualization:Appliances:Builder/openSUSE_Leap_15.6',
    '{schema_version}': '8.0',
    '{kiwi}': 'KIWI NG',
    '{kiwi-product}': 'KIWI Next Generation (KIWI NG)',
    '{kiwi-legacy}': 'KIWI Legacy'
}

latex_documents = [
    ('index', 'kiwi.tex', 'KIWI NG Documentation', 'Marcus Schäfer', 'manual')
]
latex_elements = {
    'papersize': 'a4paper',
    'pointsize':'12pt',
    'classoptions': ',openany',
    'babel': '\\usepackage[english]{babel}',
    'preamble': r'''
      \makeatletter
      \fancypagestyle{normal}{
        \fancyhf{}
        \fancyfoot[LE,RO]{{\py@HeaderFamily\thepage}}
        \fancyfoot[LO]{{\py@HeaderFamily\nouppercase{\rightmark}}}
        \fancyfoot[RE]{{\py@HeaderFamily\nouppercase{\leftmark}}}
        \fancyhead[LE,RO]{{\py@HeaderFamily \@title, \py@release}}
        \renewcommand{\headrulewidth}{0.4pt}
        \renewcommand{\footrulewidth}{0.4pt}
      }
      \makeatother
    '''
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['.templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

default_role="py:obj"

# General information about the project.
project = 'KIWI NG'
author = 'Marcus Schäfer'
copyright = f'2020-{datetime.now().year}, {author}'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '10.2.31'
# The full version, including alpha/beta/rc tags.
release = version

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

autosummary_generate = True

# -- Options for HTML output ----------------------------------------------

#html_short_title = '%s-%s' % (project, version)
#html_last_updated_fmt = '%b %d, %Y'
#html_split_index = True
html_logo = '.images/kiwi-logo.png'

html_sidebars = {
   '**': [
          'localtoc.html', 'relations.html',
          'about.html', 'searchbox.html',
         ]
}

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    'collapse_navigation': False
}

# -- Options for manual page output ---------------------------------------

# The man page toctree documents.
kiwi_doc = 'commands/kiwi'
result_list_doc = 'commands/result_list'
result_bundle_doc = 'commands/result_bundle'
system_prepare_doc = 'commands/system_prepare'
system_update_doc = 'commands/system_update'
system_build_doc = 'commands/system_build'
system_create_doc = 'commands/system_create'
image_resize_doc = 'commands/image_resize'
image_info_doc = 'commands/image_info'

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        kiwi_doc,
        'kiwi', 'Creating Operating System Images',
        [author],
        8
    ),
    (
        result_list_doc,
        'kiwi::result::list',
        'List build results',
        [author],
        8
    ),
    (
        result_bundle_doc,
        'kiwi::result::bundle',
        'Bundle build results',
        [author],
        8
    ),
    (
        system_prepare_doc,
        'kiwi::system::prepare',
        'Prepare image root system',
        [author],
        8
    ),
    (
        system_create_doc,
        'kiwi::system::create',
        'Create image from prepared root system',
        [author],
        8
    ),
    (
        system_update_doc,
        'kiwi::system::update',
        'Update/Upgrade image root system',
        [author],
        8
    ),
    (
        system_build_doc,
        'kiwi::system::build',
        'Build image in combined prepare and create step',
        [author],
        8
    ),
    (
        image_resize_doc,
        'kiwi::image::resize',
        'Resize disk images to new geometry',
        [author],
        8
    ),
    (
        image_info_doc,
        'kiwi::image::info',
        'Provide detailed information about an image description',
        [author],
        8
    )
]

# If true, show URL addresses after external links.
#man_show_urls = False
