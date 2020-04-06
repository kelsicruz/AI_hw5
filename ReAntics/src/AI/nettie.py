import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
import math

#global vars
bestFood = None
avgDistToFoodPoint = None
hiddenNetwork = [[]]
outputNetwork = [[]]
biasWeights = [0, 0, 0]
learningRate = 0.1
e = 2.71828
##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state.  This class has methods
#that
#will be implemented by students in Dr.  Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "UtilityAgent_gieseman21_cruzk20")
        self.resetPlayerData()
        
    def resetPlayerData(self):
        global bestFood
        global avgDistToFoodPoint
        bestFood = None
        avgDistToFoodPoint = None
        self.myTunnel = None
        self.myHill = None

    def getPlacement(self, currentState):
    
        me = currentState.whoseTurn
        
        if currentState.phase == SETUP_PHASE_1:
            #Hill, Tunnel, Grass
            self.resetPlayerData()
            self.myNest = (2,1)
            self.myTunnel = (7,1)
            return [(2,1), (7, 1), 
                    (0,3), (1,3), (2,3), (3,3), \
                    (4,3), (5,3), (6,3), \
                    (8,3), (9,3)]
        elif currentState.phase == SETUP_PHASE_2:
            moves = []
            for y in range(6, 10):
                for x in range(0,10):
                    if currentState.board[x][y].constr == None and len(moves) < 2:
                        moves.append((x,y))
            return moves
            
        else:            
            return None  #should never happen
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's
    #   move
    #   (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        me = currentState.whoseTurn
        workerAnts = getAntList(currentState, me, (WORKER,))
        global bestFood
        global avgDistToFoodPoint

        #starts by assigning some variables to improve evaluation of proximity to scoring 11 food
        if (me == PLAYER_ONE):
            enemy = PLAYER_TWO
        else :
            enemy = PLAYER_ONE
        
        if (self.myTunnel == None):
            self.myTunnel = getConstrList(currentState, me, (TUNNEL,))[0].coords
            
        if (self.myHill == None):
            self.myHill = getConstrList(currentState, me, (ANTHILL,))[0].coords
        
        if (bestFood == None and avgDistToFoodPoint == None):
            assignGlobalVars(currentState, self.myTunnel, self.myHill)

        selectedMove = getMove(currentState)
            
        return selectedMove
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked
    #   (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

#in the current version, only evaluates proximity to winning via food collection
def heuristicStepsToGoal(currentState):
    me = currentState.whoseTurn
    myQueen = getAntList(currentState, me, (QUEEN,))[0]

    #if a state has a dead queen, it should be avoided!!!
    if (myQueen.health == 0):
        return 99999999

    stepsToGoal = stepsToFoodGoal(currentState)
    
    #add the enemy health to our heuristic measure in order to encourage attacks
    stepsToGoal += getTotalEnemyHealth(currentState)

    return stepsToGoal
        

#helper method for heuristicStepsToGoal, evaluates distance to win by food
def stepsToFoodGoal(currentState):
    #get the board
    # fastClone(currentState)
        
    #get numWorkers
    global avgDistToFoodPoint
    global bestFood

    myInv = getCurrPlayerInventory(currentState)
    foodScore = myInv.foodCount
    me = currentState.whoseTurn
    workerAnts = getAntList(currentState, me, (WORKER,))

    #cant collect food without workers
    if (len(workerAnts) == 0):
        return 99999999

    #in assignGlobalVars, we assigned avgDistToFoodPoint
    #we multiply that by the number of food points we need
    stepsToFoodGoal = 0
    for i in range(11-foodScore):
        stepsToFoodGoal += avgDistToFoodPoint
    
    #to that, we add the distance from scoring a food point of the ant that is closest to scoring one
    minStepsToFoodPoint = 99999999
    for worker in workerAnts:
        temp = stepsToFoodPoint(currentState, worker)
        if (temp < minStepsToFoodPoint):
            minStepsToFoodPoint = temp

    stepsToFoodGoal += minStepsToFoodPoint
    return stepsToFoodGoal
    
        
        
### Calculates the necessary steps to get +1 food point ###   
def stepsToFoodPoint(currentState, workerAnt):
    global bestFood
    #Check if the ant is carrying food, then we only need steps to nearest constr
    if (workerAnt.carrying):
        dist = stepsToReach(currentState, workerAnt.coords, bestFood[1])
    #Otherwise, calculate the entire cycle the ant would need to complete to get +1 food point
    else:
        dist = stepsToReach(currentState, workerAnt.coords, bestFood[0].coords) + stepsToReach(currentState, bestFood[0].coords, bestFood[1])
        
    return dist

#not yet implemented
def stepsToQueenGoal(currentState):
    pass

#not yet implemented   
def stepsToAntHillGoal(currentState):
    pass
    
#uses MoveNode objects to represent the outcome of all possible moves
#returns the move associated with the MoveNode that has the lowest (best) utility
def getMove(currentState):
    moves = listAllLegalMoves(currentState)

    moveNodes = []

    for move in moves:
        nextState = getNextState(currentState, move)
        stateUtility = heuristicStepsToGoal(nextState)
        node = MoveNode(move, nextState)
        node.setUtility(stateUtility)
        moveNodes.append(node)
        
    bestMoveNode = bestMove(moveNodes)
    retMove = bestMoveNode.move
            
    return retMove

#returns the MoveNode with the lowest (best) utility given a list of MoveNodes
def bestMove(moveNodes):
    bestNodeUtility = 99999999
    bestNode = moveNodes[0]
    for moveNode in moveNodes:
        if (moveNode.utility < bestNodeUtility):
            bestNode = moveNode
            bestNodeUtility = moveNode.utility
    
    return bestNode

