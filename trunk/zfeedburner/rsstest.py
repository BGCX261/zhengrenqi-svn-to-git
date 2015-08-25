# -*- coding: utf-8 -*-
'''
Created on 2010-7-7

@author: 郑仁启
'''
from cgi import parse_header
from google.appengine.ext.webapp import template
from xml.dom.minidom import Element
import datetime
import feedparser
import hashlib
import logging
import random
import re
import string
import time
import unittest
import urllib2
import urlparse
import xml.dom.minidom
import fetchpage


class Test(unittest.TestCase):


  def setUp(self):
    pass


  def tearDown(self):
    pass


  def testwsjallfullrss(self):
    #resp = urllib2.urlopen('http://pipes.yahoo.com/pipes/pipe.run?_id=2440e3be9621a932e4063eb0dd30196b&_render=rss')
    #rssxml = resp.read()
    rssxml = open('wsjrssall.xml').read()
    #print '1e'.rjust(2,'0')
    #hex_xml = ' '.join([hex(int(ord(c)))[2:].rjust(2,'0') for c in rssxml[:500]])
    #print hex_xml
    #print rssxml[275:295],rssxml[283:286]
    data = feedparser.parse(rssxml)
    if data.bozo:
      print 'Bozo feed data. %s: %r', data.bozo_exception.__class__.__name__, data.bozo_exception
      if (hasattr(data.bozo_exception, 'getLineNumber') and
          hasattr(data.bozo_exception, 'getMessage')):
        line = data.bozo_exception.getLineNumber()
        print 'Line %d: %s', line, data.bozo_exception.getMessage()
        segment = self.request.body.split('\n')[line - 1]
        print 'Body segment with error: %r', segment.decode('utf-8')
    for e in data.feed:
      if e != 'entries':
        print e, data.feed[e]
    feed = data.feed
    description, title = feed.subtitle, feed.title
    alternate = ''
    print '-----', type(feed.links), len(feed.links)
    for link in feed.links:
      if link.rel == 'alternate' and link.get('href', ''):
        print link.href
    print '-----'
    print 'link', feed.link
    entry = data.entries[0]
    print '-----'
    for e in entry:
      print e, entry[e]
    published_parsed = entry.get('published_parsed', '')
    published = entry.get('published', '')
    updated_parsed = entry.updated_parsed
    print updated_parsed
    print published, published_parsed
    print '-----'
    source = 'http://renqiapp.appspot.com/pipes/wsjallfullrss'
    entries = []
    for entry in data.entries:
      new_entry = {}
      new_entry['link'] = entry.get('link', '')
      new_entry['title'] = entry.get('title', '')
      new_entry['updated'] = entry.get('updated', '')
      if hasattr(entry, 'content'):
        # This is Atom.
        new_entry['content'] = entry.content[0].value
      else:
        new_entry['content'] = entry.get('description', '')

      new_entry['id'] = entry.get('id', '') or source + "/" + hashlib.sha1((new_entry['link'] or new_entry['title'] or new_entry['content'])).hexdigest()


      entries.append(new_entry)
    context = {
      'entries': entries,
      'title':title,
      'description':description,
      'source': source,
    }
    if entries:
      context['first_entry'] = entries[0]
    rssxml = template.render('atom.xml', context)
    #print rssxml

    pass
  def test02(self):
    wsjrssall = open('wsjallfullrss.xml', 'r')
    rssxml = wsjrssall.read()
    xml_doc = xml.dom.minidom.parseString(rssxml)
    print xml_doc.getElementsByTagName('channel')
    channel = xml_doc.getElementsByTagName('channel')[0]
    #print channel.childNodes
    #print channel.getElementsByTagName('link')

    for l in channel.getElementsByTagName('link'):
      if l in channel.childNodes:
        ognl_link = l
        break
    link = Element('link')
    link.setAttribute('href', 'http://pubsubhubbub.appspot.com')
    link.setAttribute('rel', 'hub')
    channel.insertBefore(link, ognl_link.nextSibling)

    #print xml_doc.toxml()
    pass
  def test_get_page(self):
    print 'start'
    url = 'http://cn.wsj.com/gb/20100721/rth080855.asp?source=rss'
    html_content = urllib2.urlopen(url).read()
    cut_content_from = '<!content_tag txt>'
    cut_content_to = '<!/content_tag txt>'
    
    charset = fetchpage.get_charset(html_content)
    content_tag_start = html_content.find(cut_content_from)
    content_tag_end = html_content.find(cut_content_to, content_tag_start)
    content = html_content[content_tag_start + len(cut_content_from):content_tag_end].decode(charset, 'ignore')
    content = fetchpage.remove_scriptag(content)
    accessed_url = url[:url.rfind('/') + 1] if url[-1] != '/' else url[:url[:-1].rfind('/') + 1]
    content = fetchpage.replace_url(content, accessed_url)
    
    print 'finished'
    print content
    print 'end'
    pass
  def get_content(self, html_content):
    charset = self.get_charset(html_content)
    content_tag_start = html_content.find('<!content_tag txt>')
    content_tag_end = html_content.find('<!/content_tag txt>', content_tag_start)
    return html_content[content_tag_start + len('<!content_tag txt>'):content_tag_end].decode(charset)
  def get_charset(self, html_content):
    i = 0
    while True:
      i = html_content.find('<meta', i)
      if i == -1:
        break
      attrfind = re.compile(
          r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'
          r'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@]*))?')
      tagfind = re.compile('[a-zA-Z][-.a-zA-Z0-9:_]*')
      match = tagfind.match(html_content, i + 1)
      endpos = self.check_for_whole_start_tag(html_content, i)
      k = match.end()
      attrs = []
      while k < endpos:
        m = attrfind.match(html_content, k)
        if not m:
            break
        attrname, rest, attrvalue = m.group(1, 2, 3)
        if not rest:
            attrvalue = None
        elif attrvalue[:1] == '\'' == attrvalue[-1:] or \
             attrvalue[:1] == '"' == attrvalue[-1:]:
            attrvalue = attrvalue[1:-1]
        attrs.append((attrname.lower(), attrvalue))
        k = m.end()
      for attr in attrs:
        if attr[0] == 'http-equiv' and string.lower(attr[1]) == 'content-type':
          for attr in attrs:
            if attr[0] == 'content':
              (ct, parms) = parse_header(attr[1])
              if parms.has_key('charset'):
                return parms['charset']
          break
      i = endpos
    return 'UTF-8'
  def check_for_whole_start_tag(self, rawdata, i):
      locatestarttagend = re.compile(r"""
        <[a-zA-Z][-.a-zA-Z0-9:_]*          # tag name
        (?:\s+                             # whitespace before attribute name
          (?:[a-zA-Z_][-.:a-zA-Z0-9_]*     # attribute name
            (?:\s*=\s*                     # value indicator
              (?:'[^']*'                   # LITA-enclosed value
                |\"[^\"]*\"                # LIT-enclosed value
                |[^'\">\s]+                # bare value
               )
             )?
           )
         )*
        \s*                                # trailing whitespace
      """, re.VERBOSE)
      m = locatestarttagend.match(rawdata, i)
      if m:
          j = m.end()
          next = rawdata[j:j + 1]
          if next == ">":
              return j + 1
          if next == "/":
              if rawdata.startswith("/>", j):
                  return j + 2
              if rawdata.startswith("/", j):
                  # buffer boundary
                  return - 1
              # else bogus input
          if next == "":
              # end of input
              return - 1
          if next in ("abcdefghijklmnopqrstuvwxyz=/"
                      "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
              # end of input in or before attribute value, or we have the
              # '/' from a '/>' ending
              return - 1
  def testdate(self):
    dates0 = '2010/07/07 14:40:24 +0800'
    #print feedparser._parse_date(dates0)
    #dates1 = '2010-07-07T14:49:24 +0800'
    #print feedparser._parse_date(dates1)
    date = feedparser._parse_date(dates0)

    t = datetime.datetime.fromtimestamp(time.mktime(date))
    print t.strftime("%Y-%m-%dT%H:%M:%SZ"), time.asctime(date)
    #print time.timezone
    #print ord('a'), ord('z')
    #print ''.join([chr(random.randint(97, 122))for i in range(0, 16)])[16:20]
    #print ''.join([chr(i) for i in range(97, 123)])
  def testforeach(self):
    li = ['1', '2', '4', '6', '8', '3', '5']
    for i in range(len(li) - 1, -1, -1):
      print i
      if int(li[i]) % 2 == 0:
        li.remove(li[i])
    print li
  def test_fetch_page(self):
    url = 'http://cn.wsj.com/gb/20100710/bus094831.asp?source=rss'
    accessed_url = url[:url.rfind('/') + 1] if url[-1] != '/' else url[:url[:-1].rfind('/') + 1]
    print accessed_url
    cut_content_from = '<!content_tag txt>'
    cut_content_to = '<!/content_tag txt>'
    resp = urllib2.urlopen(url)
    html_content = resp.read()

    charset = fetchpage.get_charset(html_content)
    content_tag_start = html_content.find(cut_content_from)
    content_tag_end = html_content.find(cut_content_to, content_tag_start)
    content = html_content[content_tag_start + len('<!content_tag txt>'):content_tag_end].decode(charset)
    content = remove_scriptag(content, 'script')
    content = replace_url(content, accessed_url)
    print content
  def testreg(self):

    ognl = """
    <br><script src='../truthmeter.js' type='text/javascript'></script><div style='font-size:14px' id='companyname'><script language=javascript>document.write (truthmeter('2010年07月10日08:30', 'CADAY'));</script></div>
    """
    pattern = '<script[^>]*>.*?</script>'
    content = re.sub(pattern, '', ognl)
    print content
  def teststr(self):
    c = ''
    c = unicode(c)
    print repr(c)
    print c
    pass
  def testerror(self):
    try:
      print 'try'
      a = '1' + 1
    except:
      print 'except'
    finally:
      print 'finally'
  def testmap(self):
    d = {'a':'a', 'b': 1}
    print  d['a'], d['b']
    print dir(d)
    print hasattr(d, 'a')
    
  def testdatetime(self):
    print datetime.datetime.now() > None
  def testurl(self):
    (scm, netloc, path, params, query, _) = urlparse.urlparse('http://test0.latest.zfeedburner.appspot.com/pipes/wsjall?updated_time=2010-07-15T12:43:19+08:00')
    path = urlparse.urlunparse((scm, "zfeedburner.appspot.com", path, "", "", ""))
    print path
    pass
  def testrandom(self):
    max_int = sys.maxint
    max_size = sys.maxsize
    print max_int , max_size
    print type(max_int), type(max_size)
    print hashlib.sha256(str(random.randint(0, sys.maxint))).hexdigest()
    for i in range(10):
      print hashlib.sha256(str(random.randint(0, sys.maxint))).hexdigest()
    pass
  def testsort(self):
    
    pass
def remove_scriptag(content, *tags):
  pattern = r'<script[^>]*>.*?</script>'
  content = re.sub(pattern, '', content)
  return content
def replace_url(content, accessed_url):
  TAG_START = r"(?i)\b(?P<tag>src|href|action|url|background)(?P<equals>[\t ]*[=|(][\t ]*)(?P<quote>[\"']?)"
  TRAVERSAL_URL_REGEX = r"(?P<relative>\.(\.)?)/(?!(/)|(http(s?)://)|(url\())(?P<url>[^\"'> \t\)]*)"
  pattern = TAG_START + TRAVERSAL_URL_REGEX
  print pattern
  replacement = "\g<tag>\g<equals>\g<quote>%(accessed_url)s\g<relative>/\g<url>" % {
      "accessed_url": accessed_url,
    }
  print replacement
  content = re.sub(pattern, replacement, content)
  return content
if __name__ == "__main__":
  import sys;sys.argv = ['', 'Test.test_get_page']
  unittest.main()
