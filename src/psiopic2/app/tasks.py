from psiopic2.app.ui import widgets
from psiopic2.utils.archives import Archive
from psiopic2.utils.archives import ArchiveInfo
from psiopic2.utils.database import Database
from psiopic2.utils import wikiextractor
from psiopic2.corpus import pages
import logging
import os, errno
import time
import requests
import sys
import xml
from subprocess import Popen, PIPE
import shutil
import pexpect
from psiopic2.utils.wikiextractor import WikiExtractorServer,\
  WikiExtractorClient

class TaskException(Exception):
  def __init__(self, message):
    super(TaskException, self).__init__(message)

class BaseTask(object):
  def __init__(self, conf):
    self.log = logging.getLogger('psiopic.' + self.__class__.__name__)
    self.conf = conf
    self.name = self.__class__.__name__
    
    if 'no-colors' in conf:
      self.colors = not conf['no-colors']
    else:
      self.colors = True
      
    if 'no-widgets' in conf:
      self.widgets = not conf['no-widgets']
    else:
      self.widgets = True
      
  def run(self, **kwargs):
    raise NotImplementedError
    
class SpinnerTask(BaseTask):
  def __init__(self, conf):
      super(SpinnerTask, self).__init__(conf)
      self.spinner = None


  def progress(self, label=None):
    if self.widgets:
      if self.spinner == None:
        self.spinner = widgets.Spinner()
      self.spinner.render(label)
    else:
      if label != None:
        self.log.debug("%s" % label)

class DatabaseTask(BaseTask):
  def __init__(self, conf):
    super(DatabaseTask, self).__init__(conf)
    self._db = None

  def getDatabase(self):
    if self._db == None:
      self._db = Database(
        dbtype = self.conf['dbtype'],
        dbport = self.conf['dbport'],
        dbname = self.conf['dbname'],
        dbhost = self.conf['dbhost'],
        dbpass = self.conf['dbpass'],
        dbuser = self.conf['dbuser']
      )
    return self._db


class ProgressTask(BaseTask):
  def __init__(self, conf):
    super(ProgressTask, self).__init__(conf)
    self.bar = None
    self.total = 0

  def progress(self, dl, total, info=None, no=1):
    if self.widgets:
      if self.bar == None:
        self.bar = widgets.ProgressBar()
      self.bar.render(dl, total, info, no)
      sys.stdout.flush()
    else:
      if info:
        self.log.debug(info)
      else:
        self.log.debug('%s/%s' % (dl, total))

  def run(self):
    raise NotImplementedError

class BaseTableTask(DatabaseTask):
  def __init__(self, conf):
    super(BaseTableTask, self).__init__(conf)
    self.tables = [
      'archive',
      'category',
      'categorylinks',
      'change_tag',
      'externallinks',
      'filearchive',
      'image',
      'imagelinks',
      'interwiki',
      'ipblocks',
      'iwlinks',
      'job',
      'l10n_cache',
      'langlinks',
      'logging',
      'log_search',
      'module_deps',
      'msg_resource',
      'msg_resource_links',
      'objectcache',
      'oldimage',
      'page',
      'pagelinks',
      'page_props',
      'page_restrictions',
      'protected_titles',
      'querycache',
      'querycache_info',
      'querycachetwo',
      'recentchanges',
      'redirect',
      'revision',
      'searchindex',
      'site_identifiers',
      'sites',
      'site_stats',
      'tag_summary',
      'templatelinks',
      'text',
      'transcache',
      'updatelog',
      'uploadstash',
      'user',
      'user_former_groups',
      'user_groups',
      'user_newtalk',
      'user_properties',
      'valid_tag',
      'watchlist'
    ]

