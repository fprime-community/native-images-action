import os
import shutil
import stat
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from jinja2 import Environment, PackageLoader
from setuptools_scm import get_version


def build_packages_from_directory(directory: Path, working: Path, outdir: Path, package_tag: str, extensions: Union[List[str], None] = None, meta_package: str = None):
    """ Build a set of packages around tools found in a directory

    Given a directory this will build a PIP package that wraps each tool in that directory. Tools will be filtered by
    the list of extensions, with a default of filter of no-extension and ".exe". If meta_package is supplied and
    non-None then a package of the given name will be created wrapping each of the other packages.

    Args:
        directory: path to the directory to search
        working: working directory
        outdir: output wheel directory forwarded to build
        package_tag: package tag to apply to package
        extensions: extensions to filter tools down too
        meta_package: create a meta-package wrapping the sub-packages

    Return:
        list of packages as dependencies
    """
    environment = Environment(
        loader=PackageLoader("fprime_native_images"),
    )
    version = get_version(root=(working / "..").resolve())
    extensions = extensions if extensions else ["", ".exe"]
    tools = []
    for tool in directory.glob("*"):
        if tool.suffix not in extensions:
            print(f"[INFO] Skipping {tool} with unaccepted extension")
            continue
        elif not tool.is_file():
            print(f"[INFO] Skipping {tool} with unaccepted file type")
            continue
        tools.append(f"{tool.name}=={version}")
        print(f"[INFO] Building package around {tool} with tag {package_tag}")
        directory = generate_tool_package(tool, environment, working)
        build_wheel(directory, outdir, package_tag)
    if meta_package is not None:
        directory, _ = generate_base_package(meta_package, environment, working, tools, "pyproject.toml.meta.j2")
        build_wheel(directory, outdir, None)


def generate_base_package(name: str, environment: Environment, working: Path, dependencies: List = None, template: str = "pyproject.toml.tool.j2", template_data: Dict[str, Any]=None) -> Tuple[Path, Dict[str, Any]]:
    """ Generate a base python package containing a pyproject.toml

    Generate a base package containing only a pyproject.toml file. The template defaults to a tool template, but may be
    overridden.

    Args:
        name: name of package to create
        environment: Jinja2 templating environment
        dependencies: list of dependencies
        working: working directory
        template: string containing name of template file
        template_data: extra data for the templates
    Returns:
        template_data for use in extending the base
    """
    package = f"fprime-{name}"
    package_corrected = package.replace("-", "_")
    package_path = working / package
    package_path.mkdir(parents=True, exist_ok=True)

    template = environment.get_template(template)

    template_data = {} if template_data is None else template_data
    template_data.update({
        "package": package,
        "package_corrected": package_corrected,
        "dependencies": dependencies
    })

    with open(package_path / Path(Path(template.filename).stem).stem, "w") as file_handle:
        file_handle.write(template.render(**template_data))
    return package_path, template_data


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
    tool_name = tool.stem if tool.stem else tool.name
    template_data = {
        "jar_distribution": tool.suffix == ".jar",
        "tool_name": tool_name,
    }
    package_path, template_data = generate_base_package(tool_name, environment, working, template_data=template_data)

    package_source = package_path / template_data["package_corrected"]
    package_source.mkdir(parents=True, exist_ok=True)
    (package_source / "__init__.py").touch(exist_ok=True)
    shutil.copy(tool, package_source)
    # Patch for +x ensuring tools are executable
    st = os.stat(str((package_source / tool.name).resolve()))
    os.chmod(str(tool.resolve()), st.st_mode | stat.S_IEXEC)

    template = environment.get_template("__main__.py.j2")
    with open(package_source / Path(template.filename).stem, "w") as file_handle:
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
        build_arguments.append(f'--config-setting=--build-option=--plat-name={ package_tag }')
    print(f"[INFO] Running: {' '.join(build_arguments)}")
    subprocess.run(build_arguments, check=True)
