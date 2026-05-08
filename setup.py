from setuptools import setup, find_packages

setup(
    name="cra-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.4.0",
        "requests>=2.27.0",
        "beautifulsoup4>=4.10.0",
    ],
    extras_require={
        "pdf": ["pdfplumber>=0.7.0"],
    },
)
