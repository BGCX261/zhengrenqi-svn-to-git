# -*- coding: utf-8 -*-
'''
Created on 2010-4-22

@author: zhengrenqi
'''
from google.appengine.ext import db
PUBLIC = 0
PRIVATE = 1

#common
  
class User(db.Model):
  user = db.UserProperty(required=False)
  dispname = db.StringProperty()
  email = db.StringProperty()
  isadmin = db.BooleanProperty(default=False)
  
#common

class Tag(db.Model):
  tag = db.StringProperty(multiline=False)
  parent_tag = db.SelfReference()
  add_date = db.DateTimeProperty(default=db.DateTimeProperty.now())
  tagcount = db.IntegerProperty(default=0)

class Bookmark(db.Model):
  url = db.StringProperty(multiline=False)
  add_date = db.DateTimeProperty(default=db.DateTimeProperty.now())
  title = db.StringProperty(multiline=False)
  tags = db.StringListProperty()
  owner = db.ReferenceProperty(User)
  def save(self):
    pass
  


#news

class News(db.Model):
  link = db.StringProperty()
  title = db.StringProperty()
  description = db.TextProperty()
  pubDate = db.DateTimeProperty()
  
  
#pipes
class Pipe(db.Model):
  pipe_web_address = db.StringProperty()
  title = db.StringProperty()
  subtitle = db.StringProperty()
  feed_url = db.StringProperty()
  auto_refresh = db.BooleanProperty(default=False)

class FeedAction(db.Expando):
  pipe = db.ReferenceProperty(Pipe)
  type = db.StringProperty()
  
class FeedEntry(db.Model):
  pipe = db.ReferenceProperty(Pipe)
  entry_id = db.StringProperty()
  title = db.StringProperty(multiline=True)
  link = db.StringProperty()
  updated_time = db.DateTimeProperty()
  content = db.TextProperty()
  def pipe_id(self):
    return FeedEntry.pipe.get_value_for_datastore(self)
  def get_updated_time(self):
    return self.updated_time.strftime("%Y-%m-%dT%H:%M:%SZ")
