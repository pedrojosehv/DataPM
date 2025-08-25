from setuptools import setup, find_packages

setup(
    name="datapm",
    version="1.0.0",
    description="DataPM - Sistema de procesamiento de ofertas de trabajo",
    author="DataPM Team",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "google-generativeai",
        "requests",
        "selenium",
        "webdriver-manager",
        "pytest"
    ],
    python_requires=">=3.8",
)
