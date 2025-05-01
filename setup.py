import setuptools
import os

if "PRETEND_VERSION" in os.environ:
    version = os.environ["PRETEND_VERSION"]
else:
    from setuptools_scm import get_version
    version = get_version(root='.',
                          fallback_version="0.0.0.1",
                          version_scheme="guess-next-dev",
                          local_scheme="no-local-version")
    version = version.partition(".dev")[0]

with open("README.md", "r") as fh:
    description = fh.read()

setuptools.setup(
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/AndrewQuijano/Treespace_REU_2017/",
    python_requires='>=3.8',
    version=version
)
