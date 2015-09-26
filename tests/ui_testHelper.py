import unittest

def getOutputString(call_args_list):
  outputString = ""

  for c in call_args_list:
    outputString += c[0][0]
  return outputString  
