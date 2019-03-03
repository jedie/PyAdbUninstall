import logging
import sys
from io import StringIO

log = logging.getLogger(__name__)


class RedirectStdoutStderr(object):
    """
    Context manager to redirect stdout / stderr

    >>> stdout_buffer = StringIO()
    >>> with RedirectStdoutStderr(stdout=stdout_buffer, tee=True):
    ...     print("output to **stdout** !")
    ...     sys.stderr.write("output to **stderr** !")
    >>>
    >>> stdout_buffer.getvalue()
    'output to **stdout** !'


    >>> stdout_buffer = StringIO()
    >>> stderr_buffer = StringIO()
    >>> with RedirectStdoutStderr(stdout=stdout_buffer, stderr=stderr_buffer):
    ...     print("output to **stdout** !")
    ...     sys.stderr.write("output to **stderr** !")
    >>>
    >>> stdout_buffer.getvalue()
    'output to **stdout** !'
    >>> stderr_buffer.getvalue()
    'output to **stderr** !'
    """

    def __init__(self, stdout_write=None, stderr_write=None, tee=True):
        self._stdout_write = stdout_write
        self._stderr_write = stderr_write
        self.tee = tee

    def stdout_write(self, *args):
        self._stdout_write(*args)
        if self.tee:
            self.old_stdout_write(*args)
            sys.stdout.flush()

    def stderr_write(self, *args):
        self._stderr_write(*args)
        if self.tee:
            self.old_stderr_write(*args)
            sys.stderr.flush()

    def __enter__(self):
        if self._stdout_write is not None:
            log.debug("redirect sys.stdout (tee:%r)", self.tee)
            self.old_stdout_write = sys.stdout.write
            sys.stdout.write = self.stdout_write

        if self._stderr_write is not None:
            log.debug("redirect sys.stderr (tee:%r)", self.tee)
            self.old_stderr_write = sys.stderr.write
            sys.stderr.write = self.stderr_write

    def __exit__(self, exc_type, exc_value, traceback):
        if self._stdout_write is not None:
            sys.stdout.write = self.old_stdout_write

        if self._stderr_write is not None:
            sys.stderr.write = self.old_stderr_write


if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
