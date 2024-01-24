'''
Wiring:
    SSD1306
        Vcc -> 3.3V
        GND -> GND
        SCK -> Pin 22
        SDA -> Pin 21
    3 touch sensors
        Vcc -> 3.3V
        GND -> GND
        I/O -> Pins 18, 19, 23
'''

import machine
import random
from ssd1306 import SSD1306_I2C

paper_pin = machine.Pin(23, machine.Pin.IN)
rock_pin = machine.Pin(19, machine.Pin.IN)
scissors_pin = machine.Pin(18, machine.Pin.IN)

i2c = machine.I2C(sda=machine.Pin(21), scl=machine.Pin(22))
i2c.scan()
oled = SSD1306_I2C(128, 32, i2c)

'''
Enumeration for Actions
'''
PAPER = 0
ROCK = 1
SCISSORS = 2

class Environment:
    def __init__(self, player_init_action = PAPER,
                 agent_init_action = PAPER):
      """
        Defines environment for paper-scissors-rock game.
        Parameteres:
          player_init_action(Action): Initial action of a player
          agent_init_action(Action): Initial action of an agent
      """
      self.state = (player_init_action, agent_init_action)

      """
        Total score is sum of all scores in each game
      """
      self.total_score = 0

      """
        Represent how many times each action is hit.
      """
      self.player_action_counter = [0, 0, 0]
      self.opponent_action_counter = [0, 0, 0]

    @staticmethod
    def get_actions():
      """ Returns all available actions.
      """
      return (ROCK, PAPER, SCISSORS)

    def get_state(self):
      """ Returns current state of the game.
      """
      return self.state

    def update_state(self, player_action, opponent_action):
      """ For given current player and opponent action, we update old state with
      new data.

      """
      self.state = (player_action, opponent_action)

      # Za sada sluzi samo za statistiku
      self.player_action_counter[player_action] += 1
      self.opponent_action_counter[opponent_action] += 1
      return self.state


    def get_all_states(self) :
      """ Returns list of all available states.
      """
      states = []
      for a1 in env.get_actions():
        for a2 in env.get_actions():
          states.append((a1, a2))

      return states

    def get_random_state(self):
      """ Returns random valid state.
      """
      states = self.get_all_states()
      return random.choice(states)

    def check_winner(self, player_action, opponent_action) -> int:
      """ Method that checks winner for given actions of a player and opponent.

          Returns:
            int: The outcome of the game. If player wins return 1, if player lose return -1,
            and if draws return 0
      """
      if player_action == PAPER and opponent_action == ROCK:
          score = 1
      elif opponent_action == PAPER and player_action == ROCK:
          score = -1
      elif player_action == ROCK and opponent_action == SCISSORS:
          score = 1
      elif opponent_action == ROCK and player_action == SCISSORS:
          score = -1
      elif player_action == SCISSORS and opponent_action == PAPER:
          score = 1
      elif player_action == PAPER and opponent_action == SCISSORS:
          score = -1
      else:
          score = 0
      self.total_score += score
      return score, self.total_score

    def get_player_actions_counter(self) -> tuple[int, int, int]:
      """ Returns how many times player hit each action.
      """
      return self.player.action_counter

    def get_opponent_actions_counter(self) -> tuple[int, int, int]:
      """ Returns how many times opponent hit each action.
      """
      return self.opponent.action_counter

"""### Policies"""

def random_action():
    """ Return random action.
    """
    r = random.random()
    if r <= 1/3:
        return ROCK
    elif r <= 2/3:
        return PAPER
    else:
        return SCISSORS

def random_policy(s):
  """ For given state returns random action.
  """
  return random_action()

def policy_equivalent(q_dict, state):
  q_values = q_dict.get(state, None)
  max_value = max(q_values)

  for index in range(3):
    if q_values[index] == max_value:
      return index

"""### Helper functions"""

def zoom(self):
        '''
        Set OLED to display double size
        '''
        self.temp[0] = 0x00
        self.temp[1] = 0xD6
        self.i2c.writeto(self.addr, self.temp)
        self.temp[1] = 0x01
        self.i2c.writeto(self.addr, self.temp)


def find_counter_attack(a):
  """ Returns winning response if we play against action a.
  """
  if a == PAPER:
    return SCISSORS
  if a == ROCK:
    return PAPER
  if a == SCISSORS:
    return ROCK

def find_losing_attack(a):
  """ Returns losing response if we play against action a.
  """
  if a == PAPER:
    return ROCK
  if a == ROCK:
    return SCISSORS
  if a == SCISSORS:
    return PAPER

def print_action(a):
    if a == 0:
        return "Papir"
    elif a == 1:
        return "Kamen"
    else:
        return "Makaze"

