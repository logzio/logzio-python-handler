#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="logzio-python-handler",
    version='1.0.0',
    description="Logging handler to send logs to your Logz.io account with bulk SSL",
    keywords="logging handler logz.io bulk https",
    author="roiravhon",
    author_email="roi@logz.io",
    url="https://github.com/logzio/logzio-python-handler/",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests"
    ],
    include_package_data=True,
    platform='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ]
)