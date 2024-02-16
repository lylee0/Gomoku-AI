import random
import pisqpipe as pp
from pisqpipe import DEBUG_EVAL, DEBUG
from math import log
from copy import deepcopy
pp.infotext = 'name="pbrain-pyrandom", author="Jan Stransky", version="1.0", country="Czech Republic", www="https://github.com/stranskyjan/pbrain-pyrandom"'

MAX_BOARD = 100
board = [[0 for i in range(MAX_BOARD)] for j in range(MAX_BOARD)]
sim = 500

def brain_init():
	if pp.width < 5 or pp.height < 5:
		pp.pipeOut("ERROR size of the board")
		return
	if pp.width > MAX_BOARD or pp.height > MAX_BOARD:
		pp.pipeOut("ERROR Maximal board size is {}".format(MAX_BOARD))
		return
	pp.pipeOut("OK")

def brain_restart():
	for x in range(pp.width):
		for y in range(pp.height):
			board[x][y] = 0
	pp.pipeOut("OK")

def isFree(x, y):
	return x >= 0 and y >= 0 and x < pp.width and y < pp.height and board[x][y] == 0

def brain_my(x, y):
	if isFree(x,y):
		board[x][y] = 1
	else:
		pp.pipeOut("ERROR my move [{},{}]".format(x, y))

def brain_opponents(x, y):
	if isFree(x,y):
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
	def __init__(self, temp_board, player, parent, parent_action, untried_actions, margin):
		self.board = temp_board
		self.player = player
		self.parent = parent
		self.parent_action = parent_action
		self.children = []
		self.untried_actions = untried_actions
		self.margin = margin
		self.num_visits = 0
		self.result = {1: 0, 2: 0, -1: 0, 0: 0}

def hmcts(root):
	for i in range(0, sim):
		leaf = traverse(root)
		sim_result = rollout(leaf)
		backpropagate(leaf, sim_result)
	return best_child(root)

def update_margin(action, margin):
	x, y = action
	x_start, x_end, y_start, y_end = margin
	if x-1 < x_start:
		if x-1 < 0:
			x_start = 0
		else:
			x_start = x-1
	elif x+1 > x_end:
		if x+1 > pp.height:
			x_end = pp.height
		else:
			x_end = x+1
	if y-1 < y_start:
		if y-1 < 0:
			y_start = 0
		else:
			y_start = y-1
	elif y+1 > y_end:
		if y+1 > pp.width:
			y_end = pp.width
		else:
			y_end = y+1
	return (x_start, x_end, y_start, y_end)

def expansion(node):
	action = random.choice(node.untried_actions)
	node.untried_actions.remove(action)
	current_player = node.player
	if current_player == 1:
		player = 2
	else:
		player = 1
	next_board = play(node.board, action, node.player)
	#margin = find_margin(occupied_cell(next_board))
	margin = update_margin(action, node.margin)
	child_node = Node(next_board, player, node, action, node.untried_actions, margin) 
	node.children.append(child_node)
	return child_node

def traverse(node):
	'''node traversal'''
	while game_result(node.board, node.parent_action, node.untried_actions) == 0:
		if len(node.untried_actions) == 0:
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
	margin = node.margin
	while game_result(temp_board, action, possible_moves) == 0:
		action = rollout_policy(possible_moves)
		temp_board = play(temp_board, action, player)
		margin = update_margin(action, margin)
		possible_moves = empty(temp_board, margin)
		if player == 1:
			player = 2
		else:
			player = 1
	return game_result(temp_board, action, possible_moves)

def rollout_policy(possible_moves):
	'''randomly selecting a child node'''
	return possible_moves[random.randint(0, len(possible_moves)-1)]

def backpropagate(node, result):
	'''backpropagation'''
	node.num_visits += 1
	node.result[result] += 1
	if node.parent != None:
		backpropagate(node.parent, result)
	return

def best_child(node):
	'''selecting the best child'''
	weight = uct(node)
	temp_weight = weight[0]
	best = node.children[0]
	if node.player == 1:
		for i in range(0, len(node.children)):
			if weight[i] >= temp_weight:
				best = node.children[i]
				temp_weight = weight[i]  
	else:
		for i in range(0, len(node.children)):
			if weight[i] <= temp_weight:
				best = node.children[i]
				temp_weight = weight[i]
	return best

def empty(temp_board, margin):
	x_start, x_end, y_start, y_end = margin
	possible_moves = []
	for i in range(x_start, x_end):
		for j in range(y_start, y_end):
			if temp_board[i][j] == 0:
				possible_moves.append((i, j))
	return possible_moves

'''def occupied_cell(temp_board):
	occupied = []
	for i in range(0, pp.height):
		for j in range(0, pp.width):
			if temp_board !=0 :
				occupied.append((i, j))
	return occupied'''

def count(player, pos, temp_board):
	count = 0
	for x, y in pos:
		if (not 0<=x<pp.height) or (not 0<=y<pp.width):
			break
		if temp_board[x][y] == player:
			count +=1
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
	return random.choice(node.children)

def play(temp_board, action, player):
	copy_board = deepcopy(temp_board)
	x, y = action
	copy_board[x][y] = player
	return copy_board

def uct(node, c=1.4):
	weight = []
	for child in node.children:
		player = child.player
		if player == 1:
			child_win = child.result[1] - child.result[2]
		else:
			child_win = child.result[2] - child.result[1]
		child_sim = child.num_visits
		temp_weight = (child_win/child_sim) + c*((log(sim)/child_sim)**(1/2))
		weight.append(temp_weight)
	return weight

def get_move(root):
	action = hmcts(root)
	return action

