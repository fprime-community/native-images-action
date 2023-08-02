import subprocess
import sys
import shutil


def run():
    """ Run JAR file as if it were invoked directly

    Runs a JAR file forwarding in all the arguments to the JAR file itself. The JAR file chosen is inferred from the
    name of the python executable (i.e. sys.arv[0]). Exits forwarding back the return code.
    """
    if not shutil.which("java"):
        print(f"[ERROR] {sys.argv[0]} requires 'java'. Please install 'java' and ensure it is available on the PATH.")
        sys.exit(-23)
    arguments = ["java", "-jar", f"{sys.argv[0]}.jar"] + sys.argv[1:]
    process = subprocess.run(arguments)
    sys.exit(process.returncode)
