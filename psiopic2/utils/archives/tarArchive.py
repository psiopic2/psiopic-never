from psiopic2.utils.archives import BaseArchiveInfo
from psiopic2.utils.archives import BaseArchive
import tarfile

class TarArchiveInfo(BaseArchiveInfo):

  def __init__(self, fileName, tarArchive):
    super(TarArchiveInfo, self).__init__(fileName, tarArchive.name)
    self._archive = tarArchive
    self._infoObj = self._archive.getmember(fileName)
    
  def name(self):
    return self._infoObj.name

  def size(self):
    return self._infoObj.size

  def type(self):
    if self._infoObj.isdir():
      return 'dir'
    else:
      return 'file'


class TarArchive(BaseArchive):
  def __init__(self, archiveFile):
    super(self.__class__, self).__init__(archiveFile)
    self._archive = tarfile.open(archiveFile)       

  def filenames(self):
    return self._archive.getnames()

  def getInfo(self, fn):
    return TarArchiveInfo(fn, self._archive)

  def open(self, fn):
    return self._archive.extractfile(fn)


