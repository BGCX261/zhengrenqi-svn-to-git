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
import xml.dom.minidom
import zzzutil


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
    #for e in data:
      #if e != 'entries':
        #print e, data[e]
    feed = data.feed
    description, title = feed.subtitle, feed.title

    entry = data.entries[0]
    print '-----'
    for e in entry:
      print e, entry[e]
    updated_parsed = entry.updated_parsed
    print time.asctime(updated_parsed)
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
  def test03(self):
    html_content = open('test.htm').read()
    print self.get_content(html_content)
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
    

if __name__ == "__main__":
  import sys;sys.argv = ['', 'Test.testwsjallfullrss']
  unittest.main()
