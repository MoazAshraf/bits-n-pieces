import re
from setuptools import setup

# get all package information
info = open('bitsnpieces/__init__.py').read()

def search_var(var):
    return re.search(r'^{key}\s*=\s*"(.*)"'.format(key=var), info, re.M).group(1)

package_name = search_var("PACKAGE_NAME")
version = search_var("__version__")
description = search_var("DESCRIPTION")
author = search_var("AUTHOR")
author_email = search_var("AUTHOR_EMAIL")

# run the setup
setup(
    name=package_name,
    version=version,
    packages=['bitsnpieces', 'bitsnpieces.bencode'],
    entry_points={
        'console_scripts': ['bitsnpieces = bitsnpieces.cmdline:main']
    },
    description=description,
    author=author,
    author_email=author_email,
)