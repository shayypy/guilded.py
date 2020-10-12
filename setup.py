import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="guilded.py",
    version="0.0.5",
    author="shay",
    author_email="shay@bearger.ga",
    description="An API wrapper for Guilded's undocumented user API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shayypy/guilded.py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5.3',
)