class GetDatabaseFromConfig(BaseTask):
  def __init__(self, **kwargs):
    super(GetDatabaseFromConfig, self).__init__(**kwargs)
    self.mediawikiDir = kwargs.get('mediawikiDir')
    
  def _getValue(self, configLine):
    return configLine.split('=')[1].strip()[1:-2]
    
  def run(self):
    f = open(self.mediawikiDir + "/LocalSettings.php")
    
    dbparams = {}
    
    for line in f:
      if line.startswith('$wgDBserver'):
        dbparams['host'] = self._getValue(line)
      elif line.startswith('$wgDBname'):
        dbparams['name'] = self._getValue(line)
      elif line.startswith('$wgDBuser'):
        dbparams['user'] = self._getValue(line)
      elif line.startswith('$wgDBpassword'):
        dbparams['pass'] = self._getValue(line)
        
    return dbparams

class WikiExtractor(DatabaseTask):
  def __init__(self, **kwargs):
    super(WikiExtractor, self).__init__(**kwargs)
    self.mediawikiDir = kwargs.get('mediawikiDir')
    self.wikiextractor = kwargs.get('wikiextractor')
    self.host = kwargs.get('host')
    self.port = kwargs.get('port')
    self.target = kwargs.get('target')
    
    
  def run(self):
    if (self.wikiextractor):
      self.weServer = WikiExtractorServer(
        host=self.host,
        port=self.port,
        mwdir=self.mediawikiDir,
        script=self.wikiextractor
      )
    
      self.log.info("Starting WikiExtractor server")
      self.weServer.start()
    
    self.log.info("Getting database")
    db = self.getDatabase()
    
    self.log.debug('Getting total rows')
    cur = db.execute('SELECT count(*) FROM page WHERE page_namespace=0')
    count = cur.fetchone()[0]
    
    cur = db.execute('SELECT page_id FROM page WHERE page_namespace=0 ORDER BY page_id ASC');
    
    queue = []
    
    maxjobs = 1
    jobpids = []
    
    running = True
    
    total_done = 0
    
    while running:
      
      if len(jobpids) >= maxjobs:
        try:
          pid, exitCode = os.waitpid(0, os.WNOHANG)
          if (pid != 0):
            if pid in jobpids:
              self.log.warning("%s finished!" % pid)
              maxjobs -= 1
              jobpids.remove(pid)
              self.log.warning('Total jobs: %s' % len(jobpids))
              
        except OSError, e:
          if e.errno != 10:
            raise e
            
          
      if len(queue) == 1000:
        if len(jobpids) < maxjobs:
          child_queue = queue[:]
          
          pid = os.fork()
          if pid == 0:
            """ child """
            cpid = os.getpid()
            running = False
            we = WikiExtractorClient(self.host, self.port)
            self.log.debug("(%s) Connecting to %s:%s" % (cpid, self.host, self.port))
            we.connect()
            count = len(child_queue)
            total = 0
            for id in child_queue:
              self.log.debug("(%s) Retreiving %s %s/%s" % (cpid, id, total, count))
              we.getArticle(id)
              self.log.debug("(%s) Processing %s %s/%s" % (cpid, id, total, count))
              total += 1
              
            self.log.debug("(%s) Job task finished, exiting" % cpid)  
            we.disconnect()
            sys.exit(0)
          elif pid > 0:
            """ parent """
            self.log.debug("Job task started at %s" % pid)
            jobpids.append(pid)
            queue = []
      else:
        row = cur.fetchone()
        if row:
          # self.log.debug("Queing up page #%s" % row[0])
          self.log.debug("queuing page #%s" % row[0])
          queue.append(row[0])
        else:
          self.log.debug('Iterated over all page ids')
          if len(jobpids) == 0:
            running = False
          
          
    self.log.warning("Stopping server")
    
    if self.wikiextractor:
      self.weServer.disconnect()
        
    
    
    
class TableTruncator(BaseTableTask, SpinnerTask):
  def run(self):
    db = self.getDatabase()
    
    for table in self.tables:
      sql = 'TRUNCATE TABLE %s' % table
      self.progress(sql)
      db.execSql(sql)
                
