import unittest
from psiopic2.app.ui.logutils import PsiopicFormatter

"""
Log template is simple

<color>[<color>name<color>:<color>level<color>] <color>msg

class LogFormatterTest(unittest.TestCase):

  def test_formatted_messages(self):
    formatter = PsiopicFormatter()
    
    record = LogRecord(
      name='psiopic2.test',
      level=logging.DEBUG,
      msg='debug msg',
    )

    logMsg = formatter.format(record)

    self.assertEquals(logMsg, 
"""
