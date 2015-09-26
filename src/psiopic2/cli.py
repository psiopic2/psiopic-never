from psiopic2.app.setupwiki import SetupWiki
from psiopic2.app.createcorpus import CreateCorpus
import sys
import logging
from psiopic2.app.ui.logutils import getLogger
from appdirs import AppDirs
from docopt import docopt
import traceback

DOC="""Psiopic2 CLI Tool

Usage:
  psiopic2 <command> [options]
  
Available Commands:
  setupwiki
  help
  buildcorpus
  
For more information run:
  psiopic2 <command> --help

"""

class HelpException(BaseException):
  pass

class App():
  def __init__(self, argv):
    
    self.colors = False if '--no-colors' in argv else True
    self.widgets = False if '--no-widgets' in argv else True
    
    logLevel = logging.DEBUG if '-d' in argv or '--debug' in argv else logging.INFO
    self.log = getLogger('psiopic', self.colors, logLevel)
    
    self._argv = argv
    
    self.appMap = {}
    
  def addApp(self, appName, appFunc):
    self.appMap[appName] = appFunc
    
  def help(self):
    sys.stdout.write(DOC)
    
  def getApp(self, app=None):
    if app == 'help':
      raise HelpException
    
    try:
      if app == None:
        app = self._argv[1]
      return self.appMap[app]
    except IndexError:
      raise HelpException
    
  def run(self):
    ret = 0
    
    try:
      app = self.getApp()
      app(self._argv)
    except HelpException:
      self.help()
    except Exception, e:
      self.log.critical('Unhandled exception')
      self.log.critical(traceback.format_exc())
      ret = 1
    finally:
      if ret > 0:
        self.log.error('Something went wrong. Error code: %s' % ret)
      return ret

def main():
  app = App(sys.argv)
  app.addApp('setupwiki', SetupWiki)
  return app.run()

if __name__ == '__main__':
  sys.exit(main())
