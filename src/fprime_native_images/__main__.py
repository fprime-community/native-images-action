import argparse
import sys
import shutil
from pathlib import Path
from fprime_native_images.package import build_packages_from_directory


def main():
    """ Engages the package builder """
    parser = argparse.ArgumentParser(description="Builds a set of packages from the tools found in the given directory")
    parser.add_argument("--clean", default=False, action="store_true", help="Remove outdir if it exists")
    parser.add_argument("--working-directory", default=Path.cwd() / "packages", help="Working directory for building")
    parser.add_argument("--outdir", default=None, type=Path, help="Output directory for the distribution packages")
    parser.add_argument("--package-tag", required=True, type=str, help="Package tag for packages being built")
    parser.add_argument("--meta-package", default=None, type=str, help="Name of meta-package to create")
    parser.add_argument("--extra-tools", default=[], nargs="*", required=False, help="Extra tools to add to meta package")
    parser.add_argument("directory", type=Path, help="'bin' directory to use for input files")
    arguments = parser.parse_args()

    # Error check: directory exists
    if not arguments.directory.exists():
        print(f"[ERROR] {arguments.directory} does not exist!")
        return

    arguments.outdir = arguments.outdir if arguments.outdir is not None else arguments.working_directory / "dist"

    try:
        if arguments.clean:
            shutil.rmtree(arguments.outdir, ignore_errors=True)
            shutil.rmtree(arguments.working_directory, ignore_errors=True)

        arguments.working_directory.mkdir(exist_ok=False, parents=True)
        arguments.outdir.mkdir(exist_ok=False, parents=True)
        build_packages_from_directory(
            arguments.directory,
            arguments.working_directory,
            arguments.outdir,
            None if list(arguments.directory.glob("*.jar")) else arguments.package_tag,
            [".jar"] if list(arguments.directory.glob("*.jar")) else None,
            arguments.meta_package,
            arguments.extra_tools
        )
    except OSError as oe:
        print(f"[ERROR] Could not create {arguments.outdir}. {oe}. Remove existing directory and/or grant permissions.")
        return 1
    except Exception as exception:
        print(f"[ERROR] {exception}")
        raise
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
