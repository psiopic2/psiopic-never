from psiopic2.utils.archives import BaseArchiveInfo
from psiopic2.utils.archives import BaseArchive
import os
import bz2

class Bz2ArchiveInfo(BaseArchiveInfo):
  def __init__(self, fileName, archiveName):
    super(Bz2ArchiveInfo, self).__init__(fileName, archiveName)
    self._size = -1

  def name(self):
    return self.fileName

  def size(self):
    if self._size == -1:

      bz2obj = bz2.BZ2File(self.archiveName)
      bz2obj.seek(0, os.SEEK_END)
      self._size = bz2obj.tell()
      bz2obj.close()
      
    return self._size

  def type(self):
    return 'file'


class Bz2Archive(BaseArchive):
    def __init__(self, archiveFile):
      super(self.__class__, self).__init__(archiveFile)

    def filenames(self):

      fn = self.archiveFile.replace('.bz2','')

      return [os.path.basename(fn)]

    def getInfo(self, fn):

      destFile = os.path.dirname(self.archiveFile) + '/' + fn
      if destFile + '.bz2' != self.archiveFile:
        raise ValueError('File name must the archive file name minus the bz2 extension:')

      return Bz2ArchiveInfo(destFile, self.archiveFile)

    def open(self, fileName):
      return bz2.BZ2File(self.archiveFile)


