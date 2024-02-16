import random
import pisqpipe as pp
from pisqpipe import DEBUG_EVAL, DEBUG
from copy import deepcopy
from math import log

pp.infotext = 'name="pbrain-pyrandom", author="Jan Stransky", version="1.0", country="Czech Republic", www="https://github.com/stranskyjan/pbrain-pyrandom"'

MAX_BOARD = 100
board = [[0 for i in range(MAX_BOARD)] for j in range(MAX_BOARD)]
sim = 50000 
picked = []

def brain_init():
	if pp.width < 5 or pp.height < 5:
		pp.pipeOut("ERROR size of the board")
		return
	if pp.width > MAX_BOARD or pp.height > MAX_BOARD:
		pp.pipeOut("ERROR Maximal board size is {}".format(MAX_BOARD))
		return
	pp.pipeOut("OK")

def brain_restart():
	global picked
	picked = []
	for x in range(pp.width):
		for y in range(pp.height):
			board[x][y] = 0
	pp.pipeOut("OK")

def isFree(x, y):
	return x >= 0 and y >= 0 and x < pp.width and y < pp.height and board[x][y] == 0

def brain_my(x, y):
	if isFree(x,y):
		board[x][y] = 1
		picked.append((x, y))
		#untried.remove((x, y))
	else:
		pp.pipeOut("ERROR my move [{},{}]".format(x, y))

def brain_opponents(x, y):
	if isFree(x,y):
		picked.append((x, y))
		#if (x, y) in untried:
			#untried.remove((x, y))
		board[x][y] = 2
	else:
		pp.pipeOut("ERROR opponents's move [{},{}]".format(x, y))

def brain_block(x, y):
	if isFree(x,y):
		board[x][y] = 3
	else:
		pp.pipeOut("ERROR winning move [{},{}]".format(x, y))

def brain_takeback(x, y):
	if x >= 0 and y >= 0 and x < pp.width and y < pp.height and board[x][y] != 0:
		board[x][y] = 0
		return 0
	return 2

class Node:
	def __init__(self, temp_board, player, parent, parent_action, untried_actions):
		self.board = temp_board
		self.player = player
		self.parent = parent
		self.parent_action = parent_action
		self.children = []
		self.untried_actions = untried_actions
		self.num_visits = 0
		self.result = {1: 0, 2: 0, -1: 0, 0: 0}  

def MCTS(root):
	'''Monte Carlo Tree Search'''
	#logDebug("MCTS")
	for i in range(0, sim):
		leaf = traverse(root)
		sim_result = rollout(leaf)
		backpropagate(leaf, sim_result)

	return best_child(root)

def expansion(node):	
	action = random.choice(node.untried_actions)
	node.untried_actions.remove(action)  
	current_player = node.player
	if current_player == 1:
		player = 2
	else:
		player = 1
	next_board = play(node.board, action, node.player)
	#untried_actions = deepcopy(node.untried_actions)
	#untried_actions.extend(update_eight_moves(next_board, action))
	if node.parent == True:
		parent = node.parent
		untried_actions = update_eight_moves(next_board, parent.parent_action)
	else:
		untried_actions = update_eight_moves(next_board, action)
	child_node = Node(next_board, player, node, action, untried_actions)  
	node.children.append(child_node)
	#logDebug("expansion")
	return child_node

def traverse(node):
	'''node traversal'''
	while game_result(node.board, node.parent_action, node.untried_actions) == 0:
		if len(node.untried_actions) == 0:
			#node = best_child(node)
			node = pick_random(node)
		else:
			return expansion(node)
	return node		

def rollout(node):
	'''result of simulation'''
	player = node.player
	temp_board = node.board
	possible_moves = node.untried_actions
	action = node.parent_action
	action_list = [action]
	while game_result(temp_board, action, possible_moves) == 0:
		#logDebug("rollout")
		action = rollout_policy(possible_moves)
		action_list.append(action)
		#possible_moves.remove(action)
		temp_board = play(temp_board, action, player)
		possible_moves = update_eight_moves(temp_board, action_list[len(action_list)-2])
		if player == 1:
			player = 2
		else:
			player = 1
	#logDebug("end loop in rollout")
	return game_result(temp_board, action, possible_moves)

def rollout_policy(possible_moves): 
	'''randomly selecting a child node'''
	return possible_moves[random.randint(0, len(possible_moves)-1)]

def backpropagate(node, result):
	'''back propagation'''
	node.num_visits += 1
	node.result[result] += 1
	if node.parent:
		backpropagate(node.parent, result)
	return

def best_child(node):
	'''selecting the best child'''
	#pick child with highest number of visits
	weight = uct(node)
	temp_weight = weight[0]
	best = node.children[0]
	if node.player == 1: 
		for i in range(0, len(node.children)):
			if weight[i] >= temp_weight:
				best = node.children[i]
	else:
		for i in range(0, len(node.children)):
			if weight[i] <= temp_weight:
				best = node.children[i]
	return best

def uct(node, c=1.4):
	#num_sim = node.num_visits
	weight = []
	for child in node.children:
		#logDebug("uct")
		player = child.player
		if player == 1:
			child_win = child.result[1] - child.result[2]
		else:
			child_win = child.result[2] - child.result[1]
		#child_win = child.result[player]
		child_sim = child.num_visits
		temp_weight = (child_win/child_sim) + c*((log(sim)/child_sim)**(1/2))
		weight.append(temp_weight)
	return weight

def count(player, pos, temp_board):
	count = 0
	for x, y in pos:
		if (not 0<=x<pp.width) or (not 0<=y<pp.height):
			break
		if temp_board[x][y] == player:
			count += 1
		else:
			break
	return count

