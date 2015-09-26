import sys
import math
import time
from .terminal import getTerminal
from .terminal import out

SPIN_FISH = (">))'>    "," >))'>   ","  >))'>  ","   >))'> ","    >))'>","   <'((< ","  <'((<  "," <'((<   ")
SPIN_1    = ("  []  ", " [--] ", "[----]", "------", "----- ", "----  ", "---    ", "--    ", "-     ", "     ") 

class BaseWidget(object):
  def __init__(self, label=None):
    self.label = label
    self.term = getTerminal()

  def output(self, msg, flush=True):
    out(msg, flush)

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
  

class ProgressBar(BaseWidget):
  def __init__(self, **kwargs):
    self.term = getTerminal()
    self.label = kwargs.get('label', None)
    self.brackets = kwargs.get('brackets', ('[',']'))
    self.bracket_color = kwargs.get('bracket_color', self.term.white)
    self.separator_char = kwargs.get('separator_char','|')
    self.separator_color = kwargs.get('separator_color', self.term.white + self.term.bold)
    self.width = kwargs.get('width', 30)
    self.empty_char_color = kwargs.get('empty_char_color', self.term.white)
    self.empty_char = kwargs.get('empty_char', ' ')
    self.fill_char_color = kwargs.get('fill_char_color', self.term.green)
    self.fill_char = kwargs.get('fill_char', '-')
    self.info_color = kwargs.get('info_color', self.term.white)
    self.bars = kwargs.get('bars', 1)
    self.rendered = False   

    self._last_info = ""
    self._brackets_length = sum([len(bracket) for bracket in self.brackets])
    self._separator_length = len(self.separator_char)

    # for even 10 char width:
    # 1 bar - total width = 12
    # 2 bar - total width = 23

    self._bar_width = self.width - self._brackets_length # 21 

    if self.bars > 1:
      self._bar_width -= (self.bars-1 * self._separator_length) # 20
      self._bar_width = self._bar_width / self.bars # 10

    self._bars = []
        
    self._info_pos     = self.width + 1

    if self.label != None:
      self._info_pos += len(self.label) + 1

  def _generateBar(self, width, percent):

    fillchars = self.fill_char * int(math.ceil(width * percent))
    emptychars = self.empty_char * (width - len(fillchars))

    return self.fill_char_color + fillchars + self.empty_char_color + emptychars

  def _renderBar(self, starting_pos, width, percent=0):

    #    print "RENDER BAR: START %s    WIDTH: %s    PERCENT %s" % (starting_pos, width, percent)

    self.output(self.term.move_x(starting_pos))
    self.output(self._generateBar(width, percent))
      
  def render(self, amt, expected, info=None, no=1):
    if (self.rendered == False):
      labelLength = 0
      if self.label:
        self.output(self.label + " ")
        labelLength = len(self.label)

      tpl = self.bracket_color + self.brackets[0]
      
      if self.bars < 2:
        tpl += self.empty_char_color
        tpl += self.empty_char * self._bar_width
        starting_pos = len(self.brackets[0]) + labelLength
        self._bars.append((starting_pos, self._bar_width))
      else:
        barPlaceHolders = []
        for i in range(0, self.bars):
          i += 1
          barPlaceHolder = self.empty_char_color
          barPlaceHolder += self.empty_char * self._bar_width
          barPlaceHolders.append(barPlaceHolder)

          self._bars.append((len(self.brackets[0]) + (self._separator_length * i-1) + (self._bar_width * (i-1)), self._bar_width))

        tpl += (self.separator_color + self.separator_char).join(barPlaceHolders)
      tpl += self.bracket_color + self.brackets[1]
 
      self.output(tpl)
      self.rendered = True

    percent = 0.0
    try:
      percent = (float(amt) / float(expected))
    except ZeroDivisionError:
      pass

    bar_pos, bar_width = self._bars[no-1]
    self._renderBar(bar_pos, bar_width, percent)
    
    if info != None and info != self._last_info:
      infoLen = len(info)
      if self._last_info:
        lastInfoLen = len(self._last_info)
      else:
        lastInfoLen = 0

      if infoLen < lastInfoLen:
        self.output(self.term.move_x(self._info_pos) + (lastInfoLen - infoLen))
        self.output(" " * (lastInfoLen - infoLen))

      self.output(self.term.move_x(self._info_pos))      
      self.output(self.info_color + info, True)

      self.last_info = info
