import sys
from datetime import datetime
from docopt import docopt
from psiopic2.app.ui.prompt import ask, prompt
import logging
import textwrap
from psiopic2.app.tasks import TaskException
import traceback

BASE_OPTIONS = """Options:
  --no-widgets          Turn off all widgets, useful for logfiles
  --no-colors           Turn off any coloring
  -d                    Enable debugging
  -h --help             Show this help information
  -v --version          Version information
"""

class Arg(object):
  def __init__(self, **kwargs):
    self.title = kwargs.get('title') or kwargs.get('name')
    self.name = kwargs.get('name')
    self.description = kwargs.get('description')
    self.defaultValue = kwargs.get('defaultValue')
    self.valueDesc = kwargs.get('valueDesc', '')
    self.prompt = kwargs.get('prompt', True)
    self.smallName = kwargs.get('smallName', '')
    
    self.startTime = None
    self.endTime = None

BASE_ARGS = [
  Arg(
    title="Force",
    name='force',
    description='Do not prompt user for missing settings. Use defaults',
    defaultValue=False,
    prompt=False
  ),
  Arg(
    title='No Widgets',
    name='no-widgets',
    description='Turn off all widgets, useful for logfiles',
    defaultValue=False,
    prompt=False
  ),
  Arg(
    title='No Colours',
    name='no-colors',
    description='Turn off all colours',
    defaultValue=False,
    prompt=False
  ),
  Arg(
    title='Debug',
    name='debug',
    smallName='d',
    description='Turn on debugging',
    defaultValue=False,
    prompt=False
  ),
  Arg(
    title='Help',
    name='help',
    smallName='h',
    description='Display this help',
    defaultValue=False,
    prompt=False
  ),
  Arg(
    title='Version',
    name='version',
    description='Display product version',
    defaultValue=False,
    prompt=False
  )
]

class BaseApp(object):
  
  def __init__(self, name, argv, version=None, title=None, description=None):
    self._argv = argv
    self._name = name
    self._docString = None
    self._version = version
    
    self._availArgs = None
    self._args = None
    self._cliArgs = None
    
    self._workQueue = []
    
    self._log = None
    
    self.description = description
    self.title = title or name
    
  def help(self):
    sys.stdout.write(self.getDocString())
    
  def version(self):
    sys.stdout.write(self._version)
    sys.stdout.write("\n")
    
  def getLogger(self):
    if self._log == None:
      self._log = logging.getLogger('psiopic.' + self._name)
    return self._log
  
  def addArg(self, name, title=None, description=None, defaultValue=None, prompt=True):

    if self._availArgs == None:
      self._availArgs = []
    
    if name.__class__ == Arg:
      self._availArgs.append(name)
    else:
      self._availArgs.append(Arg(
        name=name,
        title=title,
        description=description,
        defaultValue=defaultValue,
        prompt=prompt
      ))
  
  def getDocString(self):
    if self._docString == None:
      
      docString = ""
      
      if self.title:
        docString += self.title + "\n"
        
      if self.description:
        docString += "\n" + self.description
        
      docString += "\nUsage: psiopic2 %s [options]\n" % self._name
      docString += "\n"
      docString += "Options (%s):\n" % self._name
      
      
  
      # find longest argument name
      longestLen = max(len(arg.name) + len(arg.valueDesc) + len(arg.smallName) for arg in self._availArgs)
      
      longestLen = longestLen + 12 # allow for additional formatting
      
      descriptionWidth = 80 - longestLen 
  
      for arg in self._availArgs:
        
        descriptionLines = textwrap.wrap(arg.description, descriptionWidth)
        
        optString = "  "
        if arg.smallName:
          optString += "-%s " % (arg.smallName)
          
        if arg.name and arg.name != arg.smallName:
          optString += "--%s" % (arg.name)
        
        if arg.valueDesc:
          optString += '=%s' % (arg.valueDesc)
          
        optString += '  '
        
        if len(optString) < longestLen:
          optString += " " * (longestLen - len(optString))
        
        docString += optString + '%s\n' % (descriptionLines.pop())
        
        if len(descriptionLines) > 0:
          for line in descriptionLines:
            docString += " " * longestLen
            docString += line + "\n"
            
      docString += "\n"
      # docString += BASE_OPTIONS
      
      self._docString = docString
    return self._docString
  
  def getCliArgs(self):
    if self._cliArgs == None:
      self._cliArgs = docopt(self.getDocString(), self._argv[1:], False)
    return self._cliArgs
  
  def getArg(self, argName):
    return self._args[argName]
  
  def addTask(self, task, taskOpts, taskTitle=None):
    if taskTitle == None:
      taskTitle = task.__name__
    self._workQueue.append((task, taskOpts, taskTitle))
    
  def initConfiguration(self):
    
    if self._args == None:
      self._args = {}
    
      cliArgs = self.getCliArgs()
      
      argValue = None
      
      for arg in self._availArgs:
        if '--' + arg.name in cliArgs and cliArgs['--' + arg.name] != None:
          argValue = cliArgs['--' + arg.name]
        elif arg.prompt and cliArgs['--force'] != True:
          argValue = ask(arg.title, arg.defaultValue)
        else:
          argValue = arg.defaultValue
          
        self._args[arg.name] = argValue
        
    
  def run(self):
    
    ret = 0
    
    log = self.getLogger()
    self.startTime = datetime.now()
    self.initConfiguration()
    
    if len(self._workQueue) == 0:
      log.warning("There are no tasks in the work queue, is this app setup properly?")
    else:
      try:
        for taskClass, taskOpts, taskTitle in self._workQueue:
          task = taskClass(self._args)
          log.info(taskTitle or task.name)
          task.run(**taskOpts)
      except TaskException as e:
        log.error('%s failed' % task.name)
        log.exception(e)
        ret = 1
      except Exception as e:
        log.critical('Unhandled exception from %s' % taskTitle)
        log.critical(traceback.format_exc())
        ret = 1
    
    self.endTime = datetime.now() - self.startTime

    log.info('Completed in: %s' % self.endTime)
    
    return ret
  
