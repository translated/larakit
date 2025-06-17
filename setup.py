from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="lara-kit",
    version="0.0.1",
    description="Lara Kit for Python",
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=requirements,
)
