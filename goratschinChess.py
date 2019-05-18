import asyncio
import os
import sys
import math

from chess import Move
from chess.engine import PovScore
import chess.engine


# This class contains the inner workings of goratschinChess. If you want to change its settings or start it then
# Please go to launcher.py This file also lets you change what engines GoratschinChess uses.
class GoratschinChess:
    # after a stop command, ignore the finish callback. See onFinished.
    _canceled = False

    # the pythonChess engine objects, loaded from the filePath and fileName
    _engines = [None, None]
    _results = [None, None]

    # The current move decided by the engine. None when it doesn't know yet
    _moves = [None, None]
        
    # The current score of move decided by the engine. None when it doesn't know yet
    _scores = [None, None]
    _scores_white = [None, None] # from white's view

    # current board status, probably received from UCI position commands
    board = chess.Board()

    # Statistics for how often is listened to each engine.
    listenedTo = [0, 0]
    agreed = 0

    # Initialized in the init function. These are the folder path and a list of filenames in that folder
    engineFolder = None
    engineFileNames = None
    
    score_margin = None

    def __init__(self, engineLocation, engineNames):
        asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
        self.engineFolder = engineLocation
        self.engineFileNames = engineNames
        self.score_margin = 0.5 # in centipawns
        print_and_flush("GoratschinChess 1.0 by P. Feldtmann based on CombiChess by T. Friederich")

    # This starts GoratschinChess.
    def start(self):
        # first start the engines
        for i in range(0, len(self._engines)):
            try:
                ## self._engines[i] = chess.uci.popen_engine(os.path.join(self.engineFolder, self.engineFileNames[i]), setpgrp=False)
                self._engines[i] = chess.engine.SimpleEngine.popen_uci(os.path.join(self.engineFolder, self.engineFileNames[i]))
                # Register a standard info handler.
                ##info_handler = chess.uci.InfoHandler()
                ##self._engines[i].info_handlers.append(info_handler)
            except:
                sys.stderr.write("GoratschinChess Error: could not load the engine at file path: " + self.engineFolder + "/" + self.engineFileNames[i])
                sys.stderr.write(
                    "\n\nDid you change the script to include the engines you want to use with GoratschinChess?")
                sys.stderr.write("To do this, open GoratschinLauncher.py and change the engineFilePaths.\n")
                sys.exit()

            # tell the engines to init and start a new game
            ##self._engines[i].uci()
            ##self._engines[i].ucinewgame()
            
        # starts the main program
        self._mainloop()

    # Main program loop. It keep waiting for input after a command is finished
    def _mainloop(self):
        exitFlag = False
        while not exitFlag:

            userCommand = input()

            # print_and_flush("info string cmd: " + userCommand)
            
            if userCommand == "uci":
                print_and_flush("id name Goratschin")
                print_and_flush("id author Peter Feldtmann")
                print_and_flush("uciok")

            elif userCommand.startswith("setoption name"):
                # Skip button type options
                if " value " not in userCommand:
                    continue
                options = {}
                parts = userCommand.split(" ", 2)
                parts = parts[-1].split(" value ")
                options[parts[0]] = parts[1]
                for engine in self._engines:
                    engine.configure(options)
                
            elif userCommand == "isready":
                print_and_flush("readyok")

            elif userCommand.startswith("go"):
                parts = userCommand.split(" ")
                go_commands = {}
                for command in ("movetime", "wtime", "btime", "winc", "binc", "depth", "nodes"):
                    if command in parts:
                        go_commands[command] = parts[parts.index(command) + 1]
                self._start_engines(go_commands)
                ##self._check_results()
                loop = asyncio.get_event_loop()
#                 try:
                loop.run_until_complete(self._check_results())
