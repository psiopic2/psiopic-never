import logging
import sys
from .terminal import getTerminal

class PsiopicFormatter(logging.Formatter):

  def __init__(self, msgfmt=None, datefmt=None):

    self.term = getTerminal()

    logging.Formatter.__init__(self, None, '%H:%M:%S')
   
    self.tpl = self.term.bold_white('[')
    self.tpl += self.term.yellow('%(name)s')
    self.tpl += ':'
    self.tpl += '%(levelname)s'
    self.tpl += self.term.bold_white(']')
    self.tpl += ' '
    self.tpl += '%(message)s'
 
  def format(self, record):
    
    if record.levelname == 'DEBUG':
      levelname = self.term.bold_magenta('debug')
    elif record.levelname == 'INFO':
      levelname = self.term.bold_green('info')
    elif record.levelname == 'WARNING':
      levelname = self.term.bold_yellow('warn')
    elif record.levelname == 'ERROR':
      levelname = self.term.bold_red('error')
    elif record.levelname == 'CRITICAL':
      levelname = self.term.bold_red('CRITICAL')
    else:
      levelname = record.levelname

    message = record.getMessage()
    
    s = self.tpl % {
      'name': record.name,
      'levelname': levelname,
      'message': message
    }
    
    return s

def getLogger(name, goodLooking=True, logLevel=logging.INFO):
 
  logger = logging.getLogger(name)
  logger.setLevel(logLevel)
  
  ch = logging.StreamHandler()
  ch.setLevel(logLevel)

  if goodLooking == True:
    formatter = PsiopicFormatter()
  else:
    formatter = logging.Formatter()

  ch.setFormatter(formatter)

  logger.addHandler(ch)

  # setup requests lib logger if debug is on
  if logLevel == logging.DEBUG: 
    requests_logger = logging.getLogger('requests.packages.urllib3')
    requests_logger.setLevel(logging.DEBUG)
    requests_logger.propagate = True
    requests_logger.addHandler(ch)


  return logger 
