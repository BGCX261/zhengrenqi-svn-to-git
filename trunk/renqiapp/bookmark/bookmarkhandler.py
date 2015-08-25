# -*- coding: utf-8 -*-
'''
Created on 2010-4-21

@author: zhengrenqi
'''
from base import requires_admin, BaseRequestHandler
from bookmark import bookmarkparser
from google.appengine.api import memcache, apiproxy_stub_map
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import DeadlineExceededError
import logging
import model
import time

DB_TIME = 0

class BookmarkHandler(BaseRequestHandler):

  @requires_admin
  def get(self):
    logging.debug('BookmarkHandler')
    owner = self.login_user
    bookmarks = getBookmarksByOwner(owner)
    self.render("template/bookmark/bookmarkList.html", {'bookmarks':bookmarks})
    pass

  def post(self): # delete files

    self.redirect('/bookmark')

class UploadHandler(BaseRequestHandler):
  def get(self):
    self.render("template/bookmark/bookmarkUpload.html")
    pass

  def post(self):
    name = self.request.get('filename')
    mtype = self.request.get('fileext')
    bookmark = self.request.get('upfile').decode('utf-8')
    logging.debug('name %s mtype %s ', name, mtype)
    #bm = ''.join(["bookmark_" , str(time.time())])

    #memcache.add(bm, bookmark, 60)

    #queue = taskqueue.Queue("bookmark")
    #queue.add(taskqueue.Task(url="/bookmark/q/import", params={'key': bm, 'name':name}))

    try:
      logging.debug('clock %f %f', time.clock(), time.time())
      p = bookmarkparser.BookmarkParser()
      p.feed(bookmark)
      self.count(p.bookmarks)
    except DeadlineExceededError:
      pass
    finally:
      logging.debug('clock %f %f', time.clock(), time.time())
    self.redirect('/bookmark')

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write("finish!")


class ClearAll(BaseRequestHandler):

  def get(self):
    logging.debug('ClearAll')
    #list = model.BookmarkList.all()
    for l in list:
      query = model.Bookmark.gql("WHERE bookmarkList = :1", l.key())
      isLoop = True
      while isLoop:
        bookmarks = query.fetch(200)
        if len(bookmarks) < 200:
          isLoop = False
        db.delete(bookmarks)
      l.delete()
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write("clear finish!")
    pass

class ListBookmark(BaseRequestHandler):

  def get(self):
    logging.debug('ListBookmark')
    #self.response.out.write(common.render("bookmarkList", {"bookmarkLists":getAllBookmarkList()}))
    pass

class DeleteBookmark(BaseRequestHandler):

  def post(self):
    delids = self.request.POST.getall('del')
    logging.debug('start delete delids')
    if delids:
      for id in delids:
        #list = model.BookmarkList.get_by_id(int(id))
        query = model.Bookmark.gql("WHERE bookmarkList = :1", list.key())
        isLoop = True
        while isLoop:
          bookmarks = query.fetch(200)
          if len(bookmarks) < 200:
            isLoop = False
          db.delete(bookmarks)
        list.delete()
    self.redirect('/bookmark/ls')
    pass

class ImportBookmark(BaseRequestHandler):
  def post(self):
    try:
      name = self.request.get('name')
      bm = self.request.get('key')
      bookmark = memcache.get(bm)
      if bookmark is None:
        logging.debug('bookmark is None')
        return
      memcache.delete(bm)
      #bookmarkList = model.BookmarkList(uploadFile=name)
      #bookmarkList.put()

      logging.debug('clock %f %f', time.clock(), time.time())
      #p = bookmarkparser.BookmarkParser(bookmarkList)
      #p.feed(bookmark)
      #self.count(p.bookmarks)
    except DeadlineExceededError:
      pass
    finally:
      logging.debug('clock %f %f', time.clock(), time.time())
    self.redirect('/bookmark')

  def count(self, bookmarks):
    logging.debug('start count')
    acount = 0
    h3count = 0
    for b in bookmarks:
      if b.tag == "h3":
        h3count = h3count + 1
      elif b.tag == "a":
        acount = acount + 1
    logging.debug('h3 is %d , a is %d len is %d' , h3count , acount, len(bookmarks))
    pass