#assign the vars bestFood and avgDistToFoodPoint, which are used in determining stepsToFoodGoal
def assignGlobalVars(currentState, myTunnel, myHill):
    
    global bestFood
    global avgDistToFoodPoint

    foods = getConstrList(currentState, None, (FOOD,))
    bestTunnelDist = 50
    bestHillDist = 50
    bestTunnelFood = None
    bestHillFood = None
            
    for food in foods:
        dist = stepsToReach(currentState, myTunnel, food.coords)
        if (dist < bestTunnelDist) :
            bestTunnelFood = food
            bestTunnelDist = dist
        dist = stepsToReach(currentState, myHill, food.coords)
        if (dist < bestHillDist) :
            bestHillFood = food
            bestHillDist = dist
            
    if (bestHillDist < bestTunnelDist):
        bestFood = (bestHillFood, myHill)
    else :
        bestFood = (bestTunnelFood, myTunnel)

    me = currentState.whoseTurn
    workerAnts = getAntList(currentState, me, (WORKER,))

    for worker in workerAnts:
        foodToTunnelDist = stepsToReach(currentState, bestFood[0].coords, bestFood[1])
        marginalFoodPointCost = foodToTunnelDist * 2
    avgDistToFoodPoint = marginalFoodPointCost
    
#sums health of all enemy ants. Used to encourage attack moves
def getTotalEnemyHealth(currentState):
    me = currentState.whoseTurn
    if (me == PLAYER_ONE):
        enemy = PLAYER_TWO
    else :
        enemy = PLAYER_ONE
    
    enemyAnts = getAntList(currentState, enemy, (WORKER,QUEEN,DRONE,SOLDIER,R_SOLDIER))
    totalEnemyHealth = 0
    for ant in enemyAnts:
        totalEnemyHealth += ant.health
        
    return totalEnemyHealth

class MoveNode():
    
    def __init__(self, move, state):
        self.move = move
        self.state = state
        self.depth = 1
        self.utility = None
        self.parent = None
        
    def setUtility(self, newUtility):
        self.utility = newUtility + self.depth

    def __str__(self):
        return "Move: " + str(self.move) + ", Utility: " + str(self.utility)
    
    def initHiddenNetwork(self, currentState):
        me = currentState.whoseTurn
        if (me == PLAYER_ONE):
            enemy = PLAYER_TWO
        else :
            enemy = PLAYER_ONE

        myInv = getCurrPlayerInventory(currentState)
        foodScore = myInv.foodCount

        enQueen = getAntList(currentState, enemy, (QUEEN,))

        enHill = getConstrList(currentState, enemy, (ANTHILL,))[0]

        myQueen = getAntList(currentState, me, (QUEEN,))[0]
        # myQueenHealth = myQueen.health

        myHill = getConstrList(currentState, me, (ANTHILL,))[0]
        # myHillHealth = myHill.captureHealth

        return hiddenNetwork[[foodScore/11, 2, 0], [enQueen.health/10, -1, 0], [enHill.captureHealth/3, -1, 0], [myQueen.health/10, 0, 1], [myHill.captureHealth/3], 0, 1]
    
    def initOutputNetwork(self, currentState, hiddenNetwork):
        initHiddenNetwork(self, currentState)

        me = currentState.whoseTurn
        if (me == PLAYER_ONE):
            enemy = PLAYER_TWO
        else :
            enemy = PLAYER_ONE

        x1 = 1 * biasWeights[0]
        x2 = 1 * biasWeights[1]

        for i in range(len(hiddenNetwork)):
            x1 += hiddenNetwork[i][0] * hiddenNetwork[i][1]
        
        for i in range(len(hiddenNetwork)):
            x2 += hiddenNetwork[i][0] * hiddenNetwork[i][2]

        return outputNetwork[[sigmoid(self, x1), 1], [sigmoid(self, x2), 1]]

    def evaluateState(self, currentState):
        output = 1 * biasWeights[2]

        for i in range(len(outputNetwork)):
            output += outputNetwork[i][0] * outputNetwork[i][1]

        return sigmoid(self, output)
    
    def sigmoid(self, x):
        return 1/(1 + e^(-x))
    
    def backPropagation(self, currentState):
        # might change 1 later
        netOutput = evaluateState(self, currentState)
        error = 1 - netOutput
        print(str(error))

        errorTerm = error * netOutput * (1 - netOutput)

        topError = errorTerm * outputNetwork[0][1]
        bottomError = errorTerm * outputNetwork[1][1]
        
        # may need to fix last part in parens
        for i in range(len(hiddenNetwork)):
            hiddenNetwork[i][1] += learningRate * topError * ( netOutput * (1 - netOutput) * outputNetwork[0][0] )


        # commenting out for now
    # def neuralnet(self, currentState):

    #     # inputs.append(1) # bias input off
    #     # inputs.append(foodScore/11)
    #     # inputs.append(enQueen/10)
    #     # inputs.append(enHill.captureHealth/3)
    #     # inputs.append(1) # bias input def
    #     # inputs.append(myQueenHealth/10)
    #     # inputs.append(myHillHealth/3)

    #     weights = [0, 2, -1, -1] # hard coded for now, will need an init function later

    #     fun = 0
    #     for i in range(len(inputs)): # this could be wrong
    #         fun += inputs[i]*weights[i]
        
    #     output = sigmoid(self, fun)

    #     steepness = output * (1 - output) # derivative = g(x) * (1-g(x)), taking shortcut rn

    #     # readjust weights 
    #     for i in range(len(weights)):
    #         # may have to change "desiredOutcome" to something else
    #         weights[i] = weights[i] + (learningRate)(desiredOutcome - output)(steepness)(inputs[i])
    