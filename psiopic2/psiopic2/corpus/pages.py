import threading
import xml.sax
import re
import os
import random
import time
from subprocess import Popen, PIPE

class Page(object):
  def __init__(self):
    self.title = None
    self.ns = None
    self.id = None
    self.revision_id = None
    self.revision_parentid = None
    self.timestamp = None
    self.model = None
    self.format = None
    self.text = None
    self.revision_sha1 = None
    self.revision_format = None

    self._currentContent = None

    self._len = None

    self.insertPageQuery = 'insert into page '
    self.insertPageQuery += '  (page_id, page_namespace, page_title, page_is_redirect, page_is_new, page_random, '
    self.insertPageQuery += '   page_latest, page_len, page_content_model) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'

    self.insertTextQuery = 'insert into text (old_id, old_text) values (%s, %s)'

    self.insertRecentChangesQuery = 'insert into recentchanges (rc_id, rc_timestamp, rc_user, rc_user_text, '
    self.insertRecentChangesQuery += 'rc_title, rc_minor, rc_bot, rc_cur_id, rc_this_oldid, rc_last_oldid, '
    self.insertRecentChangesQuery += 'rc_type, rc_source, rc_patrolled, rc_ip, rc_old_len, rc_new_len, rc_deleted, '
    self.insertRecentChangesQuery += 'rc_logid) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    self.insertRevisionQuery = 'insert into revision '
    self.insertRevisionQuery += '(rev_id, rev_page, rev_text_id, rev_user, rev_user_text, rev_timestamp, '
    self.insertRevisionQuery += 'rev_minor_edit, rev_deleted, rev_len, rev_parent_id, rev_sha1) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

  def getTextValueArray(self):
    return [self.id, self.text]

  def getRevisionValueArray(self):
    return [
      self.revision_id, #rev_id
      self.id, #rev_page
      self.id, #rev_text_id
      0, #rev_user
      'Psiopic2', #rev_user_text
      self.timestamp, #rev_timestamp
      0, #rev_minor_edit
      0, #rev_deleted
      self.getLength(), #rev_length
      0, #rev_parent_id
      self.revision_sha1, #rev_sha1
    ]


  def getRecentChangesValueArray(self):
    return [
      self.id, #rc_id
      self.timestamp, #rc_timestamp 
      0, #rc_user
      'Psiopic2', #rc_user_text
      self.title, #rc_title
      0, #rc_minor
      0, #rc_bot,
      self.id, #rc_cur_id,
      self.id, #rc_this_oldid,
      0, #rc_last_oldid,
      0, #rc_type,
      "mw.new", #rc_source,
      0, #rc_patrolled,
      "127.0.0.1", #rc_ip,
      0, #rc_old_len,
      self.getLength(), #rc_new_len,
      0, #rc_deleted,
      0, #rc_logid
    ]

  def getPageValueArray(self):
    return [
      self.id, #page_id
      self.ns, #page_namespace,
      self.title, #page_title
      0, #page_isredirect,
      1, #page_is_new
      random.random(), #page_random
      self.revision_id, #page_latest
      self.getLength(), #page_len
      'wikitext', #page_model
    ]

  def getTextId(self):
    return self.id

  def getLength(self):
    if self._len == None:
      self._len = len(self.text)
    return self._len

  def getCategories(self):
    return re.findall("\[\[Category\:([a-zA-Z0-9\_\s\-]+)\]\]", self.text)


