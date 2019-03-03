import logging
import subprocess
import sys
import time

from adb_uninstall.utils.humanize import human_duration

log = logging.getLogger(__name__)


def verbose_check_output(*popenargs, timeout=5, **kwargs):
    """
    'verbose' version of subprocess.check_output()
    """
    print("Call: %r..." % " ".join(popenargs), end=" ", flush=True)

    start_time = time.time()

    completed_process = subprocess.run(
        popenargs,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=True,
        universal_newlines=True,
        **kwargs
    )

    duration = time.time() - start_time
    exit_code = completed_process.returncode
    print("(exit code:%r after %s)" % (exit_code, human_duration(duration)))

    completed_process.check_returncode()  # if exit_code != 0: raise CalledProcessError

    output = completed_process.stdout
    return output


if __name__ == "__main__":
    if "stdout" in sys.argv:
        sys.stdout.write("output to **stdout** !")
        sys.exit(0)

    if "stderr" in sys.argv:
        sys.stderr.write("output to **stderr** !")
        sys.exit(0)

    print(verbose_check_output("python3", __file__, "stdout"))
    print(verbose_check_output("python3", __file__, "stderr"))
