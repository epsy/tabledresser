from __future__ import print_function

import sys

class ProxyFile(object):
    def __init__(self, real, **callbacks):
        self.real = real
        self.callbacks = callbacks

    def __getattr__(self, attr):
        if attr in self.callbacks:
            return self.callbacks[attr]
        else:
            return getattr(self.real, attr)

class Printer(object):
    def __init__(self, output=None, safe=False):
        self.output = output or sys.stdout
        self.status = None
        self._status_printed = False
        self.safe = safe

    def print(self, *args, **kwargs):
        self._clear_status()
        print(*args, file=self.output, **kwargs)
        self._print_status()

    def _print(self, text):
        self._clear_status()
        self.output.write(text)
        if text[-1] == '\n':
            self._print_status()

    def new_status(self, text):
        self._clear_status()
        self._status_printed = False
        self.status = text
        self._print_status()

    def _clear_status(self):
        if self.safe and self._status_printed:
            self._clear_line()
            self._status_printed = False

    def _print_status(self):
        if self.status is not None and not self._status_printed:
            if self.safe:
                self.output.write(self.status)
                self.output.flush()
            else:
                print(self.status, file=self.output)
            self._status_printed = True


    def _clear_line(self):
        self.output.write('\r\033[K')

    def install(self, parent=sys, name='stdout'):
        setattr(parent, name, ProxyFile(self.output, write=self._print))
        self.safe = True

printer = Printer()
