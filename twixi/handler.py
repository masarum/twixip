# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from twixi.model import TwixiUser
from mixi import mixi
import twixi
import urllib2
import logging
from xml.etree import ElementTree
import datetime
import pytz

class SyncHandler(webapp.RequestHandler):
  usertl_url_format = ('http://twitter.com/statuses/'
                       'user_timeline.%s?'
                       'screen_name=%s')
  title_date_format = '%Y-%m-%d'
  date_format = '%H:%M'
  body_format = u'　%(content)s （%(date)s）\n\n'

  def newTweets(self, user, format):
    screen_name = user.twitter_screen_name
    url = self.usertl_url_format % (format, screen_name)
    if user.last_tweetid is not None:
      url = url+'&since_id='+user.last_tweetid      
    try:
      logging.debug('opening timeline: %s', url)
      feed = urllib2.urlopen(url)
    except urllib2.URLError:
      logging.error("Cant fetch %s's timeline" % screen_name)
      return None
    logging.debug(feed)
    (tweets, lastid) = self.parseAtom(feed)
    if tweets is None:
      logging.error("Bad Feed")
      return None
    if (lastid is not None):
        user.last_tweetid = str(lastid)
        user.put()
    return tweets
      

  def parseAtom(self, atom):
    tweets = dict()
    tree = ElementTree.parse(atom)
    logging.debug(tree)
    entries = tree.findall('{http://www.w3.org/2005/Atom}entry')
    lastid = None
    for entry in entries:
      datestring = entry.find('{http://www.w3.org/2005/Atom}published').text
      published = datetime.datetime.strptime(datestring,
                                             "%Y-%m-%dT%H:%M:%S+00:00")
      tweets[published] = entry.find('{http://www.w3.org/2005/Atom}content').text
      id = entry.find('{http://www.w3.org/2005/Atom}id').text
      id = int(id.rsplit('/', 1)[1]);
      if id > lastid or lastid is None:
        lastid = id
    return (tweets, lastid)


  def prettyFormat(self, tweets, user):
    usertz = pytz.timezone(user.timezone)
    dates = tweets.keys()
    dates.sort()
    logging.debug(dates)
    title = usertz.localize(dates[0]).strftime(self.title_date_format)
    
    header = user.twitter_screen_name+': '
    body = ''
    for date in dates:
      fmtdate = pytz.utc.localize(date)
      fmtdate = fmtdate.astimezone(usertz).strftime(self.date_format)
      content = tweets[date]
      if content.startswith(header):
        content = content[len(header):len(content)]
      if content.startswith('@'):
        continue
      body += (self.body_format.encode('utf-8') %
               {'date':fmtdate, 'content':content.encode('utf-8')})
    return (title, body)


  def get(self, screen_name):
    query = TwixiUser.all()
    user = query.filter('twitter_screen_name =', screen_name).get()
    if user is None:
      self.error(500)
      logging.error("No user with twitter screen name %s" % screen_name)
      return

    tweets = self.newTweets(user, 'atom')
    logging.debug(tweets)
    if not tweets or len(tweets) == 0:
      self.response.out.write('No new tweets\n')
      return

    (title, body) = self.prettyFormat(tweets, user)
    logging.debug(title)
    logging.debug(body)
  
    service = mixi.Service(user.mixi_username,
                           twixi.Decrypt(user.mixi_password),
                           user.mixi_memberid)
    entry = mixi.DiaryEntry(title, body)
    (response, body) = service.postDiary(entry);

    self.response.set_status(response.status, response.reason.encode('utf-8'))
    self.response.out.write(body.encode('utf-8'))

class AddUserHandler(webapp.RequestHandler):
  def get(self):
    logging.info('adding user')
    tsn = self.request.get('tsn')
    mun = self.request.get('mun')
    mpw = self.request.get('mpw')
    mid = self.request.get('mid')
    tz = self.request.get('tz')
    user = TwixiUser(twitter_screen_name=tsn,
                     mixi_username=mun,
                     mixi_password=mpw,
                     mixi_memberid=mid,
                     timezone=tz)
    user.put()
    self.response.out.write('OK\n')