#                 finally:
#                     loop.close()

            elif userCommand.startswith("position"):
                self._handle_position(userCommand)

            elif userCommand.startswith("endg"):   
                self._handle_position("position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1 moves e1f2 e8e7" )
                
            elif userCommand.startswith("bdg"):   
                self._handle_position("position fen rn1qkb1r/ppp1pppp/8/5b2/3Pn3/2N5/PPP3PP/R1BQKBNR w KQkq - 0 6" )
                 
            elif userCommand.startswith("tb"):  
                options = {}    
                options["SyzygyPath"] = "D:/chess/tb-master/tb"
                #for engine in self._engines:
                    # engine.configure(options)
                self._engines[1].configure(options)
                    
            elif userCommand.startswith("mw3"): 
                self._handle_position("position fen " + "k7/8/8/3K4/8/8/8/7R w - - 4 1" )
                
            elif userCommand.startswith("mb3"): 
                self._handle_position("position fen " + "r7/8/8/8/4k3/8/8/7K b - - 0 1 " )
                                    
            elif userCommand == "quit":
                for en in self._engines:
                    en.quit()
                print("Bye.")
                exitFlag = True
                
            elif userCommand == "stop":
                for en in self._engines:
                    en.quit()
            else:
                print_and_flush("unknown command")

    def _start_engine(self, index, cmds):
        engine = self._engines[index]
        ##engine.ucinewgame()
        #engine.position(self.board)
        
        white_clock = int(int(cmds.get("wtime"))/1000) if cmds.get("wtime") is not None else None 
        black_clock=int(int(cmds.get("btime"))/1000)   if cmds.get("btime") is not None else None 
        white_inc=int(int(cmds.get("winc"))/1000) if cmds.get("winc") is not None else None 
        black_inc=int(int(cmds.get("binc"))/1000) if cmds.get("binc") is not None else None 
        depth=int(cmds.get("depth")) if cmds.get("depth") is not None else None 
        nodes=int(cmds.get("nodes")) if cmds.get("nodes") is not None else None 
        time=int(int(cmds.get("movetime"))/1000) if cmds.get("movetime") is not None else None 
        mate=int(cmds.get("mate")) if cmds.get("mate") is not None else None 
        remaining_moves=int(cmds.get("movestogo")) if cmds.get("movestogo") is not None else None 
                
        limit = chess.engine.Limit(
            white_clock=white_clock,
            black_clock=black_clock,
            white_inc=white_inc,
            black_inc=black_inc,
            depth=depth,
            nodes=nodes,
            time=time,
            mate=mate,
            remaining_moves=remaining_moves
            )
              
        self._results[index] = engine.analysis(self.board, limit)
        ## print_and_flush(self._results[index])
             
        engineName = self.engineFileNames[index]
        if index == 0:
            print_and_flush("info string started engine 0 " + engineName + " as boss " + str(limit))
        else:
            print_and_flush("info string started engine 1 " + engineName + " as clerk " + str(limit))

    def _start_engines(self, go_commands):
        self._moves = [None, None]
        self._scores = [None, None]
        self._canceled = False

        self._start_engine(1, go_commands)
        self._start_engine(0, go_commands)
        
    async def _check_result(self, index):
        info = None
        exitLoop = False
        while not exitLoop:   
            last_info = info   
            info = self._results[index].next()
            if info is None:
                exitLoop = True
            elif 'currmove' not in info:
                text = self._make_uci_info_from_dict(info)
                ## print_and_flush("info string engine " + str(index) + " " + self.engineFileNames[index] + " ")
                print_and_flush("info " + text)
            await asyncio.sleep(0)            
            
        self._decide(index, last_info)
                        
    async def _check_results(self):
        tasks = []
#         tasks.append(asyncio.ensure_future(self._check_result(0)))
#         tasks.append(asyncio.ensure_future(self._check_result(1)))
        tasks.append(self._check_result(0))
        tasks.append(self._check_result(1))
        await asyncio.gather(*tasks)
             
    def _decide(self, index, info):
        boss = 0
        clerk = 1
     
        engineMove = info["pv"][0]
        engineName = self.engineFileNames[index]
        
        # Retrieve the score of the mainline (PV 1) after search is completed.
        # Note that the score is relative to the side to move.
        povScore = info["score"]
        score = povScore.pov(self.board.turn)
        cp = score.score()
        
        ## print_and_flush("info string pov score " + str(cp))
        
        # correct score if mating
        if score.is_mate():
            if score.mate() > 0:
                cp = 30000 - (score.mate() * 10 )
            else:
                cp = -30000 + (score.mate() * 10 )
            
        cp = cp / 100

        self._scores[index] = cp
        
        # white's view
        cpWhite = cp
        if not(self.board.turn):  # BLACK to move
            cpWhite = -cpWhite
            
        self._scores_white[index] = cpWhite

        print_and_flush("info string eval " + engineName + ": bm " + str(engineMove) + ", sc " + str(cpWhite))

        # set the move in the found moves
        self._moves[index] = engineMove
        
#         if score.is_mate():
#             if index == boss:
#                 print_and_flush("info string boss detected mate, stop")
#                 self.listenedTo[boss] += 1
#                 bestMove = self._moves[boss]
#             else:
#                 print_and_flush("info string clerk detected mate, stop")
#                 self.listenedTo[clerk] += 1
#                 bestMove = self._moves[clerk]
#             for info in self._results[index]: 
#                 info.stop()
            
        # if engine 0 and 1 are done, and they agree on a move, do that move
        if self._moves[boss] is not None and self._moves[boss] == self._moves[clerk]:
            print_and_flush("info string boss and clerk agree, listening to boss")
            self.listenedTo[boss] += 1
            self.agreed += 1
            bestMove = self._moves[boss]
            
        # if clerk is much better than boss, do clerk's move
        elif self._moves[boss] is not None and self._moves[clerk] is not None:
            diff = self._scores[clerk] - self._scores[boss]
                       
            if diff >= self.score_margin:
                print_and_flush("info string listening to stronger clerk")
                self.listenedTo[clerk] += 1
                bestMove = self._moves[clerk]
            elif diff > 0:
                print_and_flush("info string listening to boss, clerk is stronger, but not enough")
                self.listenedTo[boss] += 1
                bestMove = self._moves[boss]
            else:
                print_and_flush("info string listening to boss, clerk is not stronger")
                self.listenedTo[boss] += 1
                bestMove = self._moves[boss]

        # all engines are done and they dont agree. Listen to boss
        elif None not in self._moves:
            print_and_flush("info string listening to boss, engines dont agree")
            self.listenedTo[boss] += 1
            bestMove = self._moves[boss]
            
        # we dont know our best move yet
        else:
            print_and_flush("info string dont know best move yet")
            return

        self._printStats()

        self._canceled = True
        # stop remaining engines
