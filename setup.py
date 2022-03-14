#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="cromwell-helper",
    version="0.1.0.dev",
    packages=find_packages(exclude=["tests"]),

    author="Yasunobu Okamura",
    author_email="okamura@informationsea.info",
    description="Cromwell workflow engine helper utilities",
    keywords="cromwell workflow",

    python_requires=">=3.7",
    install_requires=[
        "requests>=2.22.0"
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities"
    ],

    entry_points={
        'console_scripts':[
            'fakedocker = cromwellhelper.fakedocker:_main',
            'cromwell-cli = cromwellhelper.cromwell_cli.__main__:_main',
            'grid = cromwellhelper.grid:_main'
        ]
    }
)
