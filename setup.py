"""
Setup configuration for lettuce-melon package.
"""
from setuptools import setup, find_packages

setup(
    name="lettuce-melon",
    version="0.1.0",
    description="Transaction data generation simulator with customer tier-based shopping behavior",
    author="ibrasyad",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
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
            "lettuce-melon=generate:main",
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
    ],
)
