import logging
import subprocess
import time

log = logging.getLogger(__name__)


def verbose_check_output(*args):
    """ 'verbose' version of subprocess.check_output() """
    log.info("Call: %r" % " ".join(args))
    output = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT)
    return output


def verbose_check_call(*args):
    """ 'verbose' version of subprocess.check_call() """
    print("\tCall: %r\n" % " ".join(args))
    subprocess.check_call(args, universal_newlines=True)


def iter_subprocess_output(*args, timeout=10):
    print("_" * 80)
    cmd = " ".join(args)
    print("Call: %r" % cmd)
    process = subprocess.Popen(args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    outs, errs = process.communicate(timeout=timeout)
    for line in outs:
        yield line

    exit_code = process.returncode
    print("(Process finished with exit code %r)\n\n" % exit_code)
    if exit_code:
        raise subprocess.CalledProcessError(returncode=exit_code, cmd=cmd)
