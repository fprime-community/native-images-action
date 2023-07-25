""" fprime_native_images.py: helpers to support the native image packages """
import tarfile
import shutil
from pathlib import Path
from setuptools.command.install import install


class SafeTarfile:
    """ Safely handle tarfile and extraction"""

    @staticmethod
    def is_within_directory(directory, target):
        """ Check target is withing directory

        Ensure that the given target is within the given directory. This ensures that the target will not be extracted
        into an unsafe area (outside the archive).

        Args:
            directory: directory expected to contain target
            target: path to check

        Return:
            true if target is with directory or false otherwise
        """
        abs_directory = Path(directory).resolve()
        abs_target = Path(target).resolve()
        return abs_target.is_relative_to(abs_directory)

    @classmethod
    def extract_all(cls, tar_file):
        """ Safely extract tar files

        This extraction prevents unsafe extraction of tar files by preventing members outside the directory structure
        from extracting and instead erring the extraction.

        Args:
            tar_file: file to extract

        Throws:
            Exception when invalid member is detected
        """
        current_working_directory = Path("fprime_native_images")
        with tarfile.open(tar_file) as tar:
            for member in tar.getmembers():
                member_path = current_working_directory / member.path
                if not cls.is_within_directory(current_working_directory, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
            tar.extractall()

