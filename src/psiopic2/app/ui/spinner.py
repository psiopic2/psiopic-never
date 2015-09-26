import sys
import time
from blessings import Terminal

class Spinner():
  def __init__(self, chars=['/','-','\\','|'], interval=None, color=None):
    self.color = color
    self.chars = chars
    self.time = 0
    self.strlen = len(self.chars[0])
    self.counter = 0
    self.interval = interval
    self.terminal = Terminal()

  def _get_time(self):
    return int(round(time.time() * 1000))

  def output(self, content):
    sys.stdout.write(content)
    sys.stdout.flush()

  def spin(self):
    curtime = self._get_time()

    if self.interval != None:
      if (curtime - self.time >= self.interval) or (self.time == 0):
        self.time = curtime
      else:
        return

    spinner = self.terminal.move_left + self.chars[self.counter]

    if self.color:
      spinner = self.color + spinner + self.terminal.normal

    self.output(content)

    self.counter += 1
    if self.counter == len(self.chars):
      self.counter = 0

