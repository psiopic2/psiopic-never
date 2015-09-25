from docopt import docopt
from appdirs import AppDirs
from urlparse import urlparse
import sys
import os
import shutil
import time
import logging
from psiopic2.app.baseApp import Arg, BaseApp
from psiopic2.app.baseApp import BASE_OPTIONS
from psiopic2.app.baseApp import BASE_ARGS
from psiopic2.corpus import pages
from psiopic2.app.tasks import Extractor, SqlImporter, TableTruncator
from psiopic2.app.tasks import Downloader
from psiopic2.app.tasks import MWConfigWriter
from psiopic2.app.tasks import TableCreator
from psiopic2.app.tasks import XmlImporter
from psiopic2.app.tasks import CompileXml2Sql
from psiopic2.app.tasks import XmlCleaner
from psiopic2.app.tasks import Xml2Sql
from psiopic2.app.tasks import DumpExtractor
from psiopic2.app.ui.logutils import getLogger
import psiopic2.app.ui.widgets as widgets
import psiopic2.app.ui.prompt as prompt
from urlparse import urlparse
from datetime import datetime
from imp import PKG_DIRECTORY
from psiopic2.utils.files import getArchiveBasename


# WIKINEWS_URL = "http://dumps.wikimedia.org/enwikinews/latest/enwikinews-latest-pages-articles.xml.bz2"

MEDIAWIKI_URL = "http://download.wikimedia.org/mediawiki/1.25/mediawiki-1.25.2.tar.gz"
WIKINEWS_URL = "http://dumps.wikimedia.org/enwikinews/20150901/enwikinews-20150901-pages-articles.xml.bz2"

MEDIAWIKI_DIR = "mediawiki-1.25.2"

sysDirs = AppDirs('Psiopic2', 'Psikon')

ARGS = [
  Arg(
    title='Installion Directory', 
    description='Path to where Mediawiki should be installed',
    name='install-dir',
    valueDesc='DIR',
    defaultValue=sysDirs.user_cache_dir + '/mediawiki'),
  Arg(
    title='Database hostname',
    description='Hostname or IP address for your MySQL database',
    name='dbhost',
    valueDesc='HOST',
    defaultValue='localhost'),
  Arg(
    title='Database port',
    description='Port number of your MySQL database',
    name='dbport',
    valueDesc='PORT',
    defaultValue=3306),
  Arg(
    title='Database username',
    description='MySQL Username',
    name='dbuser',
    valueDesc='USER',
    defaultValue='root'),
  Arg(
    title='Database password',
    description='Password for MySQL user',
    name='dbpass',
    valueDesc='PASS',
    defaultValue='root'),
  Arg(
    title='Database schema name',
    description='The database schema must already exist',
    name='dbname',
    valueDesc='NAME',
    defaultValue=None),
  Arg(
    title='Database type',
    description='Database type. Currently the only acceptable value is mysql',
    name='dbtype',
    valueDesc='TYPE',
    defaultValue='mysql'),
  Arg(
    title='Mediawiki URL',
    description='URL to the Mediawiki software tarball',
    name='mediawiki-url',
    valueDesc='URL',
    defaultValue=MEDIAWIKI_URL),
  Arg(
    title='XML Dump URL',
    description='URL to the XML database dump',
    name='xml-dump',
    valueDesc='URL',
    defaultValue=WIKINEWS_URL),
  Arg(
    title='Skip Database',
    description='Skip creating the database tables',
    name='skip-db',
    defaultValue=False,
    prompt=False),
  Arg(
    title='Force database table creation',
    description='Force creating the database tables',
    name='force-db',
    defaultValue=False,
    prompt=False),
  Arg(
    title='Skip Mediawiki Installation',
    description='Skip downloading and installing Mediawiki',
    name='skip-mw-install',
    defaultValue=False,
    prompt=False),
  Arg(
    title='Skip XML Import',
    description='Skip importing the XML database',
    name='skip-import',
    defaultValue=False,
    prompt=False),
  Arg(
    title='Skip XML Download',
    description='Skip downloading the XML database',
    name='skip-xml-download',
    defaultValue=False,
    prompt=False),
  Arg(
    title='Force Mediawiki Installation',
    description='If Mediawiki is already installed, this flag will a reinstallation but will not create database tables',
    defaultValue=False,
    name='force-mw-install',
    prompt=False),
  Arg(
    title='Force XML Import',
    description='If the XML database dump already exists, this flag will force it to be reimported',
    defaultValue=False,
    name='force-import',
    prompt=False),
  Arg(
    title='Force XML Download',
    description='If the XML database dump already exists, this flag will force it to be downloaded and extracted again',
    defaultValue=False,
    name='force-xml-download',
    prompt=False),
  Arg(
    title='Truncate database tables',
    description='If enabled, all database tables will be truncated',
    defaultValue=False,
    name='truncate',
    prompt=False)
] + BASE_ARGS



