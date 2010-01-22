from google.appengine.ext import db

class TwixiUser(db.Model):
  twitter_screen_name = db.StringProperty(required=True)
  mixi_username = db.StringProperty(required=True)
  mixi_password = db.StringProperty(required=True)
  mixi_memberid = db.StringProperty(required=True)

