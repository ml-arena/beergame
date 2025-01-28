from setuptools import setup, find_packages

setup(
    name="beergame",
    version="0.1.0",
    description="Beer Game Environment for PettingZoo",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "gymnasium>=0.28.1",
        "pettingzoo>=1.22.3",
    ],
    python_requires=">=3.7",
)