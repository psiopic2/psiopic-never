import sys
import math
import time
from .terminal import getTerminal

SPIN_FISH = (">))'>    "," >))'>   ","  >))'>  ","   >))'> ","    >))'>","   <'((< ","  <'((<  "," <'((<   ")
SPIN_1    = ("  []  ", " [--] ", "[----]", "------", "----- ", "----  ", "---    ", "--    ", "-     ", "     ") 

class BaseWidget(object):
  def __init__(self, label=None):
    self.label = label
    self.term = getTerminal()

  def output(self, msg, flush=True):
    sys.stdout.write(msg)
    if flush:
      sys.stdout.flush()


class Spinner(BaseWidget):
  def __init__(self, chars=('/','|','\\','-'), interval=100, label=None, label_color=None, spinner_color=None, suffix_color=None):
    super(Spinner, self).__init__(label)
    self.chars = chars
    self.interval = interval

    if label_color == None:
      self.label_color = self.term.normal
    else:
      self.label_color = label_color

    if spinner_color == None:
      self.spinner_color = self.term.normal
    else:
      self.spinner_color = spinner_color

    if suffix_color == None:
      self.suffix_color = self.term.normal
    else:
      self.suffix_color = suffix_color

    self._counter = 0
    self._last_time = 0
    self.rendered = False

    self._starting_pos = 0
    if self.label:
      self._starting_pos += len(self.label) + 1

  def render(self, suffix=None):
    curtime = time.time() * 1000
    if self.rendered == False:
      if self.label:
        self.output(self.label_color + self.label + " ", False)
      self.rendered = True
    
    if ((curtime - self._last_time) >= self.interval) or self.interval == None:
      self.output(self.term.move_x(self._starting_pos) + self.spinner_color + self.chars[self._counter])

      if suffix:
        self.output(" %s%s" % (self.suffix_color, suffix))

      self._counter += 1
      self._last_time = curtime
      if self._counter == len(self.chars):
        self._counter = 0
  

class ProgressBar():
  def __init__(self, **kwargs): 
    self.term = getTerminal()
    self.width = kwargs.get('width', 30)
    self.empty_char = kwargs.get('empty_char', ' ')
    self.fill_char  = kwargs.get('fill_char', '-')
    self.empty_char_color = kwargs.get('empty_char_color', self.term.white + self.term.bold)
    self.fill_char_color  = kwargs.get('fill_char_color', self.term.green)
    self.starting_pos     = kwargs.get('starting_pos', 0)
    self.last_percent = 0
    self.last_info = None
    self.last_expected = 0
    self._interval_percent = (1 / float(self.width))

  def render(self, amt, expected): 
    sys.stdout.flush()

    if expected != self.last_expected:
      self.last_percent = 0
      self.last_expected = expected

    try:
      percent = float(amt) / float(expected)
    except ZeroDivisionError:
      percent = 0
   
    if (percent - self.last_percent) >= self._interval_percent:
      sys.stdout.write(self.term.move_x(self.starting_pos)) 
      
      self.last_percent = percent
      fillchars = self.fill_char * int(math.ceil(self.width * percent))
      emptychars = self.empty_char * (self.width - len(fillchars))

      sys.stdout.write(self.fill_char_color + fillchars)
      sys.stdout.write(self.empty_char_color + emptychars)
      
   

class ProgressBarWidget():
  def __init__(self, **kwargs):
    self.term = getTerminal()
    self._kwargs = kwargs
    self.indent = kwargs.get('indent', 0)
    self.label = kwargs.get('label', None)
    self.bracket_color = kwargs.get('bracket_color', self.term.white)
    self.bracket_start_char = kwargs.get('bracket_start_char', '[')
    self.bracket_end_char = kwargs.get('bracket_end_char', ']')
    self.separator_char = kwargs.get('separator_char','|')
    self.separator_color = kwargs.get('separator_color', self.term.white + self.term.bold)
    self.width = kwargs.get('width', 30)
    self.empty_char_color = kwargs.get('empty_char_color', self.term.white)
    self.empty_char = kwargs.get('empty_char', ' ')
    self.fill_char_color = kwargs.get('fill_char_color', self.term.green)
    self.fill_char = kwargs.get('fill_char', '-')
    self.info_color = kwargs.get('info_color', self.term.white)
    self.bars = kwargs.get('bars', 1)
    self.last_info = ""

    self.rendered = False

    self._bars = []
        
    self._starting_pos = len(self.bracket_start_char) + self.indent
    self._info_pos     = len(self.bracket_start_char) + self.width + self.indent + len(self.bracket_end_char)

    if self.label != None:
      self._starting_pos += len(self.label) + 1
      self._info_pos += len(self.label) + 1

  def render(self, amt, expected, info=None, no=1):
    sys.stdout.flush()

    if (self.rendered == False):
      if self.label:
        sys.stdout.write(self.label + " ")

      tpl = self.bracket_color + self.bracket_start_char
      bartpl = []
      width = (self.width / self.bars) - (len(self.separator_char) * (self.bars-1))

      for i in range(0, self.bars):
        starting_pos = self._starting_pos + (i * (width + len(self.separator_char)))

        self._bars.append(ProgressBar(
          width=width,
          empty_char=self.empty_char,
          empty_char_color=self.empty_char_color,
          fill_char=self.fill_char,
          fill_char_color=self.fill_char_color,
          starting_pos = starting_pos
        ))
        bartpl.append(self.empty_char_color + (self.empty_char * width))

      separator_tpl = self.separator_color + self.separator_char
      tpl += separator_tpl.join(bartpl)
      tpl += self.bracket_color + self.bracket_end_char
      sys.stdout.write(tpl)
      self.rendered = True

    self._bars[no-1].render(amt, expected)
    
    if info != None and info != self.last_info:
      sys.stdout.write(self.term.move_x(self._info_pos))
      sys.stdout.write(" " * (len(self.last_info) + 1))
      sys.stdout.flush()

      sys.stdout.write(self.term.move_x(self._info_pos))      
      sys.stdout.write(" " + self.info_color + info)
      sys.stdout.flush()

      self.last_info = info
