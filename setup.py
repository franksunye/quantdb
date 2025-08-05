"""
QDB - 智能缓存的股票数据库
Setup configuration for PyPI distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取requirements
def read_requirements(filename):
    """读取requirements文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []

# 基础依赖
install_requires = [
    "pandas>=1.3.0",
    "numpy>=1.20.0", 
    "akshare>=1.0.0",
    "sqlalchemy>=1.4.0",
    "tenacity>=9.1.0",
    "python-dateutil>=2.8.0",
]

# 可选依赖
extras_require = {
    'full': [
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "httpx>=0.18.0",
        "python-dotenv>=0.19.0",
    ],
    'dev': [
        "pytest>=6.2.0",
        "pytest-cov>=2.12.0",
        "black>=21.0.0",
        "flake8>=3.9.0",
        "mypy>=0.910",
    ],
    'docs': [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=0.5.0",
    ]
}

setup(
    # 基本信息
    name="quantdb",
    version="2.2.3",
    author="Ye Sun",
    author_email="franksunye@hotmail.com",
    description="Intelligent caching wrapper for AKShare with 90%+ performance boost (import as 'qdb')",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/franksunye/quantdb",
    project_urls={
        "Bug Reports": "https://github.com/franksunye/quantdb/issues",
        "Source": "https://github.com/franksunye/quantdb",
        "Documentation": "https://github.com/franksunye/quantdb/docs",
    },
    
    # 包配置
    packages=find_packages(include=['qdb', 'qdb.*', 'core', 'core.*']),
    include_package_data=True,
    package_data={
        'qdb': ['*.md', '*.txt'],
        'core': ['**/*.sql', '**/*.json'],
    },
    
    # 依赖配置
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    
    # 分类信息
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
    
    # 关键词
    keywords="stock, finance, akshare, cache, quantitative, trading, investment, qdb, quantdb",
    
    # 入口点 - 暂时移除CLI，专注于库功能
    # entry_points={
    #     'console_scripts': [
    #         'qdb=qdb.cli:main',
    #     ],
    # },
    
    # 许可证
    license="MIT",
    
    # 其他配置
    zip_safe=False,
    platforms=["any"],
)