#         for engine in self._engines:
#             engine.stop()

        print_and_flush("bestmove " + str(bestMove))

    # inverse of chess.emgine.parse_uci_info
    # make uci info string from dictionary
    def _make_uci_info_from_dict(self, kv_dict):
        result = []
        for i,j in kv_dict.items():
            if isinstance(j, int):
                result.append('%s %d' % (i,j))
            elif isinstance(j, float):
                result.append('%s %f' % (i,j))    
            elif isinstance(j, PovScore):
                if j.is_mate():
                    result.append('%s mate %s' % (i,j.pov(self.board.turn).mate()))   
                else:
                    result.append('%s cp %s' % (i,j.pov(self.board.turn).score()))             
            elif isinstance(j, list):
                result.append('%s ' % i)
                for m in j:
                    if isinstance(m, Move):
                        result.append('%s' % m.uci())        
            else:
                result.append("%s '%s'" % (i,j))
                ## print_and_flush(i + " is " + type(j).__name__)
        
        return ' '.join(result) 

    # handle UCI position command
    def _handle_position(self, positionInput):
        words = positionInput.split()
        # if this is not true, it is not a position command
        assert words[0] == "position"
        try:
            # handle building up the board from a FEN string
            if words[1] == "fen":
                rest = positionInput.split(' ', 2)[2]
                if "moves" in rest:
                    rest = rest.split()
                    fen, moves = " ".join(rest[:6]), rest[7:]
                    self.board.set_fen(fen)
                    for move in moves:
                        print_and_flush("Adding " + move + " to stack")
                        self.board.push_uci(move)
                else:
                    self.board.set_fen(rest)
            # handle board from startpos command, building up the board with moves
            elif words[1] == "startpos":
                self.board.reset()
                for move in words[3:]:  # skip the first two words : 'position' and 'startpos'
                    print_and_flush("Adding " + move + " to stack")
                    self.board.push_uci(move)
            else:
                print_and_flush("unknown position type")
        except Exception as e:
            print_and_flush("something went wrong with the position. Please try again")
            print_and_flush(e)

        # show the board
        # printAndFlush(self.board)

    # prints stats on how often was listened to boss and how often to clerk
    def _printStats(self):
        winBoss, drawBoss, lossBoss = get_win_draw_loss_percentages(self._scores_white[0])
        print_and_flush("info string Boss  best move: " + str(self._moves[0]) + " score: " + str(self._scores_white[0])
                       + " white {:2.1f}% win, {:2.1f}% draw, {:2.1f}% loss".format(winBoss, drawBoss, lossBoss))
        winClerk, drawClerk, lossClerk = get_win_draw_loss_percentages(self._scores_white[1])
        print_and_flush("info string Clerk best move: " + str(self._moves[1]) + " score: " + str(self._scores_white[1])
                      + " white {:2.1f}% win, {:2.1f}% draw, {:2.1f}% loss".format(winClerk, drawClerk, lossClerk))
        print_and_flush("info string listen stats [Boss, Clerk] " + str(self.listenedTo))
        totalSum = self.listenedTo[0] + self.listenedTo[1] 
        bossSum = self.listenedTo[0] 
        bossPercent = (float(bossSum) / float(totalSum)) * 100.0
        print_and_flush("info string listen stats Boss {:2.1f} %".format(bossPercent))
        agreedPercent = (float(self.agreed) / float(totalSum)) * 100.0
        print_and_flush("info string Boss and Clerk agreed so far " + str(self.agreed) + " times, {:2.1f} % ".format(agreedPercent))


# UTILS

# This function flushes stdout after writing so the UCI GUI sees it
def print_and_flush(text):
    print(text, flush=True)
  
  
# get score as win/draw/loss percentages  
def get_win_draw_loss_percentages(pawn_value):
    w = 1 / (1 + pow( 10, (- (abs(pawn_value) / 4)))) * 100 # - 50 + (abs(pawn_value) / 10)
    ## q = (math.degrees(math.atan(abs(pawn_value) / 290.680623072))) / 1.548090806     
    ## w = q # * 5000 + 5000
    if (pawn_value >= 0):
        return w, 100 - w, 0
    else:
        return 0, 100 - w, w
    
    
    
