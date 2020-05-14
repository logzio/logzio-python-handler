#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="logzio-python-handler",
    version='3.0.0',
    description="Logging handler to send logs to your Logz.io account with bulk SSL",
    keywords="logging handler logz.io bulk https",
    author="roiravhon",
    author_email="roi@logz.io",
    url="https://github.com/logzio/logzio-python-handler/",
    license="Apache License 2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.23.0"
    ],
    test_requires=[
        "future"
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7'
    ]
)
