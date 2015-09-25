import sys
import time
from blessings import Terminal

class Spinner():
  def __init__(self, chars=['/','-','\\','|'], interval=100, color=None):
    self.color = color
    self.chars = chars
    self.time = 0
    self.strlen = len(self.chars[0])
    self.counter = 0
    self.interval = interval
    self.terminal = Terminal()

  def _get_time(self):
    return int(round(time.time() * 1000))

  def spin(self):
    curtime = self._get_time()

    if (curtime - self.time >= self.interval) or (self.time == 0):
      self.time = curtime

      spinner = self.terminal.move_left + self.chars[self.counter]

      if self.color:
        spinner = self.color + spinner + self.terminal.normal

      sys.stdout.write(spinner)
      sys.stdout.flush()
      self.counter += 1
      if self.counter == len(self.chars):
        self.counter = 0


