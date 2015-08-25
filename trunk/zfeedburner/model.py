# -*- coding: utf-8 -*-
'''
Created on 2010-4-22

@author: zhengrenqi
'''
from google.appengine.ext import db

#common

class User(db.Model):
  user = db.UserProperty(required = False)
  dispname = db.StringProperty()
  email = db.StringProperty()
  isadmin = db.BooleanProperty(default = False)

#common

#pipes
class Pipe(db.Model):
  pipe_web_address = db.StringProperty()
  title = db.StringProperty()
  subtitle = db.StringProperty()
  feed_url = db.StringProperty()
  alternate = db.StringProperty()
  auto_refresh = db.BooleanProperty(default = False)
  pipe_feed_size = db.IntegerProperty(default = 50)

class FeedAction(db.Expando):
  pipe = db.ReferenceProperty(Pipe)
  type = db.StringProperty()

class FeedEntry(db.Model):
  pipe = db.ReferenceProperty(Pipe)
  entry_id = db.StringProperty()
  title = db.StringProperty(multiline = True)
  link = db.StringProperty()
  updated_time = db.DateTimeProperty()
  published_time = db.DateTimeProperty()
  content = db.TextProperty()
  def pipe_id(self):
    return FeedEntry.pipe.get_value_for_datastore(self)
  def get_updated_time(self):
    return self.updated_time.strftime("%Y-%m-%dT%H:%M:%SZ")
  def get_published_time(self):
    return self.updated_time.strftime("%Y-%m-%dT%H:%M:%SZ")
