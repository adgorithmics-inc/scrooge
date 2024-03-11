import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fh:
    readme = fh.read()

extras_require = {
    "backends": ["redis>=3.0.0"],
    "redis": ["redis>=3.0.0"],
}

setup(
    name="scrooge",
    version=__import__("scrooge").__version__,
    description="scrooge, a greedy task queue",
    long_description=readme,
    author="Brian de Heus",
    author_email="tech@adgorithmics.com",
    url="http://github.com/adgorithmics-inc/scrooge/",
    packages=find_packages(),
    extras_require=extras_require,
    package_data={
        "scrooge": [],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    test_suite="runtests.collect_tests",
    entry_points={
        "console_scripts": ["huey_consumer = scrooge.bin.huey_consumer:consumer_main"]
    },
    scripts=["scrooge/bin/scrooge_consumer.py"],
)