def getFinalMediawikiDir(app):
  return app.getArg('install-dir') + '/' + getArchiveBasename(app.getArg('mediawiki-url'))

def setupXmlDownloadWorkflow(app):
  finalInstallDir = getFinalMediawikiDir(app)
  
  pkg = os.path.basename(app.getArg('xml-dump'))
  
  finalBz2File = finalInstallDir + '/' + pkg
  
  app.addTask(Downloader, {
    'src': app.getArg('xml-dump'),
    'target': finalInstallDir,
  }, 'Downloading XML database dump')
  
  app.addTask(DumpExtractor, {
    'src': finalBz2File,
    'target': finalInstallDir
  })

def setupXmlImportingWorkflow(app):
  
  mwDir = getFinalMediawikiDir(app)
  xmlFileIn = mwDir + '/' + getArchiveBasename(app.getArg('xml-dump'))
  xmlFileOut = mwDir + '/cleaned-xml-database.xml'
  
  app.addTask(CompileXml2Sql, {}, 'Compiling the xml2sql tool')

  if os.path.exists(xmlFileOut) == False or app.getArg('force-import') == True:  
    app.addTask(XmlCleaner, {
      'src': xmlFileIn,
      'target': xmlFileOut
    }, 'Removing incompatible tags from the XML database')
    
  if (os.path.exists(mwDir + '/page.sql') == False or 
   os.path.exists(mwDir + '/revision.sql') == False or 
   os.path.exists(mwDir + '/text.sql') == False or 
   app.getArg('force-import') == True):
    app.addTask(Xml2Sql, {
      'src': xmlFileOut,
      'target': mwDir
    }, 'Converting XML database to SQL statements')
  
  
  app.addTask(SqlImporter, {
    'pageSql': mwDir + '/page.sql',
    'revisionSql': mwDir + '/revision.sql',
    'textSql': mwDir + '/text.sql'
  }, 'Importing SQL statements to database')
  

def setupTableWorkflow(app):
  finalInstallDir = getFinalMediawikiDir(app)
  
  app.addTask(TableCreator, {
    'src': finalInstallDir,
    'dbtype': app.getArg('dbtype'),
    'dbhost': app.getArg('dbhost'),
    'dbport': app.getArg('dbport'),
    'dbuser': app.getArg('dbuser'),
    'dbpass': app.getArg('dbpass'),
    'dbname': app.getArg('dbname')
  })

def setupTruncateWorkflow(app):
  app.addTask(TableTruncator, {}, 'Truncating all tables')

