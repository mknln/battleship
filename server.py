from flask import Flask, request, session, url_for, redirect, \
    g, flash, _app_ctx_stack, json, jsonify, make_response
from flaskext.mysql import MySQL
from ship_game import GameBoard, BoardSerializer

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('BATTLESHIP_CONFIG')

mysql = MySQL()
mysql.init_app(app)
# now call mysql.get_db()

def json_response(response_dict, status_code):
  return make_response(jsonify(response_dict), status_code)

# Thanks to:
# http://ianhowson.com/a-quick-guide-to-using-mysql-in-python.html
def FetchOneAssoc(cursor) :
  data = cursor.fetchone()
  if data == None :
    return None
  desc = cursor.description

  dict = {}
  for (name, value) in zip(desc, data) :
    dict[name[0]] = value

  return dict

def other_player(p):
  # another case where an ORM object for Game would be cleaner
  if p == 1:
    return 2
  return 1

def init_db():
  """Initializes the database."""
  # MySQLdb has no easy way to run a script, so tell them to run the bash script
  print "Please run the create_db.sh script to create the database"

@app.cli.command('initdb')
def initdb_command():
  """Creates the database tables."""
  init_db()

@app.route("/")
def hello():
  return "Hello, World!"

@app.route("/api/game/create")
def create():
  """
  Create a new game with this user as the first player.
  Example response:
    {
      'success': 1,
      'game_id': 17,
      'player_id': 1
      'ships': [
        {'name': 'Destroyer', length: 2, x:2, y:3, orientation: "vertical"},
        {'name': 'Destroyer', length: 2, x:9, y:5, orientation: "vertical"},
        {'name': 'Submarine', length: 3, x:2, y:3, orientation: "horizontal"},
        {'name': 'Submarine', length: 3, x:2, y:3, orientation: "vertical"},
        {'name': 'Cruiser', length: 3, x:6, y:12, orientation: "horizontal"},
        {'name': 'Cruiser', length: 3, x:4, y:6, orientation: "vertical"},
        {'name': 'Battleship', length: 4, x:6, y:14, orientation: "vertical"},
        {'name': 'Carrier', length: 5, x:2, y:0, orientation: "horizontal"},
      ]
    }
  """
  if 'game_id' in session:
    error = "You are already in a game. You must disconnect first."
    return json_response({'success': 0, 'error': error}, 400)
  db = mysql.get_db()
  cur = db.cursor()
  ip = request.environ['REMOTE_ADDR']
  cur.execute("""INSERT INTO games (user1) VALUES (%s)""", [ip])
  db.commit()
  game_id = cur.lastrowid

  # set up session
  session['game_id'] = game_id
  session['player_id'] = 1
  # initialize the boards
  board1 = GameBoard()
  board2 = GameBoard()
  BoardSerializer(board1).store(game_id, 1)
  BoardSerializer(board2).store(game_id, 2)

  cur.execute("""UPDATE games SET ready=1 WHERE id=%s""", [game_id])
  db.commit()
  cur.close()
  response = {'success': 1, 'game_id': game_id, 'player_id': 1}
  response['ships'] = [ship.as_json() for ship in board1.ships]
  return json_response(response, 200)

@app.route("/api/game/list")
def list():
  """
  Return a list of all open games.
  Example response:
    {
      'success': 1,
      'games': [
        {'game_id': 2},
        {'game_id': 4},
        {'game_id': 5},
        {'game_id': 8},
      ]
    }
  """
  db = mysql.get_db()
  cur = db.cursor()
  ip = request.environ['REMOTE_ADDR']
  #cur.execute("""SELECT * FROM games WHERE (user1 IS NULL OR user2 IS NULL) AND
  #            user1 <> %s AND user2 <> %s AND ready=1""", [ip, ip])
  # list all for testing, since I'm always localhost. TODO uncomment above to
  # make sure users don't join games against themselves.
  cur.execute("""SELECT * FROM games WHERE (user1 IS NULL OR user2 IS NULL) AND
              ready=1""")
  rows = cur.fetchall()
  cur.close()
  response = {'success': 1}
  response['games'] = [{'game_id': r[0]} for r in rows]
  return json_response(response, 200)