class XmlParser(xml.sax.ContentHandler):

    processing_ns = False
    processing_text = False
    
    def __init__(self, callback):
        xml.sax.ContentHandler.__init__(self)
        self.current_page = 0
        self.pages = [""]
        self.collectContent = False
        self.callback = callback
        self.inRedirectPage = False

        self._currentContent = ""

        self.inRevision = False
        self.inContributor = False

        self._inserts = {
          'pages': [],
          'revisions': [],
          'text': []
        }
        
    def startElement(self, name, attrs):
        methodName = "start_" + name
        self._callback(methodName)

    def endElement(self, name):
      methodName = "end_" + name
      self._callback(methodName)

    def characters(self, content):
      if self.collectContent != True:
        return

      self._currentContent += content
 
    def _callback(self, methodName):
      try:
        func = getattr(self, methodName)
      except AttributeError:
        pass
      else:
        return func()
 
    def start_redirect(self):
      self.inRedirectPage = True
   
    def start_title(self):
      if self.inRevision == False:
        self.startCollectingContent()

    def end_title(self):
      if self.inRevision == False:
        self._newPage.title = self.stopCollectingContent()
 
    def start_format(self):
      if self.inRevision == True:
        self.startCollectingContent()

    def end_format(self):
      if self.inRevision == True:
        self._newPage.revision_format = self.stopCollectingContent()

    def start_parentid(self):
      if self.inRevision == True:
        self.startCollectingContent()

    def end_parentid(self):
      if self.inRevision == True:
        self._newPage.revision_parentid = self.stopCollectingContent()

    def start_sha1(self):
      if self.inRevision == True:
        self.startCollectingContent()

    def end_sha1(self):
      if self.inRevision == True:
        self._newPage.revision_sha1 = self.stopCollectingContent()
          
    def start_model(self):
      if self.inRevision == True:
        self.startCollectingContent()

    def end_model(self):
      if self.inRevision == True:
        self._newPage.model = self.stopCollectingContent()

    def start_page(self):
      self._newPage = Page()

    def end_page(self):
      if self.inRedirectPage == False:
        self.callback.page(self._newPage)
      else:
        self.inRedirectPage = False
       
        
    def start_ns(self):
      self.startCollectingContent()
 
    def end_ns(self):
      self._newPage.ns = self.stopCollectingContent()

    def start_id(self):
      if self.inContributor == True:
        return
      
      self.startCollectingContent()

    def end_id(self):
      if self.inContributor == True:
        return

      id = self.stopCollectingContent()
      
      if self.inRevision == False:
        self._newPage.revision_id = id
      else:
        self._newPage.id = id


    def start_contributor(self):
      self.inContributor = True

    def end_contributor(self):
      self.inContributor = False
  
    def start_revision(self):
      self.inRevision = True

    def end_revision(self):
      self.inRevision = False

    def start_text(self):
      self.startCollectingContent()

    def end_text(self):
      self._newPage.text = self.stopCollectingContent()

    def startCollectingContent(self):
      self.collectContent = True
      self._currentContent = ""
      
    def stopCollectingContent(self):
      self.collectContent = False
      content = self._currentContent
      del self._currentContent

      return content
    

class ProcessingThread(threading.Thread):
  def __init__(self, pages, corpus_dir):
    threading.Thread.__init__(self)
    self.pages = pages
    self.category_count = {}
    self.total_processed = 0
    self.last_msg = ""
    self.corpus_dir = corpus_dir

  def start(self):
    self.running = True
    threading.Thread.start(self)

  def run(self):
    try:
      for page in self.pages:
        categories = page.get_categories()
        if len(categories) > 0:
          for category in categories:
            targetdir = self.corpus_dir + "/" + category
            if os.path.isdir(targetdir) == False:
              os.makedirs(targetdir)
            targetfile = targetdir + "/%s" % self.total_processed
            with open(targetfile, 'wb') as f:
              f.write(page.get_article())
        self.total_processed += 1
    finally:
      self.running = False

class SplittingThread(threading.Thread):
  def __init__(self, parser, xmlfile):
    threading.Thread.__init__(self)
    self.parser = parser
    self.xmlfile = xmlfile
    self.running = False

  def start(self):
    self.running = True
    threading.Thread.start(self)

  def run(self):
    try:
      with open(self.xmlfile) as f:
        xml.sax.parse(f, self.parser)
    finally: 
      self.running = False

  def getPageCount(self):
    return self.parser.current_page

 
