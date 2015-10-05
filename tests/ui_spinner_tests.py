import unittest
from mock import MagicMock
from psiopic2.app.ui.widgets import Spinner
from .ui_testHelper import getOutputString

class SpinnerTests(unittest.TestCase):
 
  def test_spin_no_interval_no_label_no_suffix(self):

    spinner = Spinner(interval=None, label=None)

    for interval in range(0, len(spinner.chars)):
      spinner.output = MagicMock()
      if interval >= len(spinner.chars):
        interval = interval - len(spinner.chars)

      finalString = spinner.term.move_x(0) + spinner.spinner_color + spinner.chars[interval]
      spinner.render()

      outputString = getOutputString(spinner.output.call_args_list)

      self.assertEquals(finalString, outputString)

  def test_spin_no_interval_label_no_suffix(self):

    label = "Testing"
    spinner_pos = len(label) + 1 # Space automatically added beside label    

    spinner = Spinner(interval=None, label=label)
    spinner.output = MagicMock()

    spinner.render()

    finalString = spinner.label_color + label + " " + spinner.term.move_x(spinner_pos) + spinner.spinner_color + spinner.chars[0]
    outputString = getOutputString(spinner.output.call_args_list)
    self.assertEquals(finalString, outputString)

  def test_spin_no_interval_label_suffix(self):

    label = "Testing"
    suffix = "Foobar"

    spinner_pos = len(label) + 1

    spinner = Spinner(interval=None, label=label)
    spinner.output = MagicMock()

    spinner.render()

    finalString = spinner.label_color + label + " " + spinner.term.move_x(spinner_pos) + spinner.spinner_color + spinner.chars[0] + " " + suffix
