import random
import os
import readchar as rc
import _thread as thread
from readchar.key import *
from colorama import *
from time import sleep
from os.path import isfile,isdir

#######################################################
#SETTINGS
#######################################################

NORMAL 			= "\033[96;100m"
LIGHTNORMAL		= "\033[97;46m"
CURSOR 			= "\033[30;107m"
BORDER			= "\033[97;40m"
STACK			= "\033[30;47m"
CONSOLE			= "\033[37;40m"
MENU			= "\033[30;106m"
MENUSELECTED	= "\033[96;40m"

consoleWidth 		= 40
consoleHeight		= 6
stckMax  			= 10
stckWidth 			= 7
maxPlayfieldWidth 	= 80
maxPlayfieldHeight 	= 40

runDelay = 0.1

#######################################################
#GLOBALS
#######################################################

pfOffx = 4
pfOffy = 4

playfieldWidth , playfieldHeight = 30 , 15

stckOffx = pfOffx + playfieldWidth  + 5
stckOffy = pfOffy + stckMax - 1

cnslOffx = pfOffx
cnslOffy = pfOffy + playfieldHeight + 3

consoleX, consoleY = 0, 0
console = []
stack = []
playfield = []

fieldCursor = [0,0]
programPntr = [0,0]
selectionCursor = [0,0]
programDir = [1,0]

currentFile = "new.bf"

programRunning = True
running = False
stringMode = False
selecting = False

copyBuffer = []
	
def recalculateOffsets():		
	global stckOffx
	global stckOffy
	global cnslOffx
	global cnslOffy

	stckOffx = pfOffx + playfieldWidth  + 5
	stckOffy = pfOffy + stckMax - 1		

	cnslOffx = pfOffx
	cnslOffy = pfOffy + playfieldHeight + 3
	
	if stckOffy > pfOffy + playfieldHeight:
		cnslOffy = stckOffy + 3

#######################################################
#DRAWING
#######################################################

def moveCursor(cursor,x,y):
	oldX = cursor[0]
	oldY = cursor[1]
	cursor[0] += x
	cursor[1] += y
	wrap(cursor)
	
	oldChar = getColor(oldX,oldY) + getAt(oldX,oldY)
	printAt(oldX + pfOffx, oldY + pfOffy,oldChar)
	
	newChar = CURSOR + getAt(cursor[0],cursor[1])
	printAt(cursor[0]+pfOffx,cursor[1]+pfOffy,newChar)
		
	resetCursor()
	
def moveCursorAbs(cursor,x,y):
	dx = x - cursor[0]
	dy = y - cursor[1]
	moveCursor(cursor,dx,dy)		

def eraseCursor(cursor):
	printAt(pfOffx + cursor[0], pfOffy + cursor[1], getColor(cursor[0],cursor[1]) +  getAt(cursor[0],cursor[1]))
	resetCursor()
	
def printAt(x,y,ch):
	print('\033[' + str(y+1) + ';' +str(x+1)+'H' + ch)	

def resetCursor():
	print('\033[1;1H',end = '')
	
def getColor(x,y):
	
	if x % 2 and y % 2 or not(x % 2 or y % 2):
		return NORMAL
		
	return LIGHTNORMAL	
	
def drawConsole():
	print(BORDER)
	drawFrame(cnslOffx,cnslOffy,consoleWidth,consoleHeight,"║","═","╔","╗","╚","╝")
	resetCursor()
	
def drawFrame(X,Y,w,h,ver,hor,tl,tr,bl,br):

	for x in range(X , X + w):
		printAt(x,Y - 1, hor)
		printAt(x,Y + h, hor)
		
	for y in range(Y, Y + h):
		printAt(X - 1,y, ver)
		printAt(X + w , y  , ver)
	
	printAt(X - 1, Y - 1 ,tl);
	printAt(X + w , Y -1, tr);
	printAt(X - 1, Y + h, bl);
	printAt(X + w, Y + h, br);
	
def drawConsoleContents():	
	print(CONSOLE)
	for y in range(consoleHeight):
		printAt( cnslOffx,cnslOffy + y, console[y].ljust(consoleWidth))	
		
	resetCursor()
	
def drawConsoleLine(line):
	print(CONSOLE)
	printAt(cnslOffx,cnslOffy + line, console[line].ljust(consoleWidth))
	resetCursor()
	
