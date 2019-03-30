import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="serviceless-distributor",
    version="1.0.001",
    packages=find_packages(),
    include_package_data=True,
    license="MIT License",
    description="A simple library to run exact functions over all server nodes without any service",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Fatih Kılıç",
    author_email="m.fatihklc0@gmail.com",
    url="https://github.com/FKLC/serviceless-distributor",
    download_url="https://pypi.org/project/serviceless-distributor/",
    classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=["requests"],
)
