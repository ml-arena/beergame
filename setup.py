from setuptools import setup, find_packages

setup(
    name="beergame",
    version="0.7",
    description="Beer Game Environment for PettingZoo",
    packages=find_packages(),
    package_data={
        'beergame.env': ['*.png'],
    },
    install_requires=[],
    python_requires=">=3.7",
)