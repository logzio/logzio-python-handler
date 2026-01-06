#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="logzio-python-handler",
    use_scm_version=True,
    description="Logging handler to send logs to your Logz.io account with bulk SSL",
    keywords="logging handler logz.io bulk https",
    author="roiravhon",
    maintainer="tamir-michaeli",
    mail="tamir.michaeli@logz.io",
    url="https://github.com/logzio/logzio-python-handler/",
    license="Apache License 2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.27.0",
        "protobuf>=3.20.2"
    ],
    extras_require={
        "opentelemetry-logging": ["opentelemetry-instrumentation-logging==0.60b1"]
    },
    test_requires=[
        "future"
    ],
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9'
    ]
)
