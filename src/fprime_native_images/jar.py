import subprocess
import sys


def run():
    """ Run JAR file as if it were invoked directly

    Runs a JAR file forwarding in all the arguments to the JAR file itself. The JAR file chosen is inferred from the
    name of the python executable (i.e. sys.arv[0]). Exits forwarding back the return code.
    """
    arguments = ["java", "-jar", f"{sys.argv[0]}.jar"] + sys.argv[1:]
    process = subprocess.run(arguments)
    sys.exit(process.returncode)
