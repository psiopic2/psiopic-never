import blessings

__term__ = None

def getTerminal():

  global __term__

  if __term__ == None:
    __term__ = blessings.Terminal()
  return __term__
