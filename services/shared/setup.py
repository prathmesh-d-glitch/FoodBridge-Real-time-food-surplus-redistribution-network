from setuptools import setup, find_packages

setup(
    name="foodbridge-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.6.0",
        "pydantic-settings>=2.2.0",
        "python-dateutil>=2.8.2",
    ],
)
