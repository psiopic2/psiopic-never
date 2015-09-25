__all__ = ['BaseArchive', 'BaseArchiveInfo',
           'TarArchive', 'TarArchiveInfo',
           'ZipArchive', 'ZipArchiveInfo',
           'Bz2Archive', 'Bz2ArchiveInfo']
           

from psiopic2.utils.archives.baseArchive import BaseArchive
from psiopic2.utils.archives.baseArchive import BaseArchiveInfo

from psiopic2.utils.archives.tarArchive import TarArchiveInfo
from psiopic2.utils.archives.tarArchive import TarArchive
from psiopic2.utils.archives.zipArchive import ZipArchiveInfo
from psiopic2.utils.archives.zipArchive import ZipArchive

from psiopic2.utils.archives.bz2Archive import Bz2ArchiveInfo
from psiopic2.utils.archives.bz2Archive import Bz2Archive


import os
import tarfile
import zipfile

EXTENSION_MAP = {
    '.docx': ZipArchive,
    '.egg': ZipArchive,
    '.jar': ZipArchive,
    '.odg': ZipArchive,
    '.odp': ZipArchive,
    '.ods': ZipArchive,
    '.odt': ZipArchive,
    '.pptx': ZipArchive,
    '.tar': TarArchive,
    '.tar.bz2': TarArchive,
    '.tar.gz': TarArchive,
    '.tgz': TarArchive,
    '.tz2': TarArchive,
    '.xlsx': ZipArchive,
    '.zip': ZipArchive,
    '.bz2': Bz2Archive
}  




class UnsafeArchive(Exception):
  pass


class ArchiveInfo(object):

  def __init__(self, infoObj):
    self.infoObj = infoObj

  def name(self):
    return self.infoObj.name()

  def size(self):
    return self.infoObj.size()

  def type(self):
    return self.infoObj.type()


class Archive():
  def __init__(self, archiveFile):
    self.archiveFile = archiveFile

    filenameParts = os.path.basename(self.archiveFile).split('.')
    
    if len(filenameParts) == 2:
      self._type = "." + filenameParts[1]
    else:
      type = "." + ".".join(filenameParts[-2:])
      if type in EXTENSION_MAP:
        self._type = type
      elif "." + filenameParts[-1] in EXTENSION_MAP:
        self._type = "." + filenameParts[-1] 

    self._archive = EXTENSION_MAP[self._type](self.archiveFile)
    
  def getType(self):
    return self._type

  def filenames(self):
    """
    Get a list of file names in the archive
    """
    return self._archive.filenames()

  def getInfo(self, fileName):
    """
    Get an info object for fileName
    """
    return ArchiveInfo(self._archive.getInfo(fileName))

  def open(self, fileName):
    """
    Opens fileName and returns file-like object to read from
    """
    return self._archive.open(fileName)

  def check_file(self, fileName):
    """
    Check if fileName has a safe path
    """
    return self._archive.check_files(fileName)


