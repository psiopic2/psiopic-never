import unittest
from .ui_testHelper import getOutputString
from mock import MagicMock
from psiopic2.app.ui.widgets import ProgressBar

class ProgressBarWidgetTests(unittest.TestCase):

  def test_single_bar_no_label(self):
    pb = ProgressBar(width=12)
    pb.output = MagicMock()

    pb.render(1, 10)

    outputString = getOutputString(pb.output.call_args_list)

    # "[-         ]"

    # first render
    finalString = pb.bracket_color + pb.brackets[0]
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.brackets[1]

    # render the bar, without rendering the brackets
    finalString += pb.term.move_x(1)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    self.assertEquals(outputString, finalString)

  def test_single_bar_label(self):
    pb = ProgressBar(width=12, label="Foobar")
    pb.output = MagicMock()

    pb.render(1, 10)

    outputString = getOutputString(pb.output.call_args_list)

    # first render
    finalString = pb.label + " "
    finalString += pb.bracket_color + pb.brackets[0]
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.brackets[1]

    # render the bar
    finalString += pb.term.move_x(8)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    self.assertEquals(outputString, finalString)

  def test_single_bar_label_with_info(self):
    pb = ProgressBar(width=12, label="Foobar")
    pb.output = MagicMock()

    pb.render(1, 10, info="test")

    outputString = getOutputString(pb.output.call_args_list)
    
    # Foobar [-         ] test

    # first render
    finalString = pb.label + " "
    finalString += pb.bracket_color + pb.brackets[0]
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.brackets[1]

    # render the bar
    finalString += pb.term.move_x(8)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)

    # render the info
    finalString += pb.term.move_x(20)
    finalString += "test"

    self.assertEquals(outputString, finalString)

  def test_dual_bar_no_label(self):
    pb = ProgressBar(width=23, bars=2)
    pb.output = MagicMock()

    pb.render(1, 10, no=1)
    pb.render(2, 10, no=2)

    # [-         |--        ]

    # first render
    finalString = pb.bracket_color + pb.brackets[0]
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.separator_color + pb.separator_char
    finalString += pb.empty_char_color + (pb.empty_char * 10)
    finalString += pb.bracket_color + pb.brackets[1]

    # render the bar, without rendering the brackets
    finalString += pb.term.move_x(1)
    finalString += pb.fill_char_color + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 9)
    
    # render second bar
    finalString += pb.term.move_x(12)
    finalString += pb.fill_char_color + pb.fill_char + pb.fill_char
    finalString += pb.empty_char_color + (pb.empty_char * 8)

    outputString = getOutputString(pb.output.call_args_list)

    self.assertEquals(outputString, finalString)
