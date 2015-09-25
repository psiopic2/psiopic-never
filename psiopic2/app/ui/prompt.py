import sys

def prompt(msg):
  sys.stdout.write(msg)
  sys.stdout.write(" ")
  sys.stdout.flush()
  return sys.stdin.readline().strip()

def ask(msg, defaultValue=None):
  
  out = msg + " (%s):" % defaultValue
  
  userInput = prompt(out)
  if userInput:
    return userInput
  else:
    return defaultValue