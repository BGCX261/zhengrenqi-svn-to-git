# -*- coding: utf-8 -*-
'''
Created on 2010-7-14

@author: 郑仁启
'''
from cgi import parse_header
from google.appengine.api import urlfetch
import logging
import re
import string

def fetch_page(url, cut_content_from, cut_content_to):
  html_content = fetch_content(url)
  
  charset = get_charset(html_content)
  content_tag_start = html_content.find(cut_content_from)
  content_tag_end = html_content.find(cut_content_to, content_tag_start)
  content = html_content[content_tag_start + len(cut_content_from):content_tag_end].decode(charset, 'ignore')
  content = remove_scriptag(content)
  accessed_url = url[:url.rfind('/') + 1] if url[-1] != '/' else url[:url[:-1].rfind('/') + 1]
  content = replace_url(content, accessed_url)
  return content
  pass
def fetch_content(url, fetch_limit=5):
  fetch_count = 0
  while True:
    fetch_count += 1
    if fetch_count > fetch_limit:
      break
    try:
      resp = urlfetch.fetch(url)
      break
    except Exception , e:
      logging.exception(e)

  content = resp.content
  if fetch_count > 1:
    logging.debug('fetch %d times and the size of content is %s' , fetch_count, str(len(content)))
  return content
def get_charset(html_content):
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
    endpos = check_for_whole_start_tag(html_content, i)
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
def check_for_whole_start_tag(rawdata, i):
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

def remove_scriptag(content):
  pattern = r'<script[^>]*>.*?</script>'
  content = re.sub(pattern, '', content)
  return content
def replace_url(content, accessed_url):
  TAG_START = r"(?i)\b(?P<tag>src|href|action|url|background)(?P<equals>[\t ]*[=|(][\t ]*)(?P<quote>[\"']?)"
  TRAVERSAL_URL_REGEX = r"(?P<relative>\.(\.)?)/(?!(/)|(http(s?)://)|(url\())(?P<url>[^\"'> \t\)]*)"
  pattern = TAG_START + TRAVERSAL_URL_REGEX
  replacement = "\g<tag>\g<equals>\g<quote>%(accessed_url)s\g<relative>/\g<url>" % {
      "accessed_url": accessed_url,
    }
  print replacement
  content = re.sub(pattern, replacement, content)
  return content
