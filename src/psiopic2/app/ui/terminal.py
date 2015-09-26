import blessings
import sys

__term__ = None

def getTerminal():

  global __term__

  if __term__ == None:
    __term__ = blessings.Terminal()
  return __term__

def out(msg, flush=False):
  sys.stdout.write(msg)
  if flush:
    sys.stdout.flush()
