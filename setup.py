from setuptools import setup, find_packages

setup(
    name="phantom-make",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    author="phantom",
    author_email="phantom@zju.edu.cn",
    description="A python-based traceable make system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/phantom/ptm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