def find_margin(occupied):
	x_start = pp.height
	x_end = 0
	y_start = pp.width
	y_end = 0
	for x, y in occupied:
		x_start = min(x_start, x)
		x_end = max(x_end, x)
		y_start = min(y_start, y)
		y_end = max(y_end, y)
	x_start -= 1
	x_end += 1
	y_start -= 1
	y_end += 1
	if x_start < 0:
		x_start = 0
	if x_end > pp.height:
		x_end = pp.height
	if y_start < 0:
		y_start = 0
	if y_end > pp.width:
		y_end = pp.width
	return (x_start, x_end, y_start, y_end)

def check_situation(temp_board, player):
	'''compare the score'''
	score_board, untried_actions, occupied = all_score(temp_board, player)
	highest = 0
	action = None
	for i in range(0, pp.height):
		for j in range(0, pp.width):
			if score_board[i][j] >= highest and score_board[i][j] != 0:
				action = (i, j)
				highest = score_board[i][j]
	if len(untried_actions) == pp.height * pp.width:
		action = (10, 10)
		occupied.append((10, 10))
	return action, untried_actions, find_margin(occupied)

def all_score(temp_board, player):
	'''find all the score'''
	score_board = [[0 for i in range(0, pp.height)] for j in range(0, pp.width)]
	untried_actions = []
	occupied = []
	for i in range(0, pp.height):
		for j in range(0, pp.height):
			if temp_board[i][j] == 0:
				score_board[i][j] = change_score(temp_board, (i, j), player)
				untried_actions.append((i, j))
			else:
				occupied.append((i, j))
	return score_board, untried_actions, occupied

def count_board(temp_board, pos, player):
	'''count the board'''
	count = 0
	opp_count = 0
	end = 0
	opp_end = 0
	a, b = pos[0]
	opponent = 1 if player ==2 else 2
	if 0<=a<pp.height and 0<=b<pp.width and temp_board[a][b] == player: #Attack
		for i, j in pos:
			if 0<=i<pp.height and 0<=j<pp.width:
				if temp_board[i][j] == player:
					count += 1
				else:
					end = temp_board[i][j]
					break
			else:
				end = 3
				break
	elif 0<=a<pp.height and 0<=b<pp.width and temp_board[a][b] == opponent: #count opponent
		for i, j in pos:
			if 0<=i<pp.height and 0<=j<pp.width:
				if temp_board[i][j] == opponent:
					opp_count += 1
				else:
					opp_end = temp_board[i][j]
					break
			else:
				opp_end = 3
				break
	elif 0<=a<pp.height and 0<=b<pp.width and temp_board[a][b] == 0:
		end = 0 #活棋
	else:
		end = 3 #meet wall
	
	return (count, opp_count, end, opp_end)

def situation(count, opp_count, end_1, end_2, opp_end_1, opp_end_2):
	'''determine the score according to the situation'''
	score  = 0
	#Attack
	if count == 5: #win
		score += 100000
	elif end_1 != 0 and end_2 != 0: #impossible to get 5
		score += 0
	elif count == 4 and end_1 == 0 and end_2 == 0: #活四
		score += 10000
	elif count == 4: #死四
		score += 999
	elif count == 3 and end_1 == 0 and end_2 == 0:
		score += 1000
	
	#defense
	if opp_count == 4:
		score += 90000
	elif opp_end_1 != 0 and opp_end_2 != 0:
		score +=0
	elif opp_count == 3 and opp_end_1 == 0 and opp_end_2 == 0:
		score += 80000

	return score

def change_score(temp_board, a, player):
	'''sum up the score'''
	x, y = a
	sum = 0
	pos = [[(x-1, y), (x-2, y), (x-3, y), (x-4, y)],
			[(x+1, y), (x+2, y), (x+3, y), (x+4, y)],
			[(x, y-1), (x, y-2), (x, y-3), (x, y-4)],
			[(x, y+1), (x, y+2), (x, y+3), (x, y+4)],
			[(x-1, y-1), (x-2, y-2), (x-3, y-3), (x-4, y-4)],
			[(x+1, y+1), (x+2, y+2), (x+3, y+3), (x+4, y+4)],
			[(x-1, y+1), (x-2, y+2), (x-3, y+3), (x-4, y+4)],
			[(x+1, y-1), (x+2, y-2), (x+3, y-3), (x+4, y-4)]]
	for i in range(0, 8, 2):
		temp_pos_0 = pos[i]
		temp_pos_1 = pos[i+1]
		count_1, opp_count_1, end_1, opp_end_1 = count_board(temp_board, temp_pos_0, player)
		count_2, opp_count_2, end_2, opp_end_2 = count_board(temp_board, temp_pos_1, player)
		sum += situation(count_1+count_2+1, opp_count_1+opp_count_2, end_1, end_2, opp_end_1, opp_end_2)
	
	return sum

def brain_turn():
	'''if pp.terminateAI:
		return
	i = 0
	while True:
		x = random.randint(0, pp.width)
		y = random.randint(0, pp.height)
		i += 1
		if pp.terminateAI:
			return
		if isFree(x,y):
			break
	if i > 1:
		pp.pipeOut("DEBUG {} coordinates didn't hit an empty field".format(i))
	pp.do_mymove(x, y)'''
	action, untried_actions, margin = check_situation(board, 1)
	if action != None:
		x, y = action
		pp.do_mymove(x, y)
	else:
		root = Node(board, 1, None, None, empty(board, margin), margin)
		best = get_move(root)
		x, y = best.parent_action
		pp.do_mymove(x, y)

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
"""
# define a file for logging ...
DEBUG_LOGFILE = "C:/Users/lly/Desktop/Fudan/Sem 1/人工智能/Project/Final/Phase 3(Reinforce Learning)/testing/pbrain-pyrandom.log"
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
"""
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
