import os
import shutil
import stat
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from jinja2 import Environment, PackageLoader
from setuptools_scm import get_version


def build_packages_from_directory(
    directory: Path,
    working: Path,
    outdir: Path,
    package_tag: str,
    meta_package: str,
    extensions: Union[List[str], None] = None,
    extra_tools: Optional[List] = None,
    fast: bool = False,
):
    """Build a set of packages around tools found in a directory

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
        extra_tools: base list of tools for meta-package
        fast: enable fast (deprecated) packages
    Return:
        list of packages as dependencies
    """
    environment = Environment(
        loader=PackageLoader("fprime_native_images"),
    )
    # version = get_version(root=(working / "..").resolve())
    extensions = extensions if extensions else ["", ".exe"]

    fast = True
    tools: Dict[str, str] = {}
    for tool in directory.glob("*"):
        if tool.suffix not in extensions:
            print(f"[INFO] Skipping {tool} with unaccepted extension")
            continue
        elif not tool.is_file():
            print(f"[INFO] Skipping {tool} with unaccepted file type")
            continue

        if tool.suffix == ".jar":
            fast = False

        print(f"[INFO] Adding {tool} to package")

    package_dir = generate_package(
        meta_package,
        tools,
        environment,
        working,
        fast=fast,
    )

    print(f"[INFO] Building package around {meta_package} with tag {package_tag}")
    build_wheel(package_dir, outdir, package_tag)


def generate_base_package(
    name: str,
    environment: Environment,
    working: Path,
    jar_distribution = False,
    dependencies: Optional[List] = None,
    template_name: str = "pyproject.toml.j2",
    template_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """Generate a base python package containing a pyproject.toml

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

    template = environment.get_template(template_name)

    if template is None:
        raise FileNotFoundError(f"template '{template_name}' not found")

    template_data = {} if template_data is None else template_data
    template_data.update(
        {
            "jar_distribution": jar_distribution,
            "package": package,
            "package_corrected": package_corrected,
            "dependencies": dependencies,
        }
    )

    with open(
        package_path / Path(Path(template.filename).stem).stem, "w"
    ) as file_handle:
        file_handle.write(template.render(**template_data))
    return package_path, template_data


def generate_package(
    package_name: str,
    tools: Dict[str, str],
    environment: Environment,
    working: Path,
    fast: bool = False,
) -> Path:
    """Build a PIP package for a given tool

    Builds a package for a given tool using setuptools. This wraps the setup call suplying the given package and given
    path for using SCM.

    Args:
        tool: path to tool to wrap
        environment: Jinja2 templating environment
        working: working directory
        fast: enable fast (deprecated) packages
    Return:
        package that was created in dependency form (package==version)
    """
    template_data = {
        "tools": tools,
        "fast_hack": fast,
    }

    jar_distribution = True in [".jar" in x for x in tools.values()]

    package_path, template_data = generate_base_package(
        package_name,
        environment,
        working,
        jar_distribution=jar_distribution,
        template_data=template_data
    )

    package_source = package_path / template_data["package_corrected"]
    package_source.mkdir(parents=True, exist_ok=True)
    (package_source / "__init__.py").touch(exist_ok=True)

    for tool_path in tools.values():
        # Patch for +x ensuring tools are executable
        tool = Path(tool_path)
        st = os.stat(str(tool.resolve()))
        os.chmod(str(tool.resolve()), st.st_mode | stat.S_IEXEC)
        shutil.copy(tool, package_source)

    template = environment.get_template("__main__.py.j2")
    with open(package_source / Path(template.filename).stem, "w") as file_handle:  # type: ignore
        file_handle.write(template.render(**template_data))
    return package_path


def build_wheel(package_directory: Path, outdir: Path, package_tag: str):
    """Build a wheel package using 'build'

    Generates a wheel package using the python package builder "build". The package generated is specified as
    package_directory and the distribution output directory is specified as outdir and is forwarded to the outdir
    argument of build. The package will be platform specific unless universal is True.

    Arguments:
        package_directory: directory containing a buildable python package
        outdir: forwarded to builds --outdir option
        package_tag: when true will build a universal (JAR) wheel. Defaults to building platform specific wheel
    """
    build_arguments = [
        sys.executable,
        "-m",
        "build",
        "--wheel",
        "--outdir",
        str(outdir.resolve()),
        str(package_directory.resolve()),
    ]

    if package_tag is not None:
        build_arguments.append(
            f"--config-setting=--build-option=--plat-name={ package_tag }"
        )
    print(f"[INFO] Running: {' '.join(build_arguments)}")
    subprocess.run(build_arguments, check=True)
