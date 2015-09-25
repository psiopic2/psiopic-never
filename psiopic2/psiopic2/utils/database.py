import sqlite3
import pymysql as MySQLdb
import logging
import sys

class Database(object):
  
  def __init__(self, dbtype, dbhost, dbport, dbname, dbuser, dbpass):
    self.dbtype = dbtype
    self.dbhost = dbhost
    self.dbname = dbname
    self.dbport = dbport
    self.dbuser = dbuser
    self.dbpass = dbpass

    if dbtype == 'mysql':
      self._db = MysqlAdapter(
        dbhost=self.dbhost,
        dbname=self.dbname,
        dbport=self.dbport,
        dbuser=self.dbuser,
        dbpass=self.dbpass
      )
    else:
      raise NotImplementedError(dbtype)

  def execFile(self, sqlFile):
    self._db.execFile(sqlFile)

  def execSql(self, sql):
    self._db.execSql(sql)

  def executeMany(self, sql, args):
    self._db.executeMany(sql, args)
    
  def execute(self, sql):
    return self._db.execute(sql)


class BaseAdapter(object):
  def __init__(self, *args, **kwargs):
    self.dbhost = kwargs.get('dbhost')
    self.dbport = kwargs.get('dbport')
    self.dbname = kwargs.get('dbname')
    self.dbuser = kwargs.get('dbuser')
    self.dbpass = kwargs.get('dbpass')
    
    self.log = logging.getLogger('psiopic')

  def execFile(self, sqlFile):
    raise NotImplementedError

  def execSql(self, sql):
    raise NotImplementedError

  def executeMany(self, sql, args):
    raise NotImplementedError
  
  def execute(self, sql):
    raise NotImplementedError

class MysqlAdapter(BaseAdapter):
  def __init__(self, *args, **kwargs):
    super(self.__class__, self).__init__(*args, **kwargs)
    self.conn = MySQLdb.connect(self.dbhost, self.dbuser, self.dbpass, self.dbname, charset='utf8')

  def execFile(self, sqlFile):

    from subprocess import Popen, PIPE
    f = open(sqlFile)

    cmds = ['mysql','-u',self.dbuser,'--password=' + self.dbpass,'-h',self.dbhost,'-D',self.dbname,'-v']

    proc = Popen(cmds,
                stdout=PIPE, stdin=f)

    while proc.poll() is None:
      output = proc.stdout.readline()
      if output.strip() != "":
        self.log.debug(output.strip())
        sys.stdout.flush()

#    self.log.debug(proc.communicate()[0])

  def execSql(self, sql):
    cur = self.conn.cursor()
    cur.execute(sql)
    cur.close()

  def executeMany(self, sql, args):
    cur = self.conn.cursor()
    cur.executemany(sql, args)
    self.conn.commit()
    cur.close()
    
  def execute(self, sql):
    cur = self.conn.cursor()
    cur.execute(sql)
    return cur
    