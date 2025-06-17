from setuptools import setup, find_packages

from larakit import __version__

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="lara-kit",
    version=__version__,
    description="Lara Kit for Python",
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=requirements,
)