@app.route("/api/game/join/<int:id>")
def join(id):
  """
  Join a game by id.
  Example response:
    {
      'game_id': 7,
      'success': 1,
      'player_id': 2,
      'ships': [
        {'name': 'Destroyer', length: 2, x:2, y:3, orientation: "vertical"},
        {'name': 'Destroyer', length: 2, x:9, y:5, orientation: "vertical"},
        {'name': 'Submarine', length: 3, x:2, y:3, orientation: "horizontal"},
        {'name': 'Submarine', length: 3, x:2, y:3, orientation: "vertical"},
        {'name': 'Cruiser', length: 3, x:6, y:12, orientation: "horizontal"},
        {'name': 'Cruiser', length: 3, x:4, y:6, orientation: "vertical"},
        {'name': 'Battleship', length: 4, x:6, y:14, orientation: "vertical"},
        {'name': 'Carrier', length: 5, x:2, y:0, orientation: "horizontal"},
      ]
    }
  "player_id" can be 1 or 2.
  """
  if 'game_id' in session:
    error = "You are already in a game. You must disconnect first."
    return json_response({'success': 0, 'error': error}, 400)

  db = mysql.get_db()
  cur = db.cursor()
  num_rows = cur.execute("""SELECT * FROM games WHERE id=%s AND (user1 IS NULL OR
              user2 IS NULL)""", [id])
  if num_rows == 0:
    error = "That game is no longer available."
    return json_response({'success': 0, 'error': error}, 410)

  row = FetchOneAssoc(cur)
  # prevent them from joining a game against themselves
  ip = request.environ['REMOTE_ADDR']
  if row['user1'] == ip or row['user2'] == ip:
    error = "You cannot join a game against yourself"
    print error
    #return json_response({'success': 0, 'error': error}, 400)
    # actually, why not let them e.g. open two browsers? it doesn't make sense
    # to do this by ip. it might make more sense by session key, but still may
    # be overkill.

  query = "UPDATE games SET "
  player_id = -1
  if row['user1'] is None:
    query += " user1=%s "
    player_id = 1
  elif row['user2'] is None:
    query += " user2=%s "
    player_id = 2
  query += " WHERE id=%s "
  ip = request.environ['REMOTE_ADDR']
  try:
    rows_affected = cur.execute(query, [ip, id])
  except MySQLdb.Error, e:
    db.rollback()
    print "Error %d: %s" % (e.args[0],e.args[1])
    error = "Unable to join that game"
    return json_response({'success': 0, 'error': error}, 500)

  db.commit()

  session['game_id'] = id
  session['player_id'] = player_id

  response = {'success': 1, 'game_id': id, 'player_id': player_id}
  board = BoardSerializer.load(id, player_id)
  response['ships'] = [ship.as_json() for ship in board.ships]
  return json_response(response, 200)

@app.route("/api/game/<int:id>/disconnect")
def disconnect(id):
  # mark game as ended
  # delete session vars
  # log "opponent disconnected" message
  # log "game ended" message
  return "Not Implemented"