class addBookmark(BaseRequestHandler):
  def post(self):
    pass

class PutHandler(BaseRequestHandler):
  def post(self):
    bm = self.request.get('key')
    bookmarks = memcache.get(bm)
    if bookmarks is None or len(bookmarks) == 0:
      logging.debug('bookmarks is None')
      return
    memcache.delete(bm)
    for bookmark in bookmarks:
      bookmark.put()
    logging.debug('%d bookmarks put', len(bookmarks))

class ExportBookmark(BaseRequestHandler):
  DECL = \
"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>\n"""

  def post(self, slug):
    key = slug
    logging.info('the listId is %s and type is %s' , key, type(key))
    if key and len(key) > 0:
      #list = model.BookmarkList.get(key)
      logging.info(list)
      bookmarkstr = self.fetchBookmarks(list)
    self.response.headers['Content-Type'] = 'application/octet-stream'
    self.response.headers['Content-Disposition'] = 'filename="%s"' % list.uploadFile
    self.response.out.write(bookmarkstr)

  get = post

  def fetchBookmarks(self, list):
    global DB_TIME
    DB_TIME = 0
    #debug code
    def hook(service, call, request, response):
      global DB_TIME
      DB_TIME += 1
    apiproxy_stub_map.apiproxy.GetPreCallHooks().Append('db_hook', hook, 'datastore_v3')
    #debug code

    #debug code
    start_time = time.time()
    logging.info('start time is %f', start_time)
    bookmark_count = 0
    fetch_time = 0.0
    fetch_times = 0
    #debug code

    #gql = "WHERE bookmarkList = :1 and folder = :2"
    #query = model.Bookmark.gql(gql)
    #bookmarks = self.fetchChildBookmark(query, list, None)

    #query.bind(list, None)
    #bookmarks = query.fetch(1000)

    allBookmarks = self.getAllBookmarks(list)
    bookmarks = self.getChildBookmark(allBookmarks, None)

    folderStack = []
    folderName = ['h1', 'h3']
    bls = [self.DECL]

    while len(bookmarks) > 0:
      bookmark = bookmarks.pop(0)

      while bookmark._folder is not None and len(folderStack) > 0 and bookmark._folder != folderStack[-1].key():
        #logging.info('title: bookmark._folder is %s, folderStack[-1] is %s, bookmark is %s'
        #             , repr(bookmark._folder.title) , repr(folderStack[-1].title), repr(bookmark.title))
        #logging.info('folderStack[-1] %s ,repr %s', folderStack[-1].title,repr(folderStack[-1].title))

        folderStack.pop()
        for _ in range(len(folderStack)):
          bls.append('    ')
        bls.append('</DL><p>\n')

      #if bookmark._folder is not None and bookmark._folder == folderStack[-1].key():
        #logging.info('bookmark end %s %s %s %s %s %s', bookmark._folder, folderStack[-1], bookmark._folder, folderStack[-1].key(),repr(folderStack[-1].title),repr(bookmark._folder.title))

      #debug code
      bookmark_count += 1
      if bookmark_count > 2500:
        logging.info('already join %d bookmark , folderStack  %s', bookmark_count, folderStack)
        logging.info('fetch_time is %f, fetch_times is %d, DB_TIME %d', fetch_time, fetch_times, DB_TIME)
        return ''.join(bls)
      #debug code

      #拼接当前标签
      curbookmarkls = self.getBookmarkStr(bookmark)
      for _ in range(len(folderStack)):
        bls.append('    ')
      bls.extend(curbookmarkls)
      #如果当前标签是文件夹，那么级数加1
      if bookmark.tag in folderName:
        for _ in range(len(folderStack)):
          bls.append('    ')
        bls.append('<DL><p>\n')
        folderStack.append(bookmark)

        #查询文件夹下内容
        t0 = time.time()
        #query.bind(list, folderStack[-1])
        #query_bookmarks = query.fetch(1000)

        #query_bookmarks = self.fetchChildBookmark(query, list, folderStack[-1])
        query_bookmarks = self.getChildBookmark(allBookmarks, folderStack[-1])

        fetch_time = fetch_time + time.time() - t0
        fetch_times += 1
        #logging.info('fetch %d bookmarks',len(query_bookmarks))
        #bookmarks.extend(query_bookmarks)
        query_bookmarks.extend(bookmarks)
        bookmarks = query_bookmarks

    for _ in range(len(folderStack)):
      folderStack.pop()
      for _ in range(len(folderStack)):
        bls.append('    ')
      bls.append('</DL><p>\n')
    logging.info('fetch end , len(allBookmarks) is %s', len(allBookmarks))
    end_time = time.time()
    logging.info('end time is %f exe time is %f', end_time, end_time - start_time)
    logging.info('fetch_time is %f, fetch_times is %d, DB_TIME %d', fetch_time, fetch_times, DB_TIME)
    return ''.join(bls)
    pass

  def fetchChildBookmark(self, bookmark_query, list, folder):
    bookmark_query.bind(list, folder)
    return bookmark_query.fetch(1000)

  def getAllBookmarks(self, list):
    begin_time = time.time()
    fetch_limit = 1000
    gql = "WHERE bookmarkList = :1 order by title"
    query = model.Bookmark.gql(gql)
    query.bind(list)
    bookmarks = query.fetch(fetch_limit)

    logging.info('bookmarks len is %d time is %f', len(bookmarks), time.time() - begin_time)

    if len(bookmarks) < fetch_limit:
      return bookmarks

    gql = "WHERE bookmarkList = :1 and title > :2 order by title"
    query = model.Bookmark.gql(gql)
    count = 0
    while True:
      query.bind(list, bookmarks[-1].title)
      results = query.fetch(fetch_limit)
      bookmarks.extend(results)
      count += 1
      if len(results) < fetch_limit or count > 5:
        break
    logging.info('AllBookmarks len is %d time is %f', len(bookmarks), time.time() - begin_time)
    return bookmarks

  def getChildBookmark(self, allBookmarks, folder):
    bookmarks = []
    for b in allBookmarks:
      if (folder is None and b._folder is None) or (folder is not None and b._folder == folder.key()):
        bookmarks.append(b)
    for b in bookmarks:
      allBookmarks.remove(b)
    return bookmarks

  def getBookmarkStr(self, bookmark):
    tag = bookmark.tag.upper()
    bls = []
    if tag in ['H3', 'A']:
      bls.append('<DT>')

    bls.append('<')
    bls.append(tag)
    if bookmark.href and len(bookmark.href.strip()) > 0:
      bls.append(' HREF="')
      bls.append(bookmark.href)
      bls.append('"')

    if bookmark.addDate :
      bls.append(' ADD_DATE="')
      bls.append(str(int(time.mktime(bookmark.addDate.timetuple()))))
      bls.append('"')

    bls.append('>')
    bls.append(bookmark.title if bookmark.title else '')
    bls.append('</')
    bls.append(tag)
    bls.append('>')
    bls.append('\n')
    return bls

def getBookmarksByOwner(owner, page = 1):
  mem_path = owner.email + str(page)
  bookmarks = memcache.get(mem_path)
  if bookmarks is None:
    bookmarks = model.Bookmark.gql("where owner = :1 order by title desc", owner).fetch(50 * page, 50 * (page - 1))
    memcache.add(mem_path, bookmarks, 600)

  return bookmarks

def main():
  application = webapp.WSGIApplication([('/bookmark/{0,1}', BookmarkHandler),
                                        ('/bookmark/up', UploadHandler),
                                        ('/bookmark/clearall', ClearAll),
                                        ('/bookmark/ls', ListBookmark),
                                        ('/bookmark/del', DeleteBookmark),
                                        ('/bookmark/export/([^/]*)/{0,1}.*', ExportBookmark),
                                        ('/bookmark/q/put', PutHandler),
                                        ('/bookmark/q/import', ImportBookmark),
                                        ('/bookmark/q/add', addBookmark)

                                        ], debug = True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
