import sys
import atexit
import subprocess
import typing


class AutoPager:
    def __init__(self, no_pager: bool = False, always: bool = False):
        self.original_stdout = sys.stdout
        self.always = always
        self.no_pager = no_pager

        if self.original_stdout.isatty():
            self.process: typing.Optional[
                subprocess.Popen[str]] = subprocess.Popen(
                    ['/usr/bin/less', '-F'],
                    stdin=subprocess.PIPE,
                    encoding='utf-8')
            sys.stdout = self.process.stdin  # type: ignore
        else:
            self.process = None
        atexit.register(self.output)

    def output(self):
        if self.process:
            self.process.communicate()
