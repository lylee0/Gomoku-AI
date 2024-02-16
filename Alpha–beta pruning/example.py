import random
import pisqpipe as pp
from pisqpipe import DEBUG_EVAL, DEBUG
from copy import deepcopy

max_depth = 2

pp.infotext = 'name="pbrain-pyrandom", author="Jan Stransky", version="1.0", country="Czech Republic", www="https://github.com/stranskyjan/pbrain-pyrandom"'

MAX_BOARD = 100
board = [[0 for i in range(MAX_BOARD)] for j in range(MAX_BOARD)]
#score = [[0 for i in range(MAX_BOARD)] for j in range(MAX_BOARD)]

def brain_init(): #Create board
	if pp.width < 5 or pp.height < 5:
		pp.pipeOut("ERROR size of the board")
		return
	if pp.width > MAX_BOARD or pp.height > MAX_BOARD:
		pp.pipeOut("ERROR Maximal board size is {}".format(MAX_BOARD))
		return
	pp.pipeOut("OK")

def brain_restart(): #delete old board, create new board
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

def utility(temp_board, a, color):
	#opponent_color = 1 if color == 0 else 0
	score = change_score(temp_board, a, color)
	return score
	'''if color == 2:
		return -score
	else:
		return score'''

def count(temp_board, pos, color):
	count = 0
	opp_count = 0
	end = 0
	opp_end = 0
	a, b = pos[0]
	opponent_color = 1 if color == 2 else 2
	if 0 <= a < pp.height and 0 <= b < pp.width and temp_board[a][b] == color: #Attack
		for i, j in pos:
			if 0 <= i < pp.height and 0 <= j < pp.width:
				if temp_board[i][j] == color:
						count += 1
				else:
					end = temp_board[i][j]
					break
			else:
				end = 3
				break
	elif 0 <= a < pp.height and 0 <= b < pp.width and temp_board[a][b] == opponent_color:  #count opponent
		for i, j in pos:
			if 0 <= i < pp.height and 0 <= j < pp.width:
				if temp_board[i][j] == opponent_color:
					opp_count += 1
				else:
					opp_end = temp_board[i][j]
					break
			else:
				opp_end = 3
				break
	elif 0 <= a < pp.height and 0 <= b < pp.width and temp_board[a][b] == 0:
		end = 0  #活棋
	else:
		end = 3 #meet wall

	return (count, opp_count, end, opp_end)

def situation(count, opp_count, end_1, end_2, opp_end_1, opp_end_2):
	score = 0
	#Attack
	if count == 5: #win
		score += 100000
	elif end_1 != 0 and end_2 != 0:  #impossible to get 5
		score += 0
	elif count == 4 and end_1 == 0 and end_2 == 0: #活四
		score += 10000
	elif count == 4:  #死四
		score += 1000
	elif count == 3 and end_1 == 0 and end_2 == 0:  #活三
		score += 1000
	elif count == 3: #死三
		score += 100
	elif count == 2 and end_1 == 0 and end_2 == 0:  #活二
		score += 100
	elif count == 2:  #死二
		score += 10
	elif count == 1 and end_1 == 0 and end_2 == 0: #活一
		score += 10
	elif count == 1:  #死一
		score += 2

	#防
	if opp_count == 4:
		score += 90000 
	elif opp_end_1 != 0 and opp_end_2 != 0:
		score += 0
	elif opp_count == 3 and opp_end_1 == 0 and opp_end_2 == 0:
		score += 80000  #10000
	elif opp_count == 3:
		score += 10
	elif opp_count == 2 and opp_end_1 == 0 and opp_end_2 == 0:
		score += 5
	elif opp_count == 2: 
		score += 1
	elif opp_count == 1 and opp_end_1 == 0 and opp_end_2 == 0:
		score += 1
	elif opp_count == 1:
		score += 1

	return score

def change_score(temp_board, a, color):
	x, y = a
	sum = 0

	pos = [ [(x-1, y), (x-2, y), (x-3, y), (x-4, y)],
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
		count_1, opp_count_1, end_1, opp_end_1 = count(temp_board, temp_pos_0, color)
		count_2, opp_count_2, end_2, opp_end_2 = count(temp_board, temp_pos_1, color)
		sum += situation(count_1+count_2+1, opp_count_1+opp_count_2, end_1, end_2, opp_end_1, opp_end_2)

	score = [
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
	[0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
	[0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	]

	sum += score[x][y]

	return sum

def terminal_test(depth):
	if depth == max_depth-1:
		return True
	else:
		return False

def max_value(temp_board, a, alpha, beta, depth, color):
	if terminal_test(depth):
		return utility(temp_board, a, color), a

	v = float("-inf")
	opponent_color = 1 if color == 2 else 1
	for i in range(0, pp.height):
		for j in range(0, pp.width):
			if isFree(i, j):
				a = (i, j)
				copy_board = deepcopy(temp_board)
				copy_board[i][j] = color
				move_v, move_action = min_value(copy_board, a, alpha, beta, depth+1, opponent_color)
				if move_v > v:
					v = move_v
					action = a
				if v >= beta:
					return v, action
				alpha = max(alpha, v)

	return v, action

def min_value(temp_board, a, alpha, beta, depth, color):
	if terminal_test(depth):
		return utility(temp_board, a, color), a
	v = float("inf")

	opponent_color = 1 if color == 2 else 1
	for i in range(0, pp.height):
		for j in range(0, pp.width):
			if isFree(i, j):
				a = (i, j)
				copy_board = deepcopy(temp_board)
				copy_board[i][j] = opponent_color
				move_v, move_action = max_value(copy_board, a, alpha, beta, depth+1, opponent_color)
				if move_v < v:
					v = move_v
					action = a
				if v <= alpha:
					return v, action
				beta = min(beta, v)

	return v, action

def alpha_beta_search(temp_board):
	depth = 0
	a = (10, 10)
	v, action = max_value(temp_board, a, float("-inf"), float("inf"), depth, 1)
	return action, v

def get_move(temp_board):
	action,_ = alpha_beta_search(temp_board)
	return action

def bestmove(board):
	score = 0
	action = (0, 0)
	for i in range(0, pp.height):
		for j in range(0, pp.width):
			if isFree(i, j):
				a = (i, j)
				temp_score = change_score(board, a, 1)
				if temp_score >= score:
					score = temp_score
					action = a
	return action

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

	if pp.terminateAI:
		return
	action = get_move(board)	
	#action = bestmove(board)
	x, y = action
	if pp.terminateAI:
		return
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

# define a file for logging ...
#DEBUG_LOGFILE = "/tmp/pbrain-pyrandom.log"
'''DEBUG_LOGFILE = "C:/Users/lly/Desktop/Fudan/Sem 1/人工智能/Project/Final/testing/pbrain-pyrandom.log"
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
		logTraceBack()'''

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