def setupMediawikiWorkflow(app):
  
  pkg = os.path.basename(app.getArg('mediawiki-url'))
  finalInstallDir = getFinalMediawikiDir(app)
  
  app.addTask(Downloader, {
    'src': app.getArg('mediawiki-url'),
    'target': app.getArg('install-dir')
  }, 'Downloading Mediawiki')
  
  app.addTask(Extractor, {
    'src': app.getArg('install-dir') + '/' + pkg,
    'target': app.getArg('install-dir')
  }, 'Extracting Mediawiki')
  
  app.addTask(MWConfigWriter, {
    'target': finalInstallDir,
    'dbhost': app.getArg('dbhost'),
    'dbport': app.getArg('dbport'),
    'dbuser': app.getArg('dbuser'),
    'dbpass': app.getArg('dbpass'),
    'dbname': app.getArg('dbname')
  })

def SetupWiki(argv):
  
  app = BaseApp('setupwiki', argv, '0.0.1', title='Setup Wiki')
  for arg in ARGS:
    app.addArg(arg)  
  
  if "-h" in argv or "--help" in argv:
    app.help()
    return 0
    
  if "-v" in argv or "--version" in argv:
    app.version()
    return 0  
    
  app.initConfiguration()
  
  if (os.path.exists(app.getArg('install-dir')) == False and app.getArg('skip-mw-install') == False) or app.getArg('force-mw-install') == True:
    setupMediawikiWorkflow(app)

  if (app.getArg('skip-db') == False or app.getArg('force-db') == True):
    setupTableWorkflow(app)
    
  if (app.getArg('truncate') == True):
    setupTruncateWorkflow(app)
  
  xmlFileZip = getFinalMediawikiDir(app) + '/' + os.path.basename(app.getArg('xml-dump'))
  xmlFile = getFinalMediawikiDir(app) + '/' + getArchiveBasename(app.getArg('xml-dump'))
  xmlImport = False
  
  if (os.path.exists(xmlFileZip) != True and app.getArg('skip-xml-download') == False) or app.getArg('force-xml-download') == True:
    setupXmlDownloadWorkflow(app)
    xmlImport = True
    
  
  if (os.path.exists(xmlFile) == True and app.getArg('skip-import') == False) or app.getArg('force-import') == True or xmlImport == True:
    setupXmlImportingWorkflow(app)
  
    
  app.run()

  
