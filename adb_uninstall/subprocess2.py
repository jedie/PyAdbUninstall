import logging
import subprocess
import sys
from pathlib import Path

import time

log = logging.getLogger(__name__)


def human_duration(t):
    """
    Converts a time duration into a friendly text representation.

    >>> human_duration(datetime.timedelta(microseconds=1000))
    '1.0 ms'
    >>> human_duration(0.01)
    '10.0 ms'
    >>> human_duration(0.9)
    '900.0 ms'
    >>> human_duration(datetime.timedelta(seconds=1))
    '1.0 sec'
    >>> human_duration(65.5)
    '1.1 min'
    >>> human_duration(59.1 * 60)
    '59.1 min'
    """
    if t < 1:
        return "%.1f ms" % round(t * 1000, 1)
    if t < 60:
        return "%.1f sec" % round(t, 1)
    return "%.1f min" % round(t / 60, 1)


def verbose_check_output(*popenargs, timeout=5, **kwargs):
    """ 'verbose' version of subprocess.check_output() """
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

    output = verbose_check_output("python3", __file__, "stdout")
    print("output:", repr(output))

    output = verbose_check_output("python3", __file__, "stderr")
    print("output:", repr(output))
