# -*- coding: utf-8 -*-
'''
Created on 2010-7-7

@author: 郑仁启
'''
from base import BaseRequestHandler
from google.appengine import runtime
from google.appengine.api import urlfetch, memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from model import FeedEntry
import datetime
import feedparser
import hashlib
import logging
import model
import random
import time
import urllib
import zzzutil

feed_queue = taskqueue.Queue("feed")
class PublishHandler(BaseRequestHandler):
  def get(self, slug):
    if slug and slug[0] == '/':
      slug = slug[1:]
    if slug:
      publish_url = self.request.host_url + "/pipes/" + slug
      post_params = {
        'hub.mode': 'publish',
        'hub.url': publish_url,
      }
      payload = urllib.urlencode(post_params)
      hub_url = 'http://pubsubhubbub.appspot.com/'
      try:
        logging.debug('the publish_url is %s', publish_url)
        response = urlfetch.fetch(hub_url, method='POST', payload=payload)
      except urlfetch.Error:
        logging.exception('Failed to deliver publishing message to %s', hub_url)
      else:
        logging.info('URL fetch status_code=%d, content="%s"',
                     response.status_code, response.content)
    self.response.out.write('publish finish')
  post = get
class PipesHandler(BaseRequestHandler):
  def get(self, slug):
    logging.debug('PipesHandler.get')
    self.response.headers["Content-Type"] = "text/xml"
    if slug[0] == '/':
      slug = slug[1:]
    if slug:
      logging.debug('slug is ' + slug)
      feed_xml_memcache_key = 'feed_xml_' + slug
      feed_xml = memcache.get(feed_xml_memcache_key)
      if not feed_xml:
        logging.debug('feed_xml not found in memcache, query enties')
        pipe = model.Pipe.gql("WHERE pipe_web_address = :1", slug).get()
        if pipe:
          try:
            feed_xml = self.get_feed_xml(pipe)
            
            memcache.add(feed_xml_memcache_key, feed_xml, 300)#five minutes
          except Exception , e:
            logging.exception(e)
            return self.response.set_status(500)
            
        else:
          return self.response.set_status(404)
      if feed_xml:
        logging.debug('the len(feed_xml) is %d', len(feed_xml))
        self.response.out.write(feed_xml)
    else:
      return self.response.set_status(404)

    pass
  post = get
  
  def get_feed_xml(self, pipe):
    title = pipe.title
    subtitle = pipe.subtitle
    entries = model.FeedEntry.gql("WHERE pipe = :1 ORDER BY updated_time desc", pipe.key()).fetch(50)
    logging.debug('query finish. get %d entries', len(entries))
    for entry in entries:
      entry.updated = entry.get_updated_time()
    context = {
      'entries': entries,
      'title':title,
      'subtitle':subtitle,
      'source': self.request.url,
    }
    if entries:
      context['first_entry'] = entries[0]
    feed_xml = template.render('atom.xml', context)
    return feed_xml
    pass
class AddPipeHandler(BaseRequestHandler):
  def get(self):
    pipe_web_address = self.request.get('pipeWebAddress')
    feed_url = self.request.get('feedUrl')
    pipe = model.Pipe(pipe_web_address=pipe_web_address, feed_url=feed_url)
    pipe.put()
    msg = 'add success, pipe_web_address is ' + pipe_web_address + 'feed_url is ' + feed_url
    logging.debug(msg)
    self.response.out.write(msg)
    pass
