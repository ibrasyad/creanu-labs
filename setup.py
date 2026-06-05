"""
Setup configuration for creanu-labs package.
"""
from setuptools import setup, find_packages

setup(
    name="creanu-labs",
    version="0.1.0",
    description="A realistic transaction data generator that simulates customer shopping behavior across different customer tiers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="ibrasyad",
    author_email="ibnura96@gmail.com",
    url="https://github.com/ibrasyad/creanu-labs",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pyarrow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "creanu-labs=generate:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="transaction simulation, e-commerce, data generation, customer behavior, analytics",
    include_package_data=True,
    zip_safe=False,
)
