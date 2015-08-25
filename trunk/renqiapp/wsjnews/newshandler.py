# -*- coding: utf-8 -*-
'''
Created on 2010-6-2

@author: 郑仁启
'''
from google.appengine.ext import webapp
from base import requires_admin, BaseRequestHandler
from google.appengine.ext.webapp.util import run_wsgi_app
import logging
from google.appengine.api import urlfetch
from HTMLParser import HTMLParser

class NewsAnalyzeHandler(BaseRequestHandler):
  @requires_admin
  def get(self):
    logging.debug('NewsHandler enter in')
    self.render("template/wsjnews/wsjNewsAnalyze.html")
    pass
  def post(self):
    news_urls_text = self.request.get('urls')
    news_urls = news_urls_text.split()
    for url in news_urls:
      handle_news(url)
    pass
def handle_news(url):
  news_html = urlfetch.fetch(url)
  
  pass

ESCAPE = {"lt":" < ", "#60":"<",
          "gt":">", "#62" : ">",
          "amp":"&", "#38":"&",
          "quot":"\"", "#34": "\"",
          "nbsp":" ", "#160":" ",
          "#39":"'"}

class NewsParser(HTMLParser):
  def __init__(self):
      HTMLParser.__init__(self)
      self.bookmarks = []
      self.tagStack = []
      self.count = 0
      self.skip = True
      self.tempList = []
      self.tagName = ''

  def handle_starttag(self, tag, attrs):

      #print "Encountered the beginning of a % s tag" % tag
      #if tag == "a":
          #if len(attrs) == 0: pass
          #else:
    self.tagName = tag
    #这里仅仅把tag放入栈
    if tag in ["div"]:
      for (variable, value) in attrs:
        pass
      pass
    if tag in ["a"]:
      href = ""
      addDate = None
      #for (variable, value) in attrs:
      folder = None
      if len(self.tagStack) > 0:
        folder = self.tagStack[-1]
#      bookmark = model.Bookmark(tag = tag, href = href, addDate = addDate,
#                          folder = folder, bookmarkList = self.bookmarkList)
#      self.bookmarks.append(bookmark)
      self.skip = False


  # Overridable -- handle end tag
  def handle_endtag(self, tag):

    self.skip = True
    
    if tag == "dl":
      self.tagStack.pop()
      if len(self.tagStack) == 0:
        nowCount = len(self.bookmarks)
        if self.count != nowCount:
          saveBookmarkList = self.bookmarks[self.count : nowCount]
          self.tempList.extend(saveBookmarkList)
        
        self.saveBookmark()

    if len(self.bookmarks) > 0 and tag in ["h3"]:
      bookmark = self.bookmarks[-1]
      #if not hasattr(bookmark, "title") or bookmark.title is None:
        #raise Exception("bookmark haven't a title")
      bookmark.put()
      nowCount = len(self.bookmarks)
      if nowCount - self.count > 1:
        saveBookmarkList = self.bookmarks[self.count : nowCount - 1]
        self.tempList.extend(saveBookmarkList)

      self.count = nowCount
    pass

  #handle &#39;
  def handle_charref(self, name):

    if self.skip :
      return

    key = "#" + name
    #if not ESCAPE.has_key(key):
      #raise Exception('ESCAPE not found')
    value = ESCAPE.get(key)
#    bookmark = self.bookmarks[-1]
#    bookmark.title = value if not hasattr(bookmark, "title") or bookmark.title is None else bookmark.title + value
    pass

  #replace(text, '&', '&amp;', '<', '&lt;', '>', '&gt;') "\"", "&quot;"
  # Overridable -- handle entity reference
  def handle_entityref(self, name):

    if self.skip :
      return

    key = name
    if not ESCAPE.has_key(key):
      raise Exception('ESCAPE not found')

    value = ESCAPE.get(key)

    bookmark = self.bookmarks[-1]

    bookmark.title = value if not hasattr(bookmark, "title") or bookmark.title is None else bookmark.title + value
    pass

  # Overridable -- handle data
  def handle_data(self, data):
    print data
    if self.skip :
      return

    #bookmark = self.bookmarks[-1]

    #bookmark.title = data if not hasattr(bookmark, "title") or bookmark.title is None else bookmark.title + data

    pass

  # Overridable -- handle comment
  def handle_comment(self, data):
    pass

  # Overridable -- handle declaration
  def handle_decl(self, decl):
    pass

  # Overridable -- handle processing instruction
  def handle_pi(self, data):
    pass


def main():
  application = webapp.WSGIApplication([('/wsjnews/analyze', NewsAnalyzeHandler)
                                        ], debug = True)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