class addFeedEntryHandler(BaseRequestHandler):
  def post(self, slug):
    random_key = self.request.get('key')
    pipe_web_address = self.request.get('pipe_web_address')
    entries_map = memcache.get(random_key)
    if not entries_map:
      return
    entries = entries_map['entries']
    fetch_index = entries_map['fetch_index']
    put_index = entries_map['put_index']
    while fetch_index < len(entries):
      try:
          entries[fetch_index].content = zzzutil.fetch_page(entries[fetch_index].link, '<!content_tag txt>', '<!/content_tag txt>')
          fetch_index += 1
      except runtime.DeadlineExceededError, e:
        logging.exception(e)
        logging.debug('we have fetched %d contents', fetch_index)
        entries_map['fetch_index'] = fetch_index
        entries_map['entries'] = entries
        memcache.set(random_key, entries_map, 120)
        feed_queue.add(taskqueue.Task(url="/dealFeedEntry/set/", params={'key': random_key}))
        return
      except:
        pass
    try:
      while put_index < len(entries):
        db.put(entries[put_index:put_index + 20])
        logging.debug('we put %d entries into database', len(entries[put_index:put_index + 20]))
        put_index = put_index + 20
    except runtime.DeadlineExceededError, e:
      logging.exception(e)
      entries_map['put_index'] = put_index
      entries_map['entries'] = entries
      memcache.set(random_key, entries_map, 120)
      feed_queue.add(taskqueue.Task(url="/dealFeedEntry/set/", params={'key': random_key}))
      return
    memcache.delete(random_key)
    feed_xml_memcache_key = 'feed_xml_' + pipe_web_address
    memcache.delete(feed_xml_memcache_key)
    
    pass

class RefreshFeedHandler(BaseRequestHandler):
  def get(self, slug):
    if slug and slug[0] == '/':
      slug = slug[1:]
    logging.debug('the slug is %s', slug)
    if slug == 'allpipes':
      pipes = model.Pipe.gql("WHERE auto_refresh = :1", True).fetch(200)
      logging.debug('fetch %d pipes' , len(pipes))
      for pipe in pipes:
        feed_queue.add(taskqueue.Task(url="/refreshfeed/" + pipe.pipe_web_address))

      return ['ok']
      pass
    if slug:
      pipe = model.Pipe.gql("WHERE pipe_web_address = :1", slug).get()
      if pipe and pipe.auto_refresh:
        feedUrl = pipe.feed_url
        logging.debug('start refresh feed, the feedUrl is ' + feedUrl)
        fetch_count = 0
        while True:
          fetch_count += 1
          if fetch_count > 10:
            break
          try:
            resp = urlfetch.fetch(feedUrl)
            break
          except Exception , e:
            logging.exception(e)

        feed_xml = resp.content
        logging.debug('we fetch %d times and the size of feed is %s' , fetch_count, str(len(feed_xml)))
        entries = self.get_entries(feed_xml, pipe)
        logging.debug('we fetch %d entries' , len(entries))
        if len(entries) > 0:
          entries_map = {'entries':entries, 'fetch_index':0, 'put_index':0}
          random_str = ''.join([chr(random.randint(97, 122))for i in range(0, 16)])
          random_key = slug + '_' + random_str
          memcache.set(random_key, entries_map, 120)

          feed_queue.add(taskqueue.Task(url='/dealFeedEntry/set', params={'key': random_key, 'pipe_web_address': pipe.pipe_web_address}))

        #db.put(entries)
        pass
      pass
      return ['ok']
    pass
  post = get

  def get_entries(self, feed_xml, pipe):
    try:
      
      data = feedparser.parse(feed_xml)
      if data.bozo:
        logging.error('Bozo feed data. %s: %r',
                       data.bozo_exception.__class__.__name__,
                       data.bozo_exception)
        if (hasattr(data.bozo_exception, 'getLineNumber') and
            hasattr(data.bozo_exception, 'getMessage')):
          line = data.bozo_exception.getLineNumber()
          logging.error('Line %d: %s', line, data.bozo_exception.getMessage())
          segment = self.request.body.split('\n')[line - 1]
          logging.info('Body segment with error: %r', segment.decode('utf-8'))
        return self.response.set_status(500)
      #getfeed
      #feed = data.feed
      #subtitle, title = feed.subtitle, feed.title

      entries = []
      for entry in data.entries:
        link = entry.get('link', '')
        title = entry.get('title', '')
        updated = entry.get('updated_parsed', '')
        updated_time = datetime.datetime.fromtimestamp(time.mktime(updated)) 
        content = ''

        if hasattr(entry, 'content'):
          # This is Atom.
          content = entry.content[0].value
        else:
          content = entry.get('description', '')

        id = entry.get('id', '') or hashlib.sha1(link or title).hexdigest()
        pipe_key = str(pipe.key().id_or_name())
        key_name = 'key_' + hashlib.sha1(pipe_key + "_" + id).hexdigest()
        new_entry = FeedEntry.get_by_key_name(key_name)
        isUpdated = False
        if new_entry:
          if new_entry.updated_time != updated_time :
            isUpdated = True
            new_entry.updated_time = updated_time
            new_entry.link = link
            new_entry.title = title
            new_entry.content = content
        else:
          isUpdated = True
          new_entry = FeedEntry(key_name=key_name,
                                pipe=pipe,
                                entry_id=id,
                                title=title,
                                link=link,
                                updated_time=updated_time,
                                content=content)
        if isUpdated:
          entries.append(new_entry)
      """
      context = {
        'entries': entries,
        'title':title,
        'subtitle':subtitle,
        'source': self.request.url,
      }
      if entries:
        context['first_entry'] = entries[0]
      feed_xml = template.render('atom.xml', context)
      """
    except Exception , e:
      logging.exception(e)
    return entries
    pass

class pipesEntryUpdateHandler(BaseRequestHandler):
  def get(self, slug):
    if slug and slug[0] == '/':
      slug = slug[1:]
    pipe = model.Pipe.gql("WHERE pipe_web_address = :1", slug).get()
    if pipe:
      
      logging.debug('type of pipe.key().id_or_name() is %s and str(pipe.key().id_or_name()) is %s' , type(pipe.key().id_or_name()), str(pipe.key().id_or_name()))
      entries = model.FeedEntry.gql("WHERE pipe = :1", pipe.key()).fetch(200)
      new_entries = []
      old_entries = []
      logging.debug('fetch %d entries', len(entries))
      for entry in entries:
        pipe_key = str(pipe.key().id_or_name())
        key_name = 'key_' + hashlib.sha1(pipe_key + "_" + entry.entry_id).hexdigest()
        if entry.key().id_or_name() != key_name:
          new_entry = FeedEntry(key_name=key_name,
                                pipe=pipe,
                                entry_id=entry.entry_id,
                                title=entry.title,
                                link=entry.link,
                                updated_time=entry.updated_time,
                                content=entry.content)
          new_entries.append(new_entry)
          old_entries.append(entry)
      
      logging.debug('new_entries %d,old_entries %d', len(new_entries), len(old_entries))
      if len(new_entries) > 0:
        random_str = ''.join([chr(random.randint(97, 122))for i in range(0, 16)])
        random_key = slug + '_' + random_str
        entries_map = {'entries':new_entries, 'fetch_index':len(new_entries), 'put_index':0}
        memcache.set(random_key, entries_map, 120)
        feed_queue.add(taskqueue.Task(url='/dealFeedEntry/set', params={'key': random_key, 'pipe_web_address': pipe.pipe_web_address}))
      if len(old_entries) > 0:
        random_str = ''.join([chr(random.randint(97, 122))for i in range(0, 16)])
        random_key = slug + '_' + random_str
        entries_map = {'entries':old_entries, 'del_index':0}
        memcache.set(random_key, entries_map, 120)
        feed_queue.add(taskqueue.Task(url='/dealFeedEntry/del', params={'key': random_key, 'pipe_web_address': pipe.pipe_web_address}))
    pass
class delFeedEntryHandler(BaseRequestHandler):
  def post(self, slug):
    random_key = self.request.get('key')
    pipe_web_address = self.request.get('pipe_web_address')
    entries_map = memcache.get(random_key)
    if not entries_map:
      return
    entries = entries_map['entries']
    del_index = entries_map['del_index']
    db.delete(entries)
    logging.debug('delete %d entries', len(entries))
    pass
def main():
  application = webapp.WSGIApplication([('/pipes(/.*)?', PipesHandler),
                                        ('/addPipe/{0,1}', AddPipeHandler),
                                        ('/publish(/.*)?', PublishHandler),
                                        ('/refreshfeed(/.*)?', RefreshFeedHandler),
                                        ('/dealFeedEntry/set(/.*)?', addFeedEntryHandler),
                                        ('/dealFeedEntry/del(/.*)?', delFeedEntryHandler),
                                        ('/pipesEntryUpdate(/.*)?', pipesEntryUpdateHandler),
                                        
                                        ], debug=True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
