import random
try:
  import cPickle as pickle
except:
  import pickle

class BoardSerializer:
  def __init__(self, board):
    self.board = board

  @staticmethod
  def get_path(id, player_id):
    return "data/%s_%s.pickle" % (str(id), player_id)

  def store(self, id, player_id):
    path = self.get_path(id, player_id)
    with open(path, 'wb') as f:
      pickle.dump(self.board, f)

  @staticmethod
  def load(id, player_id):
    path = BoardSerializer.get_path(id, player_id)
    with open(path, 'rb') as f:
      board_data = pickle.load(f)
      return board_data

class Ship:
  ORIENTATION_VERTICAL=1
  ORIENTATION_HORIZONTAL=2
  def __init__(self, length, orientation, name="Ship"):
    self.length = length
    self.orientation = orientation
    self.name = name

class ShipList:
  def __init__(self):
    self.ships = []

  def add_ship(self, ship, y, x):
    self.ships.append((ship, y, x))

  def as_json(self):
    """
    This is in fact not JSON, but a list that is ready to be converted to JSON
    with jsonify().
    """
    result = []
    for ship, y, x in self.ships:
      d = {}
      d['name'] = ship.name
      d['length'] = ship.length
      if ship.orientation == Ship.ORIENTATION_VERTICAL:
        d['orientation'] = "vertical"
      else:
        d['orientation'] = "horizontal"
      d['y'] = y
      d['x'] = x
      result.append(d)
    return result

def place_ships_randomly(board):
  """
  Place ships randomly onto the board for the user
  """
  def random_orientation():
    r = random.randint(0,1)
    return (Ship.ORIENTATION_VERTICAL, Ship.ORIENTATION_HORIZONTAL)[r]

  ships = []
  ships.append(Ship(2, random_orientation(), "Destroyer"))
  ships.append(Ship(2, random_orientation(), "Destroyer"))
  ships.append(Ship(3, random_orientation(), "Submarine"))
  ships.append(Ship(3, random_orientation(), "Submarine"))
  ships.append(Ship(3, random_orientation(), "Cruiser"))
  ships.append(Ship(3, random_orientation(), "Cruiser"))
  ships.append(Ship(4, random_orientation(), "Battleship"))
  ships.append(Ship(5, random_orientation(), "Carrier"))
  while len(ships) > 0:
    ship = ships.pop()
    y, x = random.randint(0,board.ROWS-1), random.randint(0,board.COLS-1)
    while not board.place_ship(y, x, ship):
      y, x = random.randint(0,board.ROWS-1), random.randint(0,board.COLS-1)


class GameBoard(object):
  def __init__(self):
    self.ROWS=16
    self.COLS=16
    self.board = []
    self.init_board()
    self.ships = ShipList()
    # for now, we will place ships for the user
    place_ships_randomly(self)

  def init_board(self):
    """
    A board is stored as a list of strings. The key for objects on the grid is:
      * - Water
      o - Battleship
      X - Hit
      - - Miss
    """
    for i in xrange(self.ROWS):
      self.board.append(['*' for i in xrange(self.COLS)])

  def get_opponent_view(self):
    """
    Get the view of the board from opponent's view.
    """
    return None

  def place_ship(self, y, x, ship):
    """
    Place a ship onto the board.
    Returns True if successful, False otherwise
    """
    steps = []
    for i in xrange(ship.length):
      steps.append((y, x))
      if self.out_of_bounds(y, x) or self.board[y][x] != '*':
        return False
      if ship.orientation == Ship.ORIENTATION_VERTICAL:
        y += 1
      elif ship.orientation == Ship.ORIENTATION_HORIZONTAL:
        x += 1

    # now place the ship
    for y, x in steps:
      self.board[y][x] = 'o'
    self.ships.add_ship(ship, y, x)
    return True


  def all_ships_are_placed(self):
    pass

  def out_of_bounds(self, y, x):
    return y < 0 or y >= self.ROWS or x < 0 or x >= self.COLS

  def fire_shot(self, y, x):
    """
    Fire a shot onto this board. Returns HIT, MISS, or INVALID
    """
    if self.out_of_bounds(y, x):
      return "INVALID"

    if self.board[y][x] == 'X' or self.board[y][x] == '-':
      return "INVALID"

    if self.board[y][x] == '*':
      self.board[y][x] = '-'
      return "MISS"

    self.board[y][x] = 'X'
    return "HIT"

  def is_game_over(self):
    for row in self.board:
      if 'o' in row:
        return False
    return True

  def __str__(self):
    s = ""
    for row in self.board:
      s += "".join(row) + "\n"
    return s