@app.route("/api/game/<int:id>/clickHandler/<int:y>/<int:x>")
def clickHandler(id, y, x):
  """
  Takes a POST of y,x coords on enemy's board and tells whether it was a HIT or
  MISS. 

  This method should return quickly. It can also queue messages that the user can
  retrieve momentarily by hitting the "feed" endpoint.

  Example response:
    {
      'success': 1,
      'result': 'HIT'
    }
  """
  # TODO need to add a "lock" based on session so user can only do one request
  # at a time. "with Lock() as lock:". Flask might have this, can't find it.
  if not "game_id" in session or session["game_id"] != id:
    error = "You are not a member of this game."
    return json_response({'success': 0, 'error': error}, 401)

  db = mysql.get_db()
  cur = db.cursor()
  num_rows = cur.execute("""SELECT * FROM games WHERE id=%s""", [id])
  if num_rows == 0:
    error = "That game could not be found."
    return json_response({'success': 0, 'error': error}, 410)

  game = FetchOneAssoc(cur)

  if game['user1'] is None or game['user2'] is None:
    error = "Waiting for another player"
    return json_response({'success': 0, 'error': error}, 400)

  if game['ended'] == 1:
    error = "The game has ended"
    return json_response({'success': 0, 'error': error}, 200)

  if game['ready'] == 0:
    error = "Waiting on server..."
    return json_response({'success': 0, 'error': error}, 200)

  if game['current_player'] != session['player_id']:
    error = "It is not your turn."
    return json_response({'success': 0, 'error': error}, 401)

  board = BoardSerializer.load(id, other_player(session['player_id']))
  result = board.fire_shot(y, x)
  if result == "INVALID":
    error = "Invalid move"
    return json_response({'success': 0, 'error': error}, 400)

  BoardSerializer(board).store(id, other_player(session['player_id']))

  other = other_player(session['player_id'])
  if board.ship_sunk:
    print "You sunk", board.ship_sunk.name
    event = ShipSunkEvent(board.ship_sunk, other)
    add_to_feed(make_key(session['game_id'], other), event)
    add_to_feed(make_key(session['game_id'], session['player_id']), event)

  if board.is_game_over():
    query = "UPDATE games SET ended=1 WHERE id=%s"
    cur.execute(query, [id])
    add_to_feed(make_key(session['game_id'], other), \
                GameEndedEvent(session['player_id']))
    add_to_feed(make_key(session['game_id'], session['player_id']), \
                GameEndedEvent(session['player_id']))
    # push a message to queue
  else:
    query = "UPDATE games SET current_player=%s WHERE id=%s"
    cur.execute(query, [other, id])
    add_to_feed(make_key(session['game_id'], other), \
                TurnChangedEvent(other))
    add_to_feed(make_key(session['game_id'], session['player_id']), \
                TurnChangedEvent(other))
  db.commit()

  response = {}
  response['success'] = 1
  response['result'] = result
  return json_response(response, 200)

@app.route("/api/game/<int:id>/placeShip/<int:x>/<int:y>")
def placeShip(id, x, y):
  # return 401 if not authorized
  # return 400 if game has started
  return "Not Implemented"


class FeedEvent:
  def __init__(self, name="unknown event"):
    self.name = name

  def as_json(self):
    d = {'name': self.name}
    return d

class LogMessageEvent(FeedEvent):
  def __init__(self, message):
    FeedEvent.__init__(self, "LogMessage")
    self.message = message

  def as_json(self):
    d = FeedEvent.as_json(self)
    d['message'] = self.message
    return d

class GameEndedEvent(FeedEvent):
  def __init__(self, winner):
    FeedEvent.__init__(self, "GameEndedEvent")
    self.winner = winner

  def as_json(self):
    d = FeedEvent.as_json(self)
    d['winner'] = self.winner
    return d

class ShotFiredEvent(FeedEvent):
  def __init__(self, y, x, result):
    FeedEvent.__init__(self, "ShotFiredEvent")
    self.y = y
    self.x = x
    self.result = result

  def as_json(self):
    d = FeedEvent.as_json(self)
    d['y'] = self.y
    d['x'] = self.x
    d['result'] = self.result
    return d

class TurnChangedEvent(FeedEvent):
  def __init__(self, player_id):
    FeedEvent.__init__(self, "TurnChangedEvent")
    self.player_id = player_id

  def as_json(self):
    d = FeedEvent.as_json(self)
    d['player_id'] = self.player_id
    return d

class ShipSunkEvent(FeedEvent):
  def __init__(self, ship, player_id):
    FeedEvent.__init__(self, "ShipSunkEvent")
    self.ship = ship
    # player whose ship was sunk
    self.player_id = player_id

  def as_json(self):
    d = FeedEvent.as_json(self)
    d['player_id'] = player_id
    d['ship'] = self.ship.as_json()
    return d

def make_key(game_id, player_id):
  return "%s-%s" % (game_id, player_id)

def add_to_feed(key, event):
  pass

@app.route("/api/game/<int:id>/feed")
def feed(id):
  """
  Possible event types:
    ShotFiredEvent
    LogMessage
    SunkBattleship (Not Implemented)
    GameEnded
      Should include enemy's full board so location of ships can be revealed
    TurnChanged
  """
  # aggregate EventItem objects into one big json dump
  events = []
  response = {'events': events}
  return "Not Implemented"


if __name__ == '__main__':
  # used for sessions
  app.secret_key = '534mxcv90mafd/3r9asR?23TYa23Cva90aj8gf4309t'
  app.run(host='0.0.0.0')

