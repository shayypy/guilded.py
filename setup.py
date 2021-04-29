import re
import setuptools

with open('README.md', 'r') as rmd:
    long_description = rmd.read()

requirements = []
with open('requirements.txt') as rtxt:
    requirements = rtxt.read().splitlines()

version = ''
with open('guilded/__init__.py') as initpy:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', initpy.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Version is not set.')

setuptools.setup(
    name='guilded.py',
    version=version,
    author='shay (shayypy)',
    author_email='shay@bearger.gay',
    description='An API wrapper in Python for Guilded\'s user/client API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/shayypy/guilded.py',
    project_urls={
        'Documentation': 'https://guildedpy.readthedocs.io/en/latest/',
        'Issue tracker': 'https://github.com/shayypy/guilded.py/issues',
    },
    packages=['guilded', 'guilded.ext.commands'],
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English'
    ],
    python_requires='>=3.6',
    install_requires=requirements
)