class TableCreator(BaseTableTask, SpinnerTask):
  def __init__(self, conf):
    super(TableCreator, self).__init__(conf)

  def run(self, **kwargs):
    installDir = kwargs.get('src')
    
    
    db = self.getDatabase()
    mwTableSqlFile = installDir + "/maintenance/tables.sql"
    initSqlFile = os.path.dirname(__file__) + '/../resources/init.sql'

    sql = ""
    
    if os.path.exists(mwTableSqlFile) == False:
      raise TaskException('%s does not exist. Is mediawiki installed?' % mwTableSqlFile)

    for line in open(mwTableSqlFile, 'r'):
      if line.strip().startswith('--'):
        continue

      sql += line.strip() + " "

      if line.strip().endswith(';'):
        self.progress('Creating Mediawiki tables...')
        db.execSql(sql)
        sql = ""

    for line in open(initSqlFile, 'r'):
      if line.strip().startswith('--'):
        continue
      sql += line.strip() + " "

      if line.strip().endswith(';'):
        self.progress('Initializing some tables with data')
        db.execSql(sql)
        sql = ""

    for table in self.tables:
      sql = 'ALTER TABLE %s CONVERT TO CHARACTER SET utf8 COLLATE utf8_bin' % table
      self.progress('Ensuring all tables have utf8_bin collation')
      db.execSql(sql)
      
    sys.stdout.write("\n")
      
class XmlCleaner(BaseTask):
  def __init__(self, conf):
    super(XmlCleaner, self).__init__(conf)

  def run(self, **kwargs):
    
    src = kwargs['src']
    target = kwargs['target']
    
    srco = open(src)
    targeto = open(target, 'w')

    filterEnabled = False

    for line in srco:
      if filterEnabled == False:
        if line.strip() != "<DiscussionThreading>":
          targeto.write(line)
        else:
          filterEnabled = True
      else:
        if line.strip() == "</DiscussionThreading>":
          filterEnabled = False
    
    srco.close()
    targeto.close()

class Xml2Sql(BaseTask):
  def __init__(self, conf):
    super(Xml2Sql, self).__init__(conf)
    self.xml2sql = os.path.dirname(__file__) + "/../resources/xml2sql/mediawiki-xml2sql/xml2sql"

  def run(self, **kwargs):
    
    target = kwargs['target']
    src = kwargs['src']
    
    try:
      os.makedirs(target)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

    cmd = [self.xml2sql, '-m', '-v', '-o', target, src]
    
    xml2sql = Popen(cmd, shell=False, bufsize=1, stdout=PIPE)
    line = ""
    
    while True:
      byte = xml2sql.stdout.read(1)
      if byte:
        if byte == "\r":
          self.log.debug(line)
          sys.stdout.flush()
          line = ""
        else:
          line += byte
      else:
        break
        
    xml2sql.stdout.close()
    xml2sql.wait()
        

class CompileXml2Sql(BaseTask):
  def __init__(self, conf):
    super(CompileXml2Sql, self).__init__(conf)
   
    self.src = os.path.dirname(__file__) + "/../resources/xml2sql/mediawiki-xml2sql"

  def run(self):
    
    oldcwd = os.getcwd()
    
    os.chdir(self.src)

    self.log.info('Cleaning up xml2sql')
    makeClean = Popen(['make', 'clean'], shell=True, bufsize=1, stdout=PIPE, stderr=PIPE)
    for line in makeClean.stdout:
      self.log.debug(line.strip())
      sys.stdout.flush()

    makeClean.stdout.close()
    makeClean.stderr.close()
    makeClean.wait()


    for d in ['.deps','getopt/.depts']:
      try:
        os.rmdir(d)
      except OSError, e:
        if e.errno != 2:
          self.log.warning('Unable to delete %s/%s: %s' % (self.src, d, e.strerror))

          
    for f in ['config.h', 'config.log', 'config.status', 'getopt/Makefile', 'Makefile', 'stamp-h1']:
      try:
        os.remove(f)
      except OSError, e:
        if e.errno != 2:
          self.log.warning('Unable to delete %s/%s: %s' % (self.src, f, e.strerror))
          

    self.log.info('Compiling xml2sql')
    configure = Popen(['./configure'], shell=True, bufsize=1, stdout=PIPE)
    for line in configure.stdout:
      self.log.debug(line.strip())
      sys.stdout.flush()
    
    configure.stdout.close()
    configure.wait()

    make = Popen(['make'], shell=True, bufsize=1, stdout=PIPE)
    for line in make.stdout:
      self.log.debug(line.strip())
      sys.stdout.flush()

    make.stdout.close()
    make.wait()

    os.chdir(oldcwd)
    

