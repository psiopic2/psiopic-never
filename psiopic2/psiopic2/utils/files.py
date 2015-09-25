import os

singleArchiveTypes = [
  'tar',
  'bz2',
  'gz',
  '7z',
  'lha',
  'lhz',
  'tgz',
  'rar'
]

dualArchiveTypes = [
  'tar'
]

def getArchiveBasename(archive):
  
  baseFilename = os.path.basename(archive)
  
  pkgParts = baseFilename.split(".")
  
  if pkgParts[-1] in singleArchiveTypes:
    if pkgParts[-2] in dualArchiveTypes:
      arBasename = ".".join(pkgParts[:-2])
    else:
      arBasename = ".".join(pkgParts[:-1])
  elif pkgParts[-2] in dualArchiveTypes:
    arBasename = ".".join(pkgParts[:-2])
  else:
    arBasename = baseFilename
  
  return arBasename
