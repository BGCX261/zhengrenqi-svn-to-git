# -*- coding: utf-8 -*-
'''
Created on 2010-4-30

@author: zhengrenqi

'''

from functools import wraps
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from model import User
import logging
import os

def requires_admin(method):
  @wraps(method)
  def wrapper(self, *args, **kwargs):
    if not self.is_login:
      self.redirect(users.create_login_url(self.request.uri))
      return
    elif not (self.is_admin
      or self.user):
      return self.error(403)
    else:
      return method(self, *args, **kwargs)
  return wrapper


class BaseRequestHandler(webapp.RequestHandler):
  def __init__(self):
    self.current = 'home'
    pass
  def initialize(self, request, response):
    webapp.RequestHandler.initialize(self, request, response)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    
    self.login_user = users.get_current_user()
    self.is_login = (self.login_user != None)
    self.loginurl = users.create_login_url(self.request.uri)
    self.logouturl = users.create_logout_url(self.request.uri)
    self.is_admin = users.is_current_user_admin()

    if self.is_admin:
      self.auth = 'admin'
      self.user = User.all().filter('email =', self.login_user.email()).get()
      if not self.user:
        self.user = User(dispname = self.login_user.nickname(), email = self.login_user.email())
        self.user.isadmin = True
        self.user.user = self.login_user
        self.user.put()
    elif self.is_login:
      self.user = User.all().filter('email =', self.login_user.email()).get()
      if self.user:
        self.auth = 'user'
      else:
        self.auth = 'login'
    else:
      self.auth = 'guest'

    try:
      self.referer = self.request.headers['referer']
    except:
      self.referer = None

    self.template_vals = {'self':self, 'current':self.current}

  def render(self, template_file, template_vals = {}):
    template_path = os.path.join(ROOT_DIR, template_file)
    logging.debug('template_path is %s ', template_path)
    self.response.out.write(template.render(template_path, self.template_vals))


ROOT_DIR = os.path.dirname(__file__)