"""
class SetupWiki(object):
  
  def run(self):
    app = BaseApp('setupwiki', sys.argv, '0.0.1', title="Setup Wiki")
    
    for arg in ARGS:
      app.addArg(arg)
      
    app.initConfiguration()
    
    if app.getArg('truncate'):
      app.addTask(TableTruncator)
    
    return app.run()    

class SetupWiki(PromptingBaseApp):
  def __init__(self):
    super(SetupWiki, self).__init__(DOCSTRING)
    self.log = logging.getLogger('psiopic.SetupWiki')

    self.startTime = None
    self.endTime = None

  def run(self):
    self.startTime = datetime.now()
    args = self.getAargs()
    ret = 0
    
    mediawikiUrl = self.getValue('Mediaiki URL', 'mediawiki-url', MEDIAWIKI_URL)
    installDir = self.getValue('Mediawiki installation directory', 'install-dir', )
    

    urlPath = urlparse(self.mediawikiUrl).path
    downloadTarget = self.installDir + "/" + os.path.basename(urlparse(self.mediawikiUrl).path)

    if self.clean:
      self.log.warning("Cleaning previous installation")
      shutil.rmtree(self.mediawikiDir)
      self.args['--force-truncate'] = True
      
      
    if (os.path.isfile(downloadTarget) == False and self.args['--skip-download-mw'] != True) or self.args['--force-download-mw'] == True:
      self.log.info('Downloading Mediawiki software')

      self.args['--force-extract-mw'] = True
      
      Downloader(
        src=self.mediawikiUrl,
        target=downloadTarget, 
        colors=self.args['colors'], 
        widgets=self.args['widgets']
      ).run()
      
    if os.path.isfile(self.mediawikiDir + '/xmldb.xml.bz2') == False:
      self.log.info('Downloading Wikinews XML dump')
      
      Downloader(
        src=self.xmlDump,
        target=self.mediawikiDir + '/xmldb.xml.bz2',
        colors=self.args['colors'],
        widgets=self.args['widgets']
      ).run()      

    if (os.path.isdir(self.mediawikiDir) == False and self.args['--skip-extract-mw'] != True) or self.args['--force-extract-mw'] == True:
      self.log.info("Extracting Mediawiki software")

      Extractor(
        src=downloadTarget, 
        target=self.installDir, 
        colors=self.args['colors'], 
        widgets=self.args['widgets']
      ).run()


    if os.path.isfile(self.mediawikiDir + "/LocalSettings.php") == False:
      self.log.info("Writing config file")
      MWConfigWriter(
        target=self.mediawikiDir,
        dbhost=self.args.get('--dbhost'),
        dbname=self.args.get('--dbname'),
        dbpass=self.args.get('--dbpass'),
        dbuser=self.args.get('--dbuser'),
        dbtype=self.args.get('--dbtype')
      ).run()

    if self.args['--skip-db'] != True or self.args['--force-db'] == True:
   
        self.log.info("Creating database tables")

        TableCreator(
          installDir=self.mediawikiDir,
          dbhost=self.args.get('--dbhost') or self.installDir + "/mw.db",
          dbport=self.args.get('--dbport'),
          dbuser=self.args.get('--dbuser'),
          dbpass=self.args.get('--dbpass'),
          dbname=self.args.get('--dbname'),
          dbtype=self.args.get('--dbtype') or 'sqlite'
        ).run()
        
    if self.args['--force-truncate'] == True:
      self.log.info("Truncating database tables")
      
      TableTruncator(
        dbhost=self.args.get('--dbhost') or self.installDir + "/mw.db",
        dbport=self.args.get('--dbport'),
        dbuser=self.args.get('--dbuser'),
        dbpass=self.args.get('--dbpass'),
        dbname=self.args.get('--dbname'),
        dbtype=self.args.get('--dbtype') or 'sqlite'                     
      ).run()
      



    if os.path.isfile(self.mediawikiDir + '/xmldb.xml') == False:
      self.log.info('Extracting XML zip')
      Extractor(
        src=self.mediawikiDir + '/xmldb.xml.bz2',
        target=self.mediawikiDir,
        colors=self.args['colors'],
        widgets=self.args['widgets']
      ).run()

    self.log.info("Compiling the xml2sql tool")
    CompileXml2Sql().run() 

    self.log.info("Cleaning XML database of unused tags")
    XmlCleaner(src=self.mediawikiDir + '/xmldb.xml', target=self.mediawikiDir+'/xmldb-cleaned.xml').run()
    
    self.log.info("Running xml2sql against the XML database")
    Xml2Sql(src=self.mediawikiDir+'/xmldb-cleaned.xml', target=self.mediawikiDir+'/xmldb-processed').run()
    
    self.log.info("Importing SQL to database")
    SqlImporter(
      pageSql=self.mediawikiDir+'/xmldb-processed/page.sql', 
      textSql=self.mediawikiDir+'/xmldb-processed/text.sql',
      revisionSql=self.mediawikiDir+'/xmldb-processed/revision.sql',
      dbhost=self.args.get('--dbhost'),
      dbport=self.args.get('--dbport'),
      dbuser=self.args.get('--dbuser'),
      dbpass=self.args.get('--dbpass'),
      dbname=self.args.get('--dbname'),
      dbtype=self.args.get('--dbtype')      
    ).run()

#    XmlImporter(
#      xmlFile=mediawikiDir + '/xmldb',
#      dbhost=self.args.get('--dbhost') or self.installDir + "/mw.db",
#      dbport=self.args.get('--dbport'),
#      dbuser=self.args.get('--dbuser'),
#      dbpass=self.args.get('--dbpass'),
#      dbname=self.args.get('--dbname'),
#      dbtype=self.args.get('--dbtype') or 'sqlite'
#
#    ).run()

    self.endTime = datetime.now() - self.startTime

    self.log.info('Completed in: %s' % self.endTime)
"""
