import setuptools

packages = [
    "treespace.create_trees",
    "treespace.drawing",
    "treespace.francis",
    "treespace.jetten",
    "treespace.max_cst",
]

with open("README.md", "r") as fh:
    description = fh.read()

setuptools.setup(
    name="treespace",
    version="0.0.1",
    author="Andrew Quijano",
    author_email="afq2101@columbia.edu",
    packages=["treespace"],
    description="A package containing Treespace algorithms for rooted phylogenetic networks",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/AndrewQuijano/Treespace_REU_2017/",
    license='MIT',
    python_requires='>=3.9',
    install_requires=[]
)
