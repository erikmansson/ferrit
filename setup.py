import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines()]

setuptools.setup(
    name="ferrit",
    author="Erik Månsson",
    author_email="erik@mansson.xyz",
    description="A stupid tool for listing and checking out Gerrit changes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/erikmansson/ferrit",
    py_modules=["ferrit"],
    entry_points={
        "console_scripts": [
            "fe=ferrit:main",
            "ferrit=ferrit:main",
        ]
    },
    zip_safe=True,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
    install_requires=requirements,
)