class SqlImporter(DatabaseTask, ProgressTask):
  def __init__(self, conf):
    super(SqlImporter, self).__init__(conf)
    
  def run(self, **kwargs):
    
    import warnings
    
    page = kwargs.get('pageSql')
    revision = kwargs.get('revisionSql')
    text = kwargs.get('textSql')
    
    db = self.getDatabase()
    sql = ""
    
    for sqlFile in [page, revision, text]:
      sqlFileSize = os.path.getsize(sqlFile)
      
      totalSqlFileRead = 0
      
      f = open(sqlFile)
      
      for line in f:
        if line.strip().startswith('--') == True:
          totalSqlFileRead += len(line)
          continue

        sql += line.strip() + " "

        if line.strip().endswith(';'):
          # xml2sql inserts this line
          # /*!40000 ALTER TABLE `page` DISABLE KEYS */
          # sql = sql.decode("utf-8").replace("/*!40000 ALTER TABLE `%s` DISABLE KEYS */" % sqlFile, "").strip()
          
          if sql != ";":
            warnings.filterwarnings('ignore')
            db.execSql(sql)
            warnings.filterwarnings('always')
            
          sql = ""
          
          totalSqlFileRead += len(line)
          
          self.progress(totalSqlFileRead, sqlFileSize, 'Importing ' + sqlFile)
    
    sys.stdout.write("\n")
    
class MWConfigWriter(ProgressTask):
  def __init__(self, conf):
    super(MWConfigWriter, self).__init__(conf)

  def run(self, **kwargs):

    try:
      target = kwargs['target']
      dbhost = kwargs['dbhost']
      dbport = kwargs['dbport']
      dbuser = kwargs['dbuser']
      dbpass = kwargs['dbpass']
      dbname = kwargs['dbname']
      dbtype = 'mysql'
    except KeyError as e:
      raise TaskException('Missing required paramter: %s' % e.message)
      
    curdir = os.path.dirname(__file__)
    conffile = curdir + "/../resources/LocalSettings.php"

    total_size = os.path.getsize(conffile)
    read_size = 0

    with open(target + "/LocalSettings.php", 'w') as f:
      for line in open(conffile):
        read_size += len(line)

        if line.startswith('$wgDBtype'):
          line = line.replace('REPLACE_ME', dbtype)
        elif line.startswith('$wgDBserver'):
          line = line.replace('REPLACE_ME', dbhost + ':' + str(dbport))
        elif line.startswith('$wgDBname'):
          line = line.replace('REPLACE_ME', dbname)
        elif line.startswith('$wgDBuser'):
          line = line.replace('REPLACE_ME', dbuser)
        elif line.startswith('$wgDBpassword'):
          line = line.replace('REPLACE_ME', dbpass)
        
        f.write(line)
        
        if self.widgets:
          self.progress(read_size, total_size)
    
    if self.widgets:
      sys.stdout.write("\n")   

class DumpExtractor(SpinnerTask):
  def __init__(self, conf):
    super(DumpExtractor, self).__init__(conf)
    
  def run(self, src, target):
    chunk_size = 4098

    archive = Archive(src)

    fileNames = archive.filenames()

    total_files = 0

    for fn in fileNames:
      dirName = os.path.dirname(fn) or fn
      if os.path.isdir(dirName) == False:
        os.makedirs(dirName)

      fInfo = archive.getInfo(fn)
      if fInfo.type() == 'file':
        targetFile = target + "/" + fn
        if os.path.isdir(os.path.dirname(targetFile)) == False:
          os.makedirs(os.path.dirname(targetFile))

        targetFobj = open(targetFile, 'wb')
        f = archive.open(fn)
        total_read = 0
        while 1:
          data = f.read(chunk_size)
          if not data:
            break;
          
          total_read += len(data)
          targetFobj.write(data)
          
          
          if self.widgets:
            self.progress(fn)

      total_files += 1
    
    if self.widgets:
      sys.stdout.write("\n")
    return True

