import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pynetwork",
    version="2.0.3",
    author="Niraj S. Kale",
    author_email="nirajkale157@outlook.com",
    description="package to manage connection swarms for your network workloads",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nirajkale/pynet",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
