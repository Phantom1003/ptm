from setuptools import setup, find_packages

setup(
    name="phantom-make",
    version="0.1.11",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'ptm=ptm:main',
        ],
    },
    author="Phantom1003",
    author_email="phantom@zju.edu.cn",
    description="A python-based traceable make system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Phantom1003/ptm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
