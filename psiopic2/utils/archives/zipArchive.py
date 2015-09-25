from psiopic2.utils.archives import BaseArchiveInfo
from psiopic2.utils.archives import BaseArchive
import zipfile

class ZipArchiveInfo(BaseArchiveInfo):
  def name(self):
    return self.infoObj.filename

  def size(self):
    return self.infoObj.file_size

  def type(self):
    if self.infoObj.filename.endswith('/'):
      return ArchiveInfo.TYPE_DIR
    else:
      return ArchiveInfo.TYPE_FILE    

class ZipArchive(BaseArchive):
  def __init__(self, archiveFile):
    super(self.__class__, self).__init__(archiveFile)
    self._archive = zipfile.ZipFile(archiveFile)

  def filenames(self):
    return self._archive.namelist()

  def getInfo(self, fn):
    return self._archive.getInfo(fn)


