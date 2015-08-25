# -*- coding: utf-8 -*-
'''
Created on 2010-4-26

@author: zhengrenqi
'''

from HTMLParser import HTMLParser
from bookmark import model
from bookmark.model import Tag
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
import datetime
import string
import time
ESCAPE = {"lt":" < ", "#60":"<",
          "gt":">", "#62" : ">",
          "amp":"&", "#38":"&",
          "quot":"\"", "#34": "\"",
          "nbsp":" ", "#160":" ",
          "#39":"'"}

class BookmarkParser(HTMLParser):
  def __init__(self, bookmarkList):
      HTMLParser.__init__(self)
      self.bookmarks = []
      self.tagStack = []
      self.count = 0
      self.skip = True
      self.bookmarkList = bookmarkList
      self.tempList = []
      self.tagName = ''
      self.datetimeNow = datetime.datetime.now()

  def handle_starttag(self, tag, attrs):

      #print "Encountered the beginning of a % s tag" % tag
      #if tag == "a":
          #if len(attrs) == 0: pass
          #else:
    self.tagName = tag
    #这里仅仅把tag放入栈
    if tag in ["h3"]:
      add_date = self.datetimeNow
      for (variable, value) in attrs:
        if variable == "add_date":
          add_date = datetime.datetime.fromtimestamp(string.atoi(value))

      bookmark_tag = Tag(add_date = add_date, parent = self.tagStack[-1])
      self.tagStack.append(bookmark_tag)
      self.skip = False
    
    if tag in ["a"]:
      href = ""
      addDate = None
      for (variable, value) in attrs:
        if variable == "href":
          href = value
        elif variable == "add_date":
          addDate = datetime.datetime.fromtimestamp(string.atoi(value))
      folder = None
      if len(self.tagStack) > 0:
        folder = self.tagStack[-1]
      bookmark = model.Bookmark(tag = tag, href = href, addDate = addDate,
                          folder = folder, bookmarkList = self.bookmarkList)
      self.bookmarks.append(bookmark)
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

      if len(self.tempList) > 300 :
        self.saveBookmark()
      self.count = nowCount
    pass

  def saveBookmark(self):
    bm = ''.join(["saveBookmarks_" , str(time.time())])
    memcache.add(bm, self.tempList, 120)
    self.tempList = []
    queue = taskqueue.Queue("bookmark")
    queue.add(taskqueue.Task(url = "/bookmark/q/put", params = {'key': bm}))
    pass
  #handle &#39;
  def handle_charref(self, name):

    if self.skip :
      return

    key = "#" + name
    if not ESCAPE.has_key(key):
      raise Exception('ESCAPE not found')
    value = ESCAPE.get(key)
    bookmark = self.bookmarks[-1]
    bookmark.title = value if not hasattr(bookmark, "title") or bookmark.title is None else bookmark.title + value
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

    if self.skip :
      return

    bookmark = self.bookmarks[-1]

    bookmark.title = data if not hasattr(bookmark, "title") or bookmark.title is None else bookmark.title + data

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

class Bookmark(object):
  def __init__(self, *args, **kwds):
    for key in kwds.keys():
      setattr(self, key, kwds.get(key))
    pass
