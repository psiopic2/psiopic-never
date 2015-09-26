from datetime import datetime
from psiopic2.app.tasks import WikiExtractor
from psiopic2.app.tasks import GetDatabaseFromConfig
class CreateCorpus(object):
  def __init__(self, args, logger):
    self.log = logger
    self.args = args

  def run(self):
    self.startTime = datetime.now()
    
    self.log.info("Getting database info")
    dbparams = GetDatabaseFromConfig(mediawikiDir=self.args.get('--mw-dir')).run()
    
    self.log.info("Extracting text and meta data from wiki")
    WikiExtractor(dbhost=dbparams['host'],
      dbuser=dbparams['user'],
      dbpass=dbparams['pass'],
      dbname=dbparams['name'],
      dbtype='mysql',
      mediawikiDir=self.args.get('--mw-dir'),
      wikiextractor=self.args.get('--wikiextractor'),
      target=self.args.get('corpusDir'),
      host=self.args.get('host') or '127.0.0.1',
      port=self.args.get('port') or '30000'
    ).run()
    
    self.endTime = datetime.now() - self.startTime
    self.log.info('Completed in: %s' % self.endTime)    