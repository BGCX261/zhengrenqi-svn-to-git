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
import datetime
import feedparser
import fetchpage
import hashlib
import logging
import model
import random
import sys
import time
import urllib
import urlparse
import zrqutil

default_feed_queue = taskqueue.Queue("feed")
add_feed_queue = taskqueue.Queue("add-feed")
HUB_URL = 'http://pubsubhubbub.appspot.com/'
PIPE_OUTPUT_FEED_XML_MEMCACHE_KEY = 'PIPE_OUTPUT_FEED_XML'
INPUT_FEED_XML_MEMCACHE_KEY = 'INPUT_FEED_XML'
PIPE_MEMCACHE_KEY = 'PIPE'
class PublishHandler(BaseRequestHandler):
  def get(self, slug):
    if slug and slug[0] == '/':
      slug = slug[1:]
    is_remove = self.request.get('is_remove')
    if slug:
      if is_remove == 1 :
        feed_xml_memcache_key = PIPE_OUTPUT_FEED_XML_MEMCACHE_KEY + '_' + slug
        #remove the xml catch
        memcache.delete(feed_xml_memcache_key)

      publish_url = self.request.host_url + "/pipes/" + slug
      post_params = {
        'hub.mode': 'publish',
        'hub.url': publish_url,
      }
      payload = urllib.urlencode(post_params)
      try:
        logging.debug('the publish_url is %s', publish_url)
        response = urlfetch.fetch(HUB_URL, method='POST', payload=payload)
      except urlfetch.Error:
        logging.exception('Failed to deliver publishing message to %s', HUB_URL)
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
      #req_path = self.request.path
      feed_xml_memcache_key = PIPE_OUTPUT_FEED_XML_MEMCACHE_KEY + '_' + slug
      feed_xml = memcache.get(feed_xml_memcache_key)
      updated_time_str = self.request.get('updated_time')
      updated_time = None
      if updated_time_str:
        updated_time = datetime.datetime.fromtimestamp(time.mktime(feedparser._parse_date(updated_time_str)))

      if not feed_xml:
        logging.debug('feed_xml not found in memcache, query enties')
        pipe = get_pipe(slug)
        if pipe:
          try:
            feed_xml = self.get_feed_xml(pipe, updated_time)

            memcache.add(feed_xml_memcache_key, feed_xml, 60 * 30)#cache ten minutes
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

  def get_feed_xml(self, pipe, updated_time=None):
    title = pipe.title
    subtitle = pipe.subtitle
    alternate = pipe.alternate

    entry_maps = self.get_entry_maps(pipe)
    (scm, netloc, path, params, query, _) = urlparse.urlparse(self.request.url)
    source = urlparse.urlunparse((scm, netloc, path, "", "", ""))
    context = {
      'entries': entry_maps,
      'title':title,
      'subtitle':subtitle,
      'source': source,
      'alternate':alternate
    }
    if entry_maps:
      context['first_entry'] = entry_maps[0]
    feed_xml = template.render('atom.xml', context)
    return feed_xml
    pass
  def get_entry_maps(self, pipe):
    entry_maps = []
    gql = model.FeedEntry.gql("WHERE pipe = :1 ORDER BY updated_time desc", pipe.key())
    entries = gql.fetch(pipe.pipe_feed_size)
    logging.debug('query finish. get %d entries', len(entries))
    for entry in entries:
      new_entry = {}
      new_entry['title'] = entry.title
      new_entry['link'] = entry.link
      new_entry['entry_id'] = entry.entry_id
      new_entry['updated'] = entry.get_updated_time()
      new_entry['published'] = entry.get_published_time()
      new_entry['content'] = entry.content
      entry_maps.append(new_entry)

    return entry_maps
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
    logging.debug('start add feed for %s', pipe_web_address)
    entries_list = memcache.get(random_key)
    if not entries_list:
      return
    entries = entries_list['entries']
    fetch_index = entries_list['fetch_index']
    put_index = entries_list['put_index']
    logging.debug('start add %d entries, fetch_index is %d, put_index is %d.', len(entries), fetch_index, put_index)
    while fetch_index < len(entries):
      try:
        entries[fetch_index].content = fetchpage.fetch_page(entries[fetch_index].link, '<!content_tag txt>', '<!/content_tag txt>')
        #logging.debug('the link is %s, the key_name is %s, the fetch_index= is %d', entries[fetch_index].link, entries[fetch_index].key().id_or_name(), fetch_index)
        fetch_index += 1
      except runtime.DeadlineExceededError, e:
        logging.exception(e)
        logging.debug('we have fetched %d contents', fetch_index - entries_list['fetch_index'])
        entries_list['fetch_index'] = fetch_index
        entries_list['entries'] = entries
        memcache.set(random_key, entries_list, 120)
        add_feed_queue.add(taskqueue.Task(url="/addFeed", params={'key': random_key, 'pipe_web_address': pipe_web_address}))
        return
      except Exception, e :
        logging.exception(e)
        logging.debug('fetch Exception entries[fetch_index].link is %s, current fetch_index is %d', entries[fetch_index].link, fetch_index)
        #skip it
        fetch_index += 1

    logging.debug('fetch finishd. we have fetched %d contents', fetch_index - entries_list['fetch_index'])
    entries_list['fetch_index'] = fetch_index
    entries_list['entries'] = entries
    try:
      while put_index < len(entries):
        db.put(entries[put_index:put_index + 20])
        logging.debug('we put %d entries into database', len(entries[put_index:put_index + 20]))
        put_index = put_index + 20
    except runtime.DeadlineExceededError, e:
      logging.exception(e)
      entries_list['put_index'] = put_index
      entries_list['entries'] = entries
      memcache.set(random_key, entries_list, 120)
      add_feed_queue.add(taskqueue.Task(url="/addFeed", params={'key': random_key, 'pipe_web_address': pipe_web_address}))
      return

    entries_list['put_index'] = put_index
    entries_list['entries'] = entries
    memcache.delete(random_key)
    if pipe_web_address:

      feed_xml_memcache_key = PIPE_OUTPUT_FEED_XML_MEMCACHE_KEY + '_' + pipe_web_address
      #remove the xml catch
      memcache.delete(feed_xml_memcache_key)
      default_feed_queue.add(taskqueue.Task(url="/publish/" + pipe_web_address))

    pass

class RefreshFeedHandler(BaseRequestHandler):
  def get(self, slug):
    if slug and slug[0] == '/':
      slug = slug[1:]
    logging.debug('the slug is %s', slug)
    if not slug:
      pipes = model.Pipe.gql("WHERE auto_refresh = :1", True).fetch(200)
      logging.debug('fetch %d pipes' , len(pipes))
      for pipe in pipes:
        default_feed_queue.add(taskqueue.Task(url="/refreshfeed/" + pipe.pipe_web_address))

      return ['ok']
      pass

    pipe = get_pipe(slug)
    if pipe and pipe.auto_refresh:
      feed_url = pipe.feed_url
      logging.debug('start refresh feed, the feedUrl is ' + feed_url)
      #req_path = self.request.path
      memcache_input_feed_xml_key = INPUT_FEED_XML_MEMCACHE_KEY + '_' + slug
      logging.debug('memcache_feed_xml_key %s', memcache_input_feed_xml_key)
      old_feed_xml = memcache.get(memcache_input_feed_xml_key)
      feed_xml = zrqutil.fetch_content(feed_url)
      if old_feed_xml == feed_xml:
        logging.info('feed_xml not change')
        return ['ok']
      elif not old_feed_xml:
        logging.info('feed_xml not found in cache')
      else:
        logging.info('feed_xml changed')
      logging.debug('start parse feed xml')
      data = feedparser.parse(feed_xml)
      #if alternate change
      try:
        if hasattr(data.feed, 'links'):
          for link in data.feed.links:
            if link.rel == 'alternate' and link.get('href', '') and pipe.alternate != link.href:
              logging.debug('update pipe alternate')
              pipe.alternate = link.href
              pipe.put()
              break
      except Exception, e :
        logging.exception(e)

      entries = get_entries(data, pipe)
      entries = filter_entries(entries, pipe)
      logging.debug('fetch %d entries' , len(entries))
      if len(entries) > 0:
        entries_map = {'entries':entries, 'fetch_index':0, 'put_index':0}
        random_str = get_random_str()
        random_key = slug + '_' + random_str
        memcache.set(random_key, entries_map, 120)

        add_feed_queue.add(taskqueue.Task(url='/addFeed', params={'key': random_key, 'pipe_web_address': pipe.pipe_web_address}))

      memcache.set(memcache_input_feed_xml_key, feed_xml, 60 * 60)
    return ['ok']
  post = get


class pipesEntryUpdateHandler(BaseRequestHandler):
  def get(self, slug):
    updated_random_key = self.request.get("updated_random_key")
    before_updated_time = None
    if updated_random_key:
      before_updated_time = memcache.get(updated_random_key)
    if not before_updated_time:
      updated_random_key = 'updated_random_key' + get_random_str()
      entry = model.FeedEntry.gql("ORDER BY updated_time DESC").get()
      if entry:
        before_updated_time = entry.updated_time
    logging.debug('the before_updated_time')
    if not before_updated_time:
      self.response.out.write('update fail')
      return
    i = 0
    r = 20
    try:
      entries = model.FeedEntry.gql("WHERE updated_time <= :1 ORDER BY updated_time DESC", before_updated_time).fetch(100)
      last_updated_time = entries[-1].updated_time
      max = len(entries)
      logging.debug('we fetch %d entries', max)

      for i in range(len(entries) - 1, -1, -1):
        if not entries[i].published_time:
          entries[i].published_time = entries[i].updated_time
        else:
          entries.remove(entries[i])

      logging.debug('we update %d entries', len(entries))
      i = 0
      while i < len(entries):
        db.put(entries[i:i + r])
        logging.debug('we put %d entries into database', len(entries[i:i + r]))
        i += r
    except runtime.DeadlineExceededError, e:
      #if we dead
      logging.exception(e)
      pass
    finally:
      #clone another me, and continue
      before_updated_time = None
      if i < len(entries):
        before_updated_time = entries[i].updated_time
      elif max == 100:
        before_updated_time = last_updated_time
      logging.debug('max = %d, i = %d, len(entries) = %d', max, i, len(entries))
      if before_updated_time:
        memcache.set(updated_random_key, before_updated_time, 60)
        default_feed_queue.add(taskqueue.Task(url='/pipesEntryUpdate', params={'updated_random_key': updated_random_key}))

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
class clearFeedHandler(BaseRequestHandler):
  def get(self, slug):
    pass
class removeFeedCacheHandler(BaseRequestHandler):
  def get(self, slug):
    logging.debug('remove memcache %s', slug)
    memcache.delete(slug)
    memcache.delete(slug[1:])
class testHandler(BaseRequestHandler):
  def get(self, slug):
    logging.debug('the slug is %s', slug)
    type = self.request.get('type')
    if slug and slug[0] == '/':
      slug = slug[1:]
    if not slug:
      return
    pipe = get_pipe(slug)
    if type == 'xml':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
    elif type == 'update_title':
      key_name = 'key_63e65c339a059b37ed1e0ae31d408d25a688c442'
      feed = model.FeedEntry.get_by_key_name(key_name)
      title = feed.title
      title1 = feed.title
      try:
        #title1 = title1.decode('utf-8')
        title1 = title1.encode('windows-1252')
        title1 = title1.decode('gb2312')
      except Exception , e:
        logging.exception(e)
      logging.debug('t0 is %s t1 is %s', title, title1)
      feed.title = title1
      feed.put()
    elif type == 'parse':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
      data = feedparser.parse(feed_xml)
    elif type == 'filter_entries0':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
      data = feedparser.parse(feed_xml)
      entries = get_entries(data, pipe)
      logging.debug('get %d entries', len(entries))
      key_names = []
      for e in entries:
        key_names.append(e['key_name'])
      entries = filter_entries0(entries, pipe)
      logging.debug('get %d entries', len(entries))
    elif type == 'filter_entries1':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
      data = feedparser.parse(feed_xml)
      entries = get_entries(data, pipe)
      logging.debug('get %d entries', len(entries))
      key_names = []
      for e in entries:
        key_names.append(e['key_name'])
      entries = filter_entries(entries, pipe)
      logging.debug('get %d entries', len(entries))
    elif type == 'filter_entries':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
      data = feedparser.parse(feed_xml)
      entries = get_entries(data, pipe)
      logging.debug('get %d entries', len(entries))
      key_names = []
      for e in entries:
        key_names.append(e['key_name'])
      entries = filter_entries(entries, pipe)
      logging.debug('get %d entries', len(entries))
      for e in entries:
        logging.debug(' e.key().id_or_name() = %s e.link = %s ', str(e.key().id_or_name()), str(e.link))

    elif type == 'time':
      oldest_update_time = datetime.datetime.fromtimestamp(time.mktime(feedparser._parse_date('2010/07/15 07:29:25 +0800')))
      logging.debug('the oldest_update_time is %s', str(oldest_update_time))
    elif type == 'query':
      feed_xml = self.get_xml(pipe)
      logging.debug('the len(feed_xml) is %d', len(feed_xml))
      data = feedparser.parse(feed_xml)
      entries = get_entries(data, pipe)
      logging.debug('start filter %d entries', len(entries))
      oldest_update_time = get_oldest_update_time(entries)
      logging.debug('the oldest_update_time is %s', str(oldest_update_time))
      db_entries = model.FeedEntry.gql("WHERE pipe = :1 AND updated_time >=:2 ORDER BY updated_time DESC", pipe, oldest_update_time).fetch(200)
      logging.debug('query finished. get %d entries', len(db_entries))
      pass
    elif type == 'random':
      logging.debug('the str is %s' , get_random_str())
    elif type == 'getentrycontent':
      #pipe = get_pipe(slug)
      key_name = self.request.get('name')
      if key_name:
        feed = model.FeedEntry.get_by_key_name(key_name)
        self.response.out.write(feed.content)
    elif type == 'fetchpage':
      link = self.request.get('link')
      logging.debug('link is %s', link)
      content = fetchpage.fetch_page(link, '<!content_tag txt>', '<!/content_tag txt>')
      self.response.out.write(content)
    elif type == 'fetchandput':
      link = self.request.get('link')
      logging.debug('link is %s', link)
      if link:
        content = fetchpage.fetch_page(link, '<!content_tag txt>', '<!/content_tag txt>')
        self.response.out.write(content)
        db_entries = model.FeedEntry.gql('WHERE link = :1', link).fetch(20)
        for e in db_entries:
          e.content = content
        db.put(db_entries)
    pass
  def get_xml(self, pipe):
    feed_url = pipe.feed_url
    feed_xml = zrqutil.fetch_content(feed_url)
    return feed_xml
class UpdateHandler(BaseRequestHandler):
  def get(self, slug):
    if slug:
      if slug[0] == '/':
        slug = slug[1:]
      pipe = get_pipe(slug)
      str_from_update_time = '2010-08-12 02:03:01'
      from_update_time = datetime.datetime.strptime(str_from_update_time , '%Y-%m-%d %H:%M:%S')
      logging.debug('from_update_time is %s ,pipe is %s', str(from_update_time), pipe.pipe_web_address)
      db_entries = model.FeedEntry.gql("WHERE pipe = :1 AND updated_time >=:2 ORDER BY updated_time DESC", pipe, from_update_time).fetch(200)
      logging.debug('update %d entries', len(db_entries))
      for entry in db_entries:
        flag = self.update_title(entry)
        if flag == 0:
          logging.debug('remove entry %s', entry.key().id_or_name())
          db_entries.remove(entry)
      logging.debug('entry.title is %s ', db_entries[-1].title)
      
      if len(db_entries) > 0:
        entries_map = {'entries':db_entries, 'fetch_index':len(db_entries), 'put_index':0}
        random_str = get_random_str()
        random_key = slug + '_' + random_str
        memcache.set(random_key, entries_map, 120)

        add_feed_queue.add(taskqueue.Task(url='/addFeed', params={'key': random_key, 'pipe_web_address': pipe.pipe_web_address}))
      pass
    
    
    pass
  def update_title(self, entry):
    title1 = entry.title
    try:
      #title1 = title1.decode('utf-8')
      title1 = title1.encode('windows-1252')
      title1 = title1.decode('gb2312')
    except Exception , e:
      logging.exception(e)
      return 0
    entry.title = title1
    return 1
    pass
def get_random_str():
  return hashlib.sha256(str(random.randint(0, sys.maxint))).hexdigest()

def get_oldest_update_time(entries):
  if len(entries) == 0:
    return datetime.datetime.now()
  update_time = entries[0]['updated_time']
  for e in entries:
    #logging.debug('updated_time %s', str(e['updated_time']))
    if e['updated_time'] < update_time:
      update_time = e['updated_time']
  return update_time

def filter_entries0(entries, pipe):
  logging.debug('start filter %d entries', len(entries))
  #oldest_update_time = get_oldest_update_time(entries)
  key_names = []
  for e in entries:
    key_names.append(e['key_name'])
  db_entries = model.FeedEntry.get_by_key_name(key_names)
  for db_e in db_entries[:]:
    if not db_e:
      db_entries.remove(db_e)
  logging.debug('query finished. get %d entries', len(db_entries))
  #latest_updated_time = db_entries[0].updated_time if len(db_entries) > 0 else None
  new_entries = []

  for e in entries:
    new_entry = None
    isExist = False
    for db_e in db_entries:
      if db_e and e['key_name'] == db_e.key().id_or_name() :
        if e['updated_time'] != db_e.updated_time:
          new_entry = db_e
          new_entry.entry_id = e['entry_id']
          new_entry.title = e['title']
          new_entry.link = e['link']
          new_entry.updated_time = e['updated_time']
      isExist = True
      db_entries.remove(db_e)
      break
    if not isExist:
      new_entry = model.FeedEntry(key_name=e['key_name'],
                              pipe=pipe,
                              entry_id=e['entry_id'],
                              title=e['title'],
                              link=e['link'],
                              updated_time=e['updated_time'],
                              published_time=e['published_time'],
                              content=e['content'])

    if new_entry:
      new_entries.append(new_entry)

  return new_entries

def filter_entries(entries, pipe):
  logging.debug('start filter %d entries', len(entries))
  oldest_update_time = get_oldest_update_time(entries)
  logging.debug('the oldest_update_time is %s', str(oldest_update_time))
  db_entries = model.FeedEntry.gql("WHERE pipe = :1 AND updated_time >=:2 ORDER BY updated_time DESC", pipe, oldest_update_time).fetch(200)
  logging.debug('query finished. get %d entries', len(db_entries))
  new_entries = []
  for e in entries:
    new_entry = None
    isExist = False
    for db_e in db_entries:
      if e['key_name'] == db_e.key().id_or_name():
        if e['updated_time'] != db_e.updated_time:
          new_entry = db_e
          new_entry.entry_id = e['entry_id']
          new_entry.title = e['title']
          new_entry.link = e['link']
          new_entry.updated_time = e['updated_time']
        isExist = True
        db_entries.remove(db_e)
        break
    if not isExist:
      new_entry = model.FeedEntry(key_name=e['key_name'],
                              pipe=pipe,
                              entry_id=e['entry_id'],
                              title=e['title'],
                              link=e['link'],
                              updated_time=e['updated_time'],
                              published_time=e['published_time'],
                              content=e['content'])
    if new_entry:
      new_entries.append(new_entry)

  return new_entries
def filter_entries1(entries, pipe):
  logging.debug('start filter %d entries', len(entries))
  oldest_update_time = get_oldest_update_time(entries)
  logging.debug('the oldest_update_time is %s', str(oldest_update_time))
  db_entries = model.FeedEntry.gql("WHERE pipe = :1 AND updated_time >=:2 ORDER BY updated_time DESC", pipe, oldest_update_time).fetch(200)
  logging.debug('query finished. get %d entries', len(db_entries))
  latest_updated_time = db_entries[0].updated_time if len(db_entries) > 0 else None
  new_entries = []
  for e in entries:
    new_entry = None
    if not latest_updated_time or (e['updated_time'] > latest_updated_time):
      new_entry = model.FeedEntry(key_name=e['key_name'],
                              pipe=pipe,
                              entry_id=e['entry_id'],
                              title=e['title'],
                              link=e['link'],
                              updated_time=e['updated_time'],
                              published_time=e['published_time'],
                              content=e['content'])
    else:
      for db_e in db_entries:
        if e['key_name'] == db_e.key().id_or_name() :
          if e['updated_time'] != db_e.updated_time:
            new_entry = db_e
            new_entry.entry_id = e['entry_id']
            new_entry.title = e['title']
            new_entry.link = e['link']
            new_entry.updated_time = e['updated_time']
        db_entries.remove(db_e)
        break

    if new_entry:
      new_entries.append(new_entry)

  return new_entries
def get_entries(data, pipe):
  try:

    if data.bozo:
      logging.error('Bozo feed data. %s: %r',
                     data.bozo_exception.__class__.__name__,
                     data.bozo_exception)
      if (hasattr(data.bozo_exception, 'getLineNumber') and
          hasattr(data.bozo_exception, 'getMessage')):
        line = data.bozo_exception.getLineNumber()
        logging.error('Line %d: %s', line, data.bozo_exception.getMessage())
      #return None
    #getfeed
    #feed = data.feed
    #subtitle, title = feed.subtitle, feed.title
    logging.debug('the feed has %d entries', len(data.entries))
    entries = []
    for entry in data.entries:
      link = entry.get('link', '')
      title = entry.get('title', '')
      updated = entry.get('updated_parsed', '')
      published = entry.get('published_parsed', '')
      if updated and not published:
        published = updated
      elif not updated and published:
        updated = published
      elif not updated and not published:
        published = updated = datetime.datetime.now()

      updated_time = datetime.datetime.fromtimestamp(time.mktime(updated))
      published_time = datetime.datetime.fromtimestamp(time.mktime(published))
      content = ''

      if hasattr(entry, 'content'):
        # This is Atom.
        content = entry.content[0].value
      else:
        content = entry.get('description', '')

      entry_id = entry.get('id', '') or hashlib.sha1(link or title).hexdigest()
      pipe_key = str(pipe.key().id_or_name())
      key_name = 'key_' + hashlib.sha1(pipe_key + "_" + entry_id).hexdigest()
      #we put it in a map
      new_entry = {}
      new_entry['key_name'] = key_name
      new_entry['pipe'] = pipe
      new_entry['entry_id'] = entry_id
      new_entry['title'] = title
      new_entry['link'] = link
      new_entry['updated_time'] = updated_time
      new_entry['published_time'] = published_time
      new_entry['content'] = content
      entries.append(new_entry)

    logging.debug('parse feed xml finish!')
  except Exception , e:
    logging.exception(e)


  return entries
def get_pipe(pipe_web_address):
  pipe_memcache_key = PIPE_MEMCACHE_KEY + '_' + pipe_web_address
  pipe = memcache.get(pipe_memcache_key)
  if pipe is not None:
    return pipe
  else:
    pipe = model.Pipe.gql("WHERE pipe_web_address = :1", pipe_web_address).get()
    memcache.add(pipe_memcache_key , pipe , 60 * 60 * 12)#12 hours
    return pipe
  pass
def main():
  application = webapp.WSGIApplication([('/pipes(/.*)?', PipesHandler),
                                        ('/addPipe/{0,1}', AddPipeHandler),
                                        ('/publish(/.*)?', PublishHandler),
                                        ('/refreshfeed(/.*)?', RefreshFeedHandler),
                                        ('/addFeed(/.*)?', addFeedEntryHandler),
                                        ('/delFeed(/.*)?', delFeedEntryHandler),
                                        ('/pipesEntryUpdate(/.*)?', pipesEntryUpdateHandler),
                                        ('/update(/.*)?', UpdateHandler),
                                        ('/clearFeed(/.*)?', clearFeedHandler),
                                        ('/removeFeedCache(/.*)?', removeFeedCacheHandler),
                                        ('/test(/.*)?', testHandler),

                                        ], debug=True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
