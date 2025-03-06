from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="agenteer",
    version="0.1.0",
    author="AI Agent Team",
    author_email="info@example.com",
    description="A streamlined AI agent builder with minimal configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agenteer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agenteer=agenteer.cli.main:app",
        ],
    },
    include_package_data=True,
)