def drawField():	
	drawFieldPortion(0,0,playfieldWidth,playfieldHeight)
	print(BORDER)
	
	drawFrame(pfOffx,pfOffy,playfieldWidth,playfieldHeight,"║","═","╔","╗","╚","╝")
	resetCursor()

def drawFieldPortion(x,y,w,h):
	for Y in range (y,y + h):
		for X in range (x,x + w):
			string = getColor(X,Y) + getAt(X,Y)
			printAt(pfOffx + X, pfOffy + Y ,string)
	
def drawStack():

	start = 0

	print(STACK)
	
	if len(stack) > stckMax:
		start = len(stack) - stckMax

	for i in range (0 ,stckMax):
		if i + start < len(stack):			
			j = stack[i + start]
			
			num =  str(j).ljust( stckWidth - 2 )
			
			if len(num) > stckWidth - 2:
				num = num[:stckWidth - 3] + "+"
			
			printAt(stckOffx,stckOffy - i, num + ":" + (chr(j) if 32 <= j <= 128 else "?"))
		else:
			printAt(stckOffx,stckOffy - i, " " * (stckWidth - 2) + ": ")
		
	resetCursor();	
	
def clearScreen():
	print('\033[37;40m')
	print('\033[2J')
	
def drawEverything():
	drawField()
	drawStack()
	print(BORDER)
	drawFrame(stckOffx,stckOffy - stckMax + 1,stckWidth,stckMax,"│","─","┌","┐","└","┘")
	drawConsole()
	drawTopMenu()
	
def drawFileMenu(dirs,files,selected,selectedOnly):	
	
	for i in range( len(dirs) ):
		format = MENU
		if i == selected:
			format = MENUSELECTED
			
		#if selectedOnly and i == selected or not selectedOnly:
		printAt(0, i, format + dirs[i].ljust(30) )
		
	for i in range( len(files) ):
		format = MENU
		if (i + len(dirs)) == selected:
			format = MENUSELECTED
			
		#if selectedOnly and i == selected or not selectedOnly:
		printAt(0, i +  len(dirs), format + files[i].ljust(30) )
	
def drawTopMenu():

	s = STACK + currentFile + MENU + "\n"
	
	for i in range(len(menu)):
		if i == menuSelector:
			s += MENUSELECTED + "[ " + menu[i][0] + " ]" + MENU
		else:
			s += "[ " + menu[i][0] + " ]"
		
	printAt(0,0,s)
		
#######################################################
#MAIN FUNCTIONS
#######################################################	

def isPrintable(num):
	return 32 <= num <= 128	

def getAt(x,y):
	if isPrintable(playfield[x][y]):
		return chr(playfield[x][y])
	return '¿'

def run():
	global programDir
	global programPntr
	global running
	global stack		
	
	stack = []
	drawStack()	
	
	console = ["" for x in range(consoleWidth)]
	drawConsoleContents()
	
	running = True
	programPntr = [0,0]
	programDir = [1,0]
	
	eraseCursor(fieldCursor)
	moveCursor(programPntr,0,0)

	L = []
	t = thread.start_new_thread(runInterruptThread, (L,))
	
	while(running):		
		char = chr(playfield[programPntr[0]][programPntr[1]])		
		
		if stringMode:
			if char[0] == '"':
				toggleString()
			else:
				push( ord(char[0]))
		elif char in ops:			
			ops[char]()
					
		sleep(runDelay)
		
		if L: 
			running = False
			break
		moveCursor(programPntr,programDir[0] ,programDir[1])
		
	#t.kill()
	eraseCursor(programPntr)
	moveCursor(fieldCursor,0,0)
	
def runInterruptThread(L):
	input()
	L.append(None)
	
def copySelection(cut):
	
	global copyBuffer
	
	startX = min(selectionCursor[0],fieldCursor[0])
	startY = min(selectionCursor[1],fieldCursor[1])
	endX = max(selectionCursor[0],fieldCursor[0]) + 1
	endY = max(selectionCursor[1],fieldCursor[1]) + 1
	
	copyBuffer = [[y for y in range(startY,endY)] for x in range(startX,endX)]	
	
	for x in range(startX,endX):
		for y in range(startY,endY):		
			copyBuffer[ x - startX ] [y - startY] = playfield[x][y]
			
			if cut:
				playfield[x][y] = 32
	
	if cut:
		drawFieldPortion(startX,startY,endX - startX,endY - startY)
		moveCursor(fieldCursor,0,0)
	
	printStringToConsole("\nSelection copied")

