import fix_path
import json, pickle
import random
import webapp2

from google.appengine.ext import ndb

# Define Picture Class to store links of pictures
class Picture(ndb.Model):
  id = ndb.IntegerProperty()
  link = ndb.StringProperty()
  date = ndb.DateProperty(auto_now_add=True)

class RecordCount(ndb.Model):
  count = ndb.IntegerProperty()

# --------------------------------------Helper Functions--------------------------------------------
def create_database():
  """Creates a new database of Picture entities"""
  # Delete all existing entries on Datastore
  ndb.delete_multi(Picture.query().iter(keys_only=True))
  ndb.delete_multi(RecordCount.query().iter(keys_only=True))

  # Load curated list of URLS on the server
  urls = pickle.load(open('raw_list.p','r'))

  record_count = RecordCount(count = len(urls))
  record_count.put()

  picture_list = []
  counter = 1
  for url in urls:
    picture_list.append(Picture(id=counter,link=url))
    counter += 1

  ndb.put_multi(picture_list)

def get_random_integers(max_num, count):
  """Returns a list of random integer, given the maximum random number and count. Unique numbers
  """
  randoms = set()
  while len(randoms) < count:
    randoms.add(random.randint(1,max_num))

  return list(randoms)

def get_record_count():
  """Returns the record count of the Picture Datastore"""
  record_counts_list = RecordCount.query().fetch(1)
  return record_counts_list[0].count

# --------------------------------------Handler Classes---------------------------------------------

class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('All the corgis!')

class Random(webapp2.RequestHandler):
  """Return a JSON file containing one picture link from the database"""
  def get(self):
    # Get the record count of the Picture DataStore
    record_count = get_record_count()
    index = random.randint(1,record_count)
    url = {'corgi':''}

    query = Picture.query(Picture.id == index)
    picture = query.fetch(1)[0]
    url['corgi'] = picture.link

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(url))

class Bomb(webapp2.RequestHandler):
  """Return a JSON file containing several picture links"""
  def get(self):
    count = self.request.get('count','4')

    # Check input validation
    if count.isdigit():
      count = int(count)
    else:
      self.redirect('/random')
      return

    if count <= 0:
      self.redirect('/random')
      return

    # Keep it at a sane level
    if count > 10: count = 10

    # Get the record count of the Picture DataStore
    record_count = get_record_count()

    # Get pictures
    urls = {'corgis':[]}

    picture_ids = get_random_integers(record_count,count)
    query = Picture.query(Picture.id.IN(picture_ids))

    for picture in query:
      urls['corgis'].append(picture.link)

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(urls))

class Dump(webapp2.RequestHandler):
  """Returns a JSON of fresh pictures to manually curate from Tumblr"""
  def get(self):
    list_of_pictures = get_all_pics()
    self.response.headers['Content-Type'] = 'application/json'
    self.response.write(json.dumps(list_of_pictures))

class Initialize(webapp2.RequestHandler):
  def get(self):
    from lib.bcrypt import bcrypt
    key = self.request.get('key','')
    hashed = '$2a$05$NSuQjRz0fYFLu/SWJDp.Xup98aDotj.Xf4EtkbdUG7hE15.yrolXC'

    if bcrypt.hashpw(key, hashed) != hashed:
      self.redirect('/')
    else:
      create_database()
      self.response.out.write('All the corgis initialized!')

router = [('/',MainPage),
          ('/random',Random),
          ('/bomb',Bomb),
          ('/dump',Dump),
          ('/init',Initialize)]

app = webapp2.WSGIApplication(router)