def print_score(score: int):
    if score == 1:
        print("COVEK pobedio!")
        return "COVEK pobedio!"
    elif score == -1:
        print("KOMP pobedio!")
        return "KOMP pobedio!"
    elif score == 0:
        print("NERESENO")
        return "NERESENO"
    else:
       print("ERROR *-*")


"""### Q dictionary"""

def update_q_dict(q_dict,
                  s,
                  a,
                  score,
                  gamma: float = 1.0):

  """ Updating and forming new Q dictionary based on the current action, score and state
      Args:
        q_dict (QDict): Current dictionary of states and values
        s (State): Current state of the game
        a (Action): Action that agent made in state s
        score (int): Outcome of the game, 1 if agent wins, -1 if agent loses, 0 if draws
        gamma (float): Number from 0 to 1 that represents how much we forget previous knowledge
      Returns:
        q_dict (QDict): Updated dictionary
  """

  """ We convert tuples from dictionary to list because we can't modify tuples, and change their values.
  """
  action_values = list(q_dict[s])

  if score < 0:
    """ If agent loses, he finds action that would win in that case.
    """
    a_counter = find_losing_attack(a) # pre find_counter_attack
    action_values[a_counter] = gamma*(-score) + (1-gamma)*action_values[a_counter]

  if score > 0:
    """ If agent wins, he .
    """
    action_values[a] = gamma*score + (1-gamma)*action_values[a]

  if score == 0:
    """ If agent draws, the next time he's in state s, he will try to win instead of playing a draw again.".
    """
    action_values[a] = -gamma + (1-gamma)*action_values[a]  # decreasing the draw rate
    a_counter = find_counter_attack(a)
    action_values[a_counter] = gamma + (1-gamma)*action_values[a_counter] # increasing winning rate

  q_dict[s] = tuple(action_values)
  return q_dict

"""# Creating environment"""

env = Environment()

q_dict = {s:(random.random(), random.random(), random.random()) for s in env.get_all_states()}

"""# Playing 99 rounds"""

''' Starting screen '''
oled.fill(0)
oled.text('99', 0, 5)
oled.text('rundi', 0, 15)
oled.text('papir', 70, 0)
oled.text('kamen', 70, 10)
oled.text('makaze', 70, 20)
oled.show()

for num_games in range(100):

    # player_move = "SCISSORS" # @param ["ROCK", "PAPER", "SCISSORS"]
    gamma = 0.95 # @param {type:"slider", min:0, max:1, step:0.05}
    
    # If player touches all the buttons, game ends
    if paper_pin.value() == 1 and rock_pin.value() == 1 and scissors_pin.value() == 1:
        break
    
    # Waiting for player input
    player_action = -1
    while player_action<0:
        if paper_pin.value() == 1:
            player_action = PAPER
        elif rock_pin.value() == 1:
            player_action = ROCK
        elif scissors_pin.value() == 1:
            player_action = SCISSORS
    
    state = env.get_state()
    #greedy_policy = create_greedy_policy(q_dict)
    #opponent_action = greedy_policy(state)

    opponent_action = policy_equivalent(q_dict, state)

    #print(f"Player plays {player_action}, agent plays {opponent_action}")
    print(f"Computer play {opponent_action}")

    score,total = env.check_winner(player_action, opponent_action)
    q_dict=update_q_dict(q_dict, state, opponent_action, -score, gamma=gamma)

    new_state = env.update_state(player_action, opponent_action)

    print_score(score)
    # print(f"Total score : {total}")

    # print(f"Player next move: {find_losing_attack(greedy_policy(new_state))}")

    oled.fill(0)
    oled.text(print_action(player_action)+ ' - ' + print_action(opponent_action), 0, 0)
    oled.text(print_score(score), 0, 10)
    oled.text('runda ' + str(num_games) + '.', 0, 25)
    oled.text('rez ' + str(total), 70, 25)
    oled.show()
    
    machine.sleep(350)

    ''' 3s timer showing on line 3 of display '''
    '''
    oled.text("3", 0, 20)
    oled.show()
    machine.sleep(1000);
    oled.text("2", 20, 20)
    oled.show()
    machine.sleep(1000);
    oled.text("1", 40, 20)
    oled.show()
    machine.sleep(1000);'''

''' Ending screen '''
oled.fill(0)
oled.text('Br. rundi:', 0, 0)
oled.text(str(num_games), 90, 0)
oled.text('Rezultat :', 0, 10)
oled.text(str(total), 90, 10)
if total >= 0:
    oled.text('dobar :)', 0, 20)
else:
    oled.text('los :)', 0, 20)
    
oled.show()