def pasteSelection():
	
	if copyBuffer == []:
		printStringToConsole("\nNothing in selection")
		return

	w = len(copyBuffer)
	h = len(copyBuffer[0])
		
	for x in range(w):
		for y in range(h):
			X = (fieldCursor[0] + x) % playfieldWidth
			Y = (fieldCursor[1] + y) % playfieldHeight
			playfield[X][Y] = copyBuffer[x][y]
	
	drawFieldPortion(fieldCursor[0],fieldCursor[1],w,h)
	moveCursor(fieldCursor,0,0)
		
def mainLoop():
	global programRunning
	global selecting
	
	cut = False
	
	while programRunning:
		key = rc.readkey()

		cursor = selectionCursor if selecting else fieldCursor
		
		if key == UP:
			moveCursor(cursor,0,-1)

		elif key == DOWN:
			moveCursor(cursor,0,1)

		elif key == RIGHT:
			moveCursor(cursor,1,0)

		elif key == LEFT:
			moveCursor(cursor,-1,0)
			
		elif key == '\x0e' and not selecting: #CTRL-N
			selecting = True
			selectionCursor[0] = fieldCursor[0]
			selectionCursor[1] = fieldCursor[1]
			
		elif key == '\x0b' and not selecting: #CTRL-K
			selectionCursor[0] = fieldCursor[0]
			selectionCursor[1] = fieldCursor[1]
			selecting = True
			cut = True
			
		elif key == '\x15' and not selecting: #CTRL-U
			pasteSelection()
			
		elif key == ENTER:
			if selecting:
				selecting = False
				eraseCursor(selectionCursor)
				copySelection(cut)
				cut = False
			else:
				run()
		
		elif key == ESC or key == '\x08':
			topMenu()
		
		elif isPrintable(ord(key[0])):
			playfield[fieldCursor[0]][fieldCursor[1]]= ord(key[0])
			moveCursor(fieldCursor,0,0)
			
		if selecting:
			moveCursor(fieldCursor,0,0)
			moveCursor(selectionCursor,0,0)
			
	clearScreen()
		
def exit():
	global programRunning
	programRunning = False
	
#######################################################
#MENUS
#######################################################

menuSelector = -1
def topMenu():
	global menuSelector
	global programRunning
	menuSelector = 0
	drawTopMenu()
	
	while(programRunning):
		key = rc.readkey()

		if key == RIGHT:
			menuSelector += 1
			menuSelector %= len(menu)
			drawTopMenu()
			
		elif key == LEFT:
			menuSelector -= 1
			menuSelector %= len(menu)
			drawTopMenu()
			
		elif key == ENTER:
			menu[menuSelector][1]()
			menuSelector = -1
			drawTopMenu()
			return
			
		elif key == ESC:
			menuSelector = -1
			drawTopMenu()
			return
				
def fileBrowser(directoryOnly):
	
	clearScreen()
	
	currentDir = os.getcwd()
	selector = 0
	
	while True:
		f = []
		d = [".."]
		
		if directoryOnly:
			d.append("[THIS FOLDER]")
		
		for (dirpath, dirnames, filenames) in os.walk(currentDir):
		
			if not directoryOnly:
				f.extend(filenames)				
				
			d.extend(dirnames)
			break
					
		f = [ x for x in f if (x.endswith('.bf') or x.endswith('.txt'))]	
		tot = len(d) + len(f)
		
		drawFileMenu(d,f,selector,False)
		
		while True:
			key = rc.readkey()
			
			if key == UP:
				selector -= 1
				selector %= tot
				drawFileMenu(d,f,selector,True)
				
			elif key == DOWN:
				selector += 1
				selector %= tot
				drawFileMenu(d,f,selector,True)
				
			elif key == ENTER:
				if selector == 0:
					clearScreen()
					currentDir = os.path.abspath('..')					
					break
					
				elif selector == 1 and directoryOnly:
					return currentDir					
					
				elif selector >= 1 and selector < len(d):
					clearScreen()					
					currentDir = currentDir + "\\" + d[selector]
					selector = 0
					break					
					
				elif selector >= len(d):
					return currentDir + "\\" + f[selector - len(d)]
		
			elif key == ESC:					
				return ""