def game_result(temp_board, action, possible_moves):
	if action == None:
		return 0

	i, j = action
	player = temp_board[i][j]
	positions = [
	[(i-1, j), (i-2, j), (i-3, j), (i-4, j)],
	[(i+1, j), (i+2, j), (i+3, j), (i+4, j)],
	[(i, j-1), (i, j-2), (i, j-3), (i, j-4)],
	[(i, j+1), (i, j+2), (i, j+3), (i, j+4)],
	[(i-1, j-1), (i-2, j-2), (i-3, j-3), (i-4, j-4)],
	[(i+1, j+1), (i+2, j+2), (i+3, j+3), (i+4, j+4)],
	[(i-1, j+1), (i-2, j+2), (i-3, j+3), (i-4, j+4)],
	[(i+1, j-1), (i+2, j-2), (i+3, j-3), (i+4, j-4)]
	]
	
	temp = 0
	for z in range(0, 8):
		temp = count(player, positions[z], temp_board)
		if temp == 4:
			return player

	#not yet end
	for i, j in possible_moves:
		if temp_board[i][j] == 0:
			return 0

	#tie
	return -1

def pick_random(node):
	#random
	return random.choice(node.children)

def update_eight_moves(temp_board, action):
	x, y = action
	new_moves = []
	if (0<=(x-1)<pp.width) and (temp_board[x-1][y] == 0):
		new_moves.append((x-1, y))
	if (0<=(x+1)<pp.width) and (temp_board[x+1][y] == 0):
		new_moves.append((x+1, y))
	if (0<=(y-1)<pp.width) and (temp_board[x][y-1] == 0):
		new_moves.append((x, y-1))
	if (0<=(y+1)<pp.width) and (temp_board[x][y+1] == 0):
		new_moves.append((x, y+1))
	if (0<=(x-1)<pp.width) and (0<=(y-1)<pp.width) and (temp_board[x-1][y-1] == 0):
		new_moves.append((x-1, y-1))
	if (0<=(x+1)<pp.width) and (0<=(y+1)<pp.width) and (temp_board[x+1][y+1] == 0):
		new_moves.append((x+1, y+1))
	if (0<=(x-1)<pp.width) and (0<=(y+1)<pp.width) and (temp_board[x-1][y+1] == 0):
		new_moves.append((x-1, y+1))
	if (0<=(x+1)<pp.width) and (0<=(y-1)<pp.width) and (temp_board[x+1][y-1] == 0):
		new_moves.append((x+1, y-1))
	return new_moves

def play(temp_board, action, player):
	copy_board = deepcopy(temp_board)
	x, y = action
	copy_board[x][y] = player
	return copy_board  

def brain_turn():
	#try:
	if pp.terminateAI:
		return
	untried_actions = []
	if(picked == []):
		untried_actions.append((10, 10))
	elif(len(picked) == 1):
		untried_actions = update_eight_moves(board, picked[0])
	else:
		untried_actions = update_eight_moves(board, picked[len(picked)-2])
	#untried_actions = get_eight_moves(board, picked)
	root = Node(board, 1, None, None, untried_actions)
	best = MCTS(root)
	x, y = best.parent_action
	if pp.terminateAI:
		return
	pp.do_mymove(x, y)
	#except:
		#logTraceBack()

def brain_end():
	pass

def brain_about():
	pp.pipeOut(pp.infotext)

if DEBUG_EVAL:
	import win32gui
	def brain_eval(x, y):
		# TODO check if it works as expected
		wnd = win32gui.GetForegroundWindow()
		dc = win32gui.GetDC(wnd)
		rc = win32gui.GetClientRect(wnd)
		c = str(board[x][y])
		win32gui.ExtTextOut(dc, rc[2]-15, 3, 0, None, c, ())
		win32gui.ReleaseDC(wnd, dc)

######################################################################
# A possible way how to debug brains.
# To test it, just "uncomment" it (delete enclosing """)
######################################################################
'''
# define a file for logging ...
DEBUG_LOGFILE = "C:/Users/lly/Desktop/Fudan/Sem 1/人工智能/Project/Final/Phase 2(MCTS)/testing/pbrain-pyrandom.log"
#DEBUG_LOGFILE = "/tmp/pbrain-pyrandom.log"
# ...and clear it initially
with open(DEBUG_LOGFILE,"w") as f:
	pass

# define a function for writing messages to the file
def logDebug(msg):
	with open(DEBUG_LOGFILE,"a") as f:
		f.write(msg+"\n")
		f.flush()

# define a function to get exception traceback
def logTraceBack():
	import traceback
	with open(DEBUG_LOGFILE,"a") as f:
		traceback.print_exc(file=f)
		f.flush()
	raise

# use logDebug wherever
# use try-except (with logTraceBack in except branch) to get exception info
# an example of problematic function
def brain_turn():
	logDebug("some message 1")
	try:
		logDebug("some message 2")
		1. / 0. # some code raising an exception
		logDebug("some message 3") # not logged, as it is after error
	except:
		logTraceBack()
'''
######################################################################

# "overwrites" functions in pisqpipe module
pp.brain_init = brain_init
pp.brain_restart = brain_restart
pp.brain_my = brain_my
pp.brain_opponents = brain_opponents
pp.brain_block = brain_block
pp.brain_takeback = brain_takeback
pp.brain_turn = brain_turn
pp.brain_end = brain_end
pp.brain_about = brain_about
if DEBUG_EVAL:
	pp.brain_eval = brain_eval

def main():
	pp.main()

if __name__ == "__main__":
	main()
