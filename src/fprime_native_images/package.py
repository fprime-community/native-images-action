import os
import platform
import sys
import subprocess
from pathlib import Path
from typing import List, Union

from jinja2 import Environment, PackageLoader


def build_packages_from_directory(directory: Path, working: Path, outdir: Path, package_tag: str, extensions: Union[List[str], None] = None):
    """ Build a set of packages around tools found in a directory

    Given a directory this will build a PIP package that wraps each tool in that directory. Tools will be filtered by
    the list of extensions, with a default of filter of no-extension and ".exe".

    Args:
        directory: path to the directory to search
        working: working directory
        outdir: output wheel directory forwarded to build
        package_tag: package tag to apply to package
        extensions: extensions to filter tools down too

    Return:
        list of packages as dependencies
    """
    environment = Environment(
        loader=PackageLoader("fprime_native_images"),
    )
    extensions = extensions if extensions else ["", ".exe"]
    for tool in directory.glob("*"):
        if tool.suffix not in extensions:
            print(f"[INFO] Skipping {tool} with unaccepted extension")
            continue
        print(f"[INFO] Building package around {tool} with tag {package_tag}")
        directory = generate_tool_package(tool, environment, working)
        # Patch for +x ensuring tools are executable
        st = os.stat(str(tool.resolve()))
        os.chmod(str(tool.resolve()), st.st_mode | st.S_IEXEC)
        build_wheel(directory, outdir, package_tag)


def generate_tool_package(tool: Path, environment: Environment, working: Path) -> Path:
    """ Build a PIP package for a given tool

    Builds a package for a given tool using setuptools. This wraps the setup call suplying the given package and given
    path for using SCM.

    Args:
        tool: path to tool to wrap
        environment: Jinja2 templating environment
        working: working directory
    Return:
        package that was created in dependency form (package==version)
    """
    package = f"fprime-{tool.stem}"
    package_path = working / package
    package_path.mkdir(parents=True, exist_ok=True)

    template = environment.get_template("setup.py.j2")

    template_data = {
        "package": package,
        "jar_distribution": tool.suffix == ".jar",
        "tool_path": str(tool.resolve())
    }

    with open(package_path / Path(template.filename).stem, "w") as file_handle:
        file_handle.write(template.render(**template_data))
    return package_path


def build_wheel(package_directory: Path, outdir: Path, package_tag: str):
    """ Build a wheel package using 'build'

    Generates a wheel package using the python package builder "build". The package generated is specified as
    package_directory and the distribution output directory is specified as outdir and is forwarded to the outdir
    argument of build. The package will be platform specific unless universal is True.

    Arguments:
        package_directory: directory containing a buildable python package
        outdir: forwarded to builds --outdir option
        package_tag: when true will build a universal (JAR) wheel. Defaults to building platform specific wheel
    """
    build_arguments = [
        sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir.resolve()),
        str(package_directory.resolve())
    ]

    if package_tag is not None:
        build_arguments.append(f'--config-setting=--global-option=--plat-name={ package_tag }')
    print(f"[INFO] Running: {' '.join(build_arguments)}")
    subprocess.run(build_arguments, check=True)
