from google.appengine.ext import webapp
from twixi.model import TwixiUser
from mixi import mixi
import twixi
import urllib2
import logging

class SyncHandler(webapp.RequestHandler):
  def newTweets(self, user, format):
    pass

  def parseAtom(self, atom):
    pass

  def prettyFormat(self, tweets):
    pass

  def get(self, screen_name):
    query = TwixiUser.all()
    user = query.filter('twitter_screen_name =', screen_name).get()
    if user is None:
      self.response.set_status(500, "No user with twitter "
                                    "screen name %s" % screen_name)
      return

    tweet_atom = self.newTweets(user, 'atom')
    if tweet_atom is None:
      self.response.set_status(500, "Cant fetch %s's timeline" % screen_name)
      return
    logging.debug(tweet_atom)

    tweets = self.parseAtom(tweet_atom)
    if tweets is None:
      self.response.set_status(500, "Bad Feed")
      return
    logging.debug(tweets)

    (title, body) = self.prettyFormat(tweets)
    logging.debug(title)
    logging.debug(body)
  
    service = mixi.Service(user.mixi_username,
                           twixi.Decrypt(user.mixi_password),
                           user.mixi_memberid)
    entry = mixi.DiaryEntry(title, body)
    (response, body) = service.postDiary(entry);

    self.response.set_status(response.status, response.reason)
    self.response.out.write(body)


