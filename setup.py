"""
QDB - Intelligent caching stock database
Setup configuration for PyPI distribution
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read PyPI-specific README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README_PYPI.md").read_text(encoding="utf-8")


# Read requirements
def read_requirements(filename):
    """Read requirements file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


# Basic dependencies
install_requires = [
    "pandas>=1.3.0",
    "numpy>=1.20.0",
    "akshare>=1.0.0",
    "pandas-market-calendars>=4.0.0",
    "sqlalchemy>=1.4.0",
    "tenacity>=8.2.3,!=8.4.0",  # Removed upper bound for better compatibility
    "python-dateutil>=2.8.0",
    "beautifulsoup4>=4.12.3",  # Explicit version to avoid conflicts
]

# Optional dependencies
extras_require = {
    "full": [
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "httpx>=0.18.0",
        "python-dotenv>=0.19.0",
    ],
    "dev": [
        "pytest>=6.2.0",
        "pytest-cov>=2.12.0",
        "black>=21.0.0",
        "flake8>=3.9.0",
        "mypy>=0.910",
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=0.5.0",
    ],
}

setup(
    # Basic information
    name="quantdb",
    version="2.2.11",
    author="Ye Sun",
    author_email="franksunye@hotmail.com",
    description="Intelligent caching wrapper for AKShare with 90%+ performance boost - 100% English codebase (import as 'qdb')",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/franksunye/quantdb",
    project_urls={
        "Bug Reports": "https://github.com/franksunye/quantdb/issues",
        "Source": "https://github.com/franksunye/quantdb",
        "Documentation": "https://franksunye.github.io/quantdb/",
    },
    # Package configuration
    packages=find_packages(include=["qdb", "qdb.*", "core", "core.*"]),
    include_package_data=True,
    package_data={
        "qdb": ["*.md", "*.txt"],
        "core": ["**/*.sql", "**/*.json"],
    },
    # Dependency configuration
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    # Classification information
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    # Keywords
    keywords="stock, finance, akshare, cache, quantitative, trading, investment, qdb, quantdb",
    # Entry points - temporarily removed CLI, focusing on library functionality
    # entry_points={
    #     'console_scripts': [
    #         'qdb=qdb.cli:main',
    #     ],
    # },
    # License
    license="MIT",
    # Other configuration
    zip_safe=False,
    platforms=["any"],
)