class Extractor(ProgressTask):
  def __init__(self, conf):
    super(Extractor, self).__init__(conf)

    self.bar = widgets.ProgressBar(bars=2)

    

  def run(self, src, target):

    chunk_size = 4098

    archive = Archive(src)

    fileNames = archive.filenames()

    total_files = 0

    for fn in fileNames:
      dirName = os.path.dirname(fn) or fn
      if os.path.isdir(dirName) == False:
        os.makedirs(dirName)

      fInfo = archive.getInfo(fn)
      if fInfo.type() == 'file':
        targetFile = target + "/" + fn
        if os.path.isdir(os.path.dirname(targetFile)) == False:
          os.makedirs(os.path.dirname(targetFile))

        targetFobj = open(targetFile, 'wb')
        f = archive.open(fn)
        total_read = 0
        while 1:
          data = f.read(chunk_size)
          if not data:
            break;
          
          total_read += len(data)
          targetFobj.write(data)
          if self.widgets and archive.getType != '.bz2':
            self.progress(total_read, fInfo.size(), fn, 2)

      total_files += 1
      if self.widgets:
        self.progress(total_files, len(fileNames), None, 1)
      else:
        self.log.debug("Extracted: %s" % fn)
    
    if self.widgets:
      sys.stdout.write("\n")
    return True

class XmlImporter(DatabaseTask):
  def __init__(self, **kwargs):
    super(XmlImporter, self).__init__(**kwargs)
    self.xmlFile = kwargs.get('xmlFile')

    self._pageQueue = []
    self._maxPageQueue = 10000
    self.pages = 0

  def run(self):
    db = self.getDatabase()

    source = open(self.xmlFile)
    xml.sax.parse(source, pages.XmlParser(self))
    
  def page(self, page):
    self.pages += 1
    self._pageQueue.append(page)

    if len(self._pageQueue) == self._maxPageQueue:
      db = self.getDatabase()

      pageValues = []
      textValues = []
      rcValues = []
      revValues = []

      for page in self._pageQueue:
        pageValues.append(page.getPageValueArray())
        textValues.append(page.getTextValueArray())
        rcValues.append(page.getRecentChangesValueArray())
        revValues.append(page.getRevisionValueArray())


      db.executeMany(page.insertPageQuery, pageValues)
      db.executeMany(page.insertTextQuery, textValues)
      db.executeMany(page.insertRecentChangesQuery, rcValues)
      db.executeMany(page.insertRevisionQuery, revValues)
      self._pageQueue = []

    self.progress('%s page(s)' % self.pages)
    
 
class Downloader(ProgressTask):
  def __init__(self, conf):
    super(Downloader, self).__init__(conf)
    
    self.name = "Downloader"

  def run(self, **kwargs):
    
    src = kwargs.get('src')
    target = kwargs.get('target') + "/" + os.path.basename(src)
    
    self.log.debug('downloading %s to %s' % (src, target))

    target_dir = os.path.dirname(target)

    if os.path.isdir(target_dir) == False:
      os.makedirs(target_dir)

    r = requests.get(src, stream=True)
    r.raise_for_status()
    total_length = int(r.headers.get('content-length'))
   
    with open(target, 'wb') as f: 
      if total_length is None:
        f.write(r.content)
      else:
        dl = 0

        for chunk in r.iter_content(1024):
          dl += len(chunk)
          f.write(chunk)
          self.progress(dl, total_length, info="%s / %s bytes" % (dl, total_length))
    
    if self.widgets:
      sys.stdout.write(os.linesep)

    return True