def saveToFile(filepath):
	with open(filepath,'w+') as file:
	
		for y in range(playfieldHeight):
			for x in range(playfieldWidth):
				file.write( chr(playfield[x][y]))
				
			file.write("\n")
				
	printStringToConsole("\nFile saved")
	
def saveAs():
	filename = inputField("File name:",'string')	
	dir = fileBrowser(True)
	
	if len(filename) == 0 or filename == "\n":
		filename = "new.bf"
	
	clearScreen()
	drawEverything()
	saveToFile(dir + "\\" + filename)
	
def loadPlayfield():

	global currentFile
	global playfieldHeight
	global playfieldWidth
	global playfield
	
	filename = fileBrowser(False)	
	lastLen = -1
	
	pf = []
	
	w,h = 0,0
	
	if filename != "":
		currentFile = filename		
		with open(filename,'r') as file:
			
			for line in file:
				if len(line) != lastLen and lastLen != -1 and len(line) != lastLen-1:
					clearScreen()
					drawEverything()
					printStringToConsole("\nPlayfield has inconsistent lines")
					return #back to main menu , lines aren't consistent 
				else :
					lastLen = len(line)
					w = lastLen
				
				l = []
				for c in line:
					l.append(ord(c))
					
				pf.append(l)
					
				h += 1
					
	if w > maxPlayfieldWidth or h > maxPlayfieldHeight or w == 0 or h == 0:
		printStringToConsole("\nPlayfield size too big or null")
			
	else:
		playfieldHeight = h
		playfieldWidth = w - 1
		recalculateOffsets()
		
		playfield = [[32 for y in range(playfieldHeight)] for x in range(playfieldWidth) ]
		
		for x in range(playfieldWidth):
			for y in range(playfieldHeight):
				playfield[x][y] = pf[y][x]
			
	clearScreen()
	drawEverything()		

def newPlayfield(w,h):
	global playfield
	global console	
	global playfieldHeight
	global playfieldWidth
	
	playfieldHeight = h
	playfieldWidth = w
	
	recalculateOffsets()
	
	playfield = [[32 for y in range(playfieldHeight)] for x in range(playfieldWidth) ]
	console = ["" for x in range(consoleWidth)]

	clearScreen()
	drawEverything()
	moveCursor(fieldCursor,0,0)	

def newPlayfieldMenu():
	
	global currentFile
	
	w = inputField("New file width:",'int')
	h = inputField("New file height:",'int')
	
	if w < 1 or w > maxPlayfieldWidth:
		w = maxPlayfieldWidth
	if h < 1 or h > maxPlayfieldHeight:
		h = maxPlayfieldHeight
	
	currentFile = "new.bf"
	newPlayfield(w,h)
		
def inputField(text,type):
		
	frameWidth = 20	
	
	for x in range(frameWidth):
		printAt(x,0," ")
		printAt(x,1," ")
		printAt(x,2," ")
	
	drawFrame(1,1,frameWidth,1,"│","─","┌","┐","└","┘")
	printAt(2,0,text)
	
	if type == "char":
	
		while True:
			input = rc.readkey()		
			if ' ' <= input <= '~':
				return input			
			elif input == ENTER:
				return "\n"
				
	if type == "int":
		
		num = ""
		while True:
			input = rc.readkey()
							
			if input == BACKSPACE or input == '\x1f' or input == '\x08':
				num = num[:-1]					
			
			elif input.isdigit() and len(num) < 8:
				num += input				
				
			elif input == ENTER:
				try:
					num = int(num)
				except:
					num = 0
				break	
		
			printAt(1,1,num.ljust(frameWidth - 1))
		
		return int(num)
		
	if type == "string":
		
		string = ""		
		
		while True:
			input = rc.readkey()	
			
			if ' ' <= input <= '~' and len(string) < frameWidth - 2:
				string += input
				
			elif input == ENTER:
				break
				
			elif input == BACKSPACE or input == '\x1f' or input == '\x08':
				string = string[:-1]
		
			printAt(1,1,string.ljust(frameWidth - 1))
		
		return string

def setDelay():
	global runDelay
	delay = inputField("Set run delay (ms):","int")
	
	if delay < 25:
		delay = 25
	
	runDelay = delay / 1000
	clearScreen()
	drawEverything()
		
menu = [
("NEW" , newPlayfieldMenu),
("LOAD", loadPlayfield),
("SAVE", lambda : saveToFile(currentFile)),
("SAVE AS", saveAs),
("DELAY", setDelay),
("EXIT", exit)
]
	
