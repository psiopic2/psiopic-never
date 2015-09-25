import os

class BaseArchiveInfo(object):

  def __init__(self, fileName, archiveName):
    self.fileName = fileName
    self.archiveName = archiveName

  def name(self):
    raise NotImplementedError

  def size(self):
    raise NotImplementedError

  def type(self):
    raise NotImplementedError

class BaseArchive(object):
  def __init__(self, archiveFile):
    self.archiveFile = archiveFile
    self._archive = None

  def open(self, fileName):
    raise NotImplementedError()

  def getInfo(self, fileName):
    raise NotImplementedError()

  def check_file(self, fileName, targetDir=None):
    if targetDir:
      targetPath = os.path.normpath(os.path.realpath(targetDir))
    else:
      targetPath = os.getcwd()

    extract_path = os.path.join(targetPath, src)
    extract_path = os.path.normpath(os.path.realpath(extract_path))

    if not extract_path.startswith(targetPath):
      raise UnsafeArchive("%s is outside of %s" % (src, targetPath))
    
  def filenames(self):
    raise NotImplementedError()

