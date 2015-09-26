import unittest
from .ui_testHelper import getOutputString
from mock import MagicMock
from psiopic2.app.ui.widgets import ProgressBar

class ProgressBarWidgetTests(unittest.TestCase):

  def test_single_bar_no_label(self):
    pb = ProgressBar(width=10)
    pb.output = MagicMock()

    pb.render(1, 10)

    outputString = getOutputString(pb.output.call_args_list)

    # "[-         ]"

    # first render
    finalString = pb.bracket_color + pb.bracket_start_char
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.bracket_end_char

    # render the bar, without rendering the brackets
    finalString += pb.term.move_x(1)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    self.assertEquals(outputString, finalString)

  def test_single_bar_label(self):
    pb = ProgressBar(width=10, label="Foobar")
    pb.output = MagicMock()

    pb.render(1, 10)

    outputString = getOutputString(pb.output.call_args_list)

    # first render
    finalString = pb.label + " "
    finalString += pb.bracket_color + pb.bracket_start_char
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.bracket_end_char

    # render the bar
    finalString += pb.term.move_x(8)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    self.assertEquals(outputString, finalString)

  def test_single_bar_label_with_info(self):
    pb = ProgressBar(width=10, label="Foobar")
    pb.output = MagicMock()

    pb.render(1, 10, info="test")

    outputString = getOutputString(pb.output.call_args_list)
    
    # Foobar [-         ] test

    # first render
    finalString = pb.label + " "
    finalString += pb.bracket_color + pb.bracket_start_char
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.bracket_end_char

    # render the bar
    finalString += pb.term.move_x(8)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    # render the info
    finalString += pb.term.move_x(20)
    finalString += "test"

    self.assertEquals(outputString, finalString)
