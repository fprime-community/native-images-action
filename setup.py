from setuptools import setup

setup(
    name="fprime-native-images",
    use_scm_version={"root": ".", "relative_to": __file__},
    license="Apache 2.0 License",
    description="fprime-layout distribution package",
    url="https://github.com/nasa/fprime",
    keywords=["fpp", "fprime", "embedded", "nasa"],
    project_urls={"Issue Tracker": "https://github.com/nasa/fprime/issues"},
    author="Michael Starch",
    author_email="Michael.D.Starch@jpl.nasa.gov",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    setup_requires=["setuptools_scm"],
    python_requires=">=3.7",
    packages=["fprime_native_images"],
    package_dir={"": "src"},
)