#######################################################
#BEFUNGE FUNCTIONS
#######################################################

def pop():
	r = 0
	if stack:
		r = stack.pop()
	drawStack()
	return r

def push(ch):
	stack.append(ch)
	drawStack()

def jump():
	programPntr[0] += programDir[0]
	programPntr[1] += programDir[1]
	wrap(programPntr)

def swap():
	a = pop()
	b = pop()
	push(a)
	push(b)

def dup():
	a = pop()
	push(a)
	push(a)	

def changeProgramDir(x,y):
	global programDir
	programDir = [x,y]		

def wrap(cursor):
	cursor[0] %= playfieldWidth
	cursor[1] %= playfieldHeight	

def kill():
	global running
	running = False

def sub():
	a = pop()
	b = pop()
	push(b - a)
	
def div():
	a = pop()
	b = pop()
	push(b / a)
	
def mod():
	a = pop()
	b = pop()
	push(b % a)
	
def gt():
	a = pop()
	b = pop()
	
	if b > a:
		push(1)
	else:
		push(0)

def randDir():	
	global programDir
	programDir = random.choice([[0,1],[0,-1],[1,0],[-1,0]])
	
def toggleString():
	global stringMode
	stringMode = not stringMode
	
def printToConsole(num):	
	global consoleY
		
	char = chr(num)	
	
	if num == 127:
		if len ( console[consoleY] ) > 0:
			console[consoleY] = console[consoleY][:-1]			
	elif num == 10:
		consoleNewLineCheck(True)
	
	elif 32 <= num <= 126:
		consoleNewLineCheck(False)
		console[consoleY] += char
		drawConsoleLine(consoleY)
			
def printStringToConsole(string):	
	for c in string:
		printToConsole(ord(c))
	
def consoleNewLineCheck(newLine):
	global consoleY
	
	if newLine or len(console[consoleY]) >= consoleWidth:
		consoleY += 1
		newLine = True
		
	if consoleY >= consoleHeight:
		consoleY = consoleHeight - 1
			
		for i in range(consoleHeight - 1):
			console[i] = console[i + 1]
			
		console[consoleHeight - 1] = ""
				
		drawConsoleContents()		
	else:
		drawConsoleLine(consoleY)	
		if newLine:
			drawConsoleLine(consoleY -1)
					
def printChr():
	printToConsole( pop() )
	
def printNum():
	i = pop()	
	string = str(i)
	
	for c in string:
		printToConsole(ord(c))
	
def readCh():
	push(ord(inputField("Input a character",'char')))
	clearScreen()
	drawEverything()
		
def readNum():
	push(inputField("Input a number",'int'))
	clearScreen()
	drawEverything()
	
def get():
	y = pop()
	x = pop()
	
	try:		
		push(playfield[x][y])
	except:
		push(0)

def put():
	
	y = pop()
	x = pop()
	v = pop()
	
	oldX = programPntr[0]
	oldY = programPntr[1]
		
	try:
		playfield[x][y] = v
		moveCursorAbs(programPntr,x,y)
		sleep(0.05)
		moveCursorAbs(programPntr,oldX,oldY)
	except:
		printToConsole(31);
		pass
	
#######################################################
#FUNCTION DICTIONARY
#######################################################

ops = {
'+' : lambda : push(pop() + pop()),
'-' : sub,
'*' : lambda : push(pop() * pop()),
'/' : div,
'>' : lambda : changeProgramDir(1,0),
'v' : lambda : changeProgramDir(0,1),
'<' : lambda : changeProgramDir(-1,0),
'^' : lambda : changeProgramDir(0,-1),
':' : dup,
'\\': swap,
'@' : kill,
'#' : jump,
'%' : mod,
'`' : gt,
'!' : lambda : push(1) if pop() == 0 else push(0),
'?' : randDir,
'_' : lambda : changeProgramDir(1,0) if pop() == 0 else changeProgramDir(-1,0),
'|' : lambda : changeProgramDir(0,1) if pop() == 0 else changeProgramDir(0,-1),
'"' : toggleString,
'$' : pop,
'.' : printNum,
',' : printChr,
'g' : get,
'p' : put,
'&' : readNum,
'~' : readCh
}

for i in range(10):
	ops[str(i)] = lambda i=i : push(i)
	
#######################################################
#INIT
#######################################################

init()
newPlayfield(playfieldWidth,playfieldHeight)
mainLoop()
