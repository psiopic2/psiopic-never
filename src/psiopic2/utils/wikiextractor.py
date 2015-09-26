import socket
import logging
import os
import subprocess
import signal

class ConnectionError(Exception):
  def __init__(self, message):
    super(ConnectionError, self).__init__(message)


class WikiExtractorServer(object):
  def __init__(self, host, port, script, mwdir):
    self.host = host
    self.port = port
    self.script = script
    self.log = logging.getLogger('psiopic.' + self.__class__.__name__)
    self.server_pid = None
    self.mwdir = mwdir
    
  def start(self):
    
    cmd = [
      'php',
      self.script,
      '--host',
      self.host,
      '--port',
      str(self.port),
      '-m',
      self.mwdir,
      '--daemon'
    ]
    
    print cmd
    
    self.proc = subprocess.Popen(cmd)
    self.proc.wait()
    
  def stop(self):
    os.kill(self.proc.pid, signal.SIGTERM)

class WikiExtractorClient(object):
  def __init__(self, host, port):
    self.host = host
    self.port = int(port)
    self.connected = False
    self._socket = None
    self.log = logging.getLogger('psiopic.wikiExtractorClient')
    
  
  def handshake(self, s):
    """Perform handshake with Wikiextractor
    
    Args:
      s: socket instance
    Returns:
      True if successful, False otherwise
    """
    s.send("hello\n")
    helo = s.recv(6)
    
    if (helo == "hello\n"):
      return True
    else:
      return False
    
  
  def connect(self):
    """Connects to a Wikiextractor server
    
    It will perform the handshake as well.
    
    Returns nothing
    """
    if self.connected == False:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.log.debug('Connecting to %s:%s' % (self.host, self.port))
      s.connect((self.host, self.port))
      
      if self.handshake(s):
        self.log.debug('Connection established')
        self.connected = True
        self._socket = s
      else:
        self.log.error('Handshake failed')
        raise ConnectionError('Handshake failed')
        
  def disconnect(self):
    """Disconnect from Wikiextractor"""
    if self.connected == True:
      self._socket.send("goodbye\n")
      self._socket.close()
      
      
  def getArticle(self, pageId):
    """Gets full HTML for pageId from Wikiextractor"""
    self._socket.send("%s\n" % pageId)
    
    start = self._socket.recv(10)
    
    articleBuffer = ""
    
    if start == "--start--\n":
      running = True
      
      while running:
        content = self._socket.recv(1024)
        
        if content[-8:] == "--end--\n":
          articleBuffer += content[:-8]
          running = False
        else:
          articleBuffer += content
          
    return articleBuffer                   


class WikiExtractorResult(object):
  def __init__(self, articleBody, categories):
    self.categories = categories
    self.articleBody = articleBody 
     
  
