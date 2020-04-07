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
        super(AIPlayer, self).__init__(inputPlayerId, "Nettie")
        self.resetPlayerData()
        # self.hiddenNetwork = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        # self.outputNetwork = [[0, 0], [0, 0], [0, 0]]
        # self.biasWeights = []
        # self.setWeights()
        # printWeights(self)
        self.hiddenNetwork = [[0, 1.3324, -1.1546, 0.1127], [0, 0.3683, 0.1637, -0.6542], [0, -0.3298, 0.3555, 0.1057], [0, -1.3252, 0.2899, 0.1528], [0, -0.0549, 0.9299, 0.5141]]
        self.outputNetwork = [[0, 1.1102], [0, -1.6929], [0, -0.6007]]
        self.biasWeights = [-0.2783, -0.5767, -2.4206, 0.1364]
        self.learningRate = 0.1
        # self.outFileLocation = "../neuralNetwork.txt"
        # self.outFile = open(self.outFileLocation, "w+")
        # sys.stdout = self.outFile  # redirect stdout

    def setWeights(self):
        # set biases
        for i in range(4):
            num = random.random()
            if random.randint(0, 1) == 1:
                self.biasWeights.append(num)
            else:
                self.biasWeights.append(-1*num)
        
        # set normal weights
        for j in range(len(self.hiddenNetwork)):
            for k in range(1, len(self.hiddenNetwork[j])):
                num = random.random()
                if random.randint(0, 1) == 1:
                    self.hiddenNetwork[j][k] = num
                else:
                    self.hiddenNetwork[j][k] = -1*num
        
        # set output network weights
        for j in range(len(self.outputNetwork)):
            for k in range(1, len(self.outputNetwork[j])):
                num = random.random()
                if random.randint(0, 1) == 1:
                    self.outputNetwork[j][k] = num
                else:
                    self.outputNetwork[j][k] = -1*num

        
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

        selectedMove = getUtilityMove(self, currentState)
            
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
        if hasWon:
            print("we won!")
            # rintWeights(self)
        
        else:
            print("we lost :( ")
            # printWeights(self)

#in the current version, only evaluates proximity to winning via food collection
def heuristicStepsToGoal(currentState):
    me = currentState.whoseTurn
    myQueen = getAntList(currentState, me, (QUEEN,))[0]

    #if a state has a dead queen, it should be avoided!!!
    if (myQueen.health == 0):
        return 100

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
        return 100

    #in assignGlobalVars, we assigned avgDistToFoodPoint
    #we multiply that by the number of food points we need
    stepsToFoodGoal = 0
    for i in range(11-foodScore):
        stepsToFoodGoal += avgDistToFoodPoint
    
    #to that, we add the distance from scoring a food point of the ant that is closest to scoring one
    minStepsToFoodPoint = 100
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
def getUtilityMove(self, currentState):
    # evalFinal(self, currentState)
    
    moves = listAllLegalMoves(currentState)

    moveNodes = []

    for move in moves:
        nextState = getNextState(currentState, move)
        #stateUtility = heuristicStepsToGoal(nextState)
        stateUtility = (getOutput(self, nextState))*100
        node = MoveNode(move, nextState)
        node.setUtility(stateUtility)
        moveNodes.append(node)
        
    bestMoveNode = bestMove(moveNodes)
    retMove = bestMoveNode.move
            
    return retMove

#returns the MoveNode with the lowest (best) utility given a list of MoveNodes
def bestMove(moveNodes):
    bestNodeUtility = 100
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

def setInputs(self, currentState):
        me = currentState.whoseTurn
        if (me == PLAYER_ONE):
            enemy = PLAYER_TWO
        else:
            enemy = PLAYER_ONE

        # myInv = getCurrPlayerInventory(currentState)
        # foodScore = myInv.foodCount

        foodGoal = stepsToFoodGoal(currentState)

        enQueen = getAntList(currentState, enemy, (QUEEN,))[0]

        enHill = getConstrList(currentState, enemy, (ANTHILL,))[0]

        myQueen = getAntList(currentState, me, (QUEEN,))[0]
        # myQueenHealth = myQueen.health

        myHill = getConstrList(currentState, me, (ANTHILL,))[0]
        # myHillHealth = myHill.captureHealth

        self.hiddenNetwork[0][0] = foodGoal/100
        self.hiddenNetwork[1][0] = enQueen.health/10
        self.hiddenNetwork[2][0] = enHill.captureHealth/3
        self.hiddenNetwork[3][0] = myQueen.health/10
        self.hiddenNetwork[4][0] = myHill.captureHealth/3

    
def getOutput(self, currentState):

        setInputs(self, currentState)

        me = currentState.whoseTurn
        if (me == PLAYER_ONE):
            enemy = PLAYER_TWO
        else :
            enemy = PLAYER_ONE

        x1 = 1 * self.biasWeights[0]
        x2 = 1 * self.biasWeights[1]
        x3 = 1 * self.biasWeights[2]

        for i in range(len(self.hiddenNetwork)):
            x1 += self.hiddenNetwork[i][0] * self.hiddenNetwork[i][1]
        
        for i in range(len(self.hiddenNetwork)):
            x2 += self.hiddenNetwork[i][0] * self.hiddenNetwork[i][2]

        for i in range(len(self.hiddenNetwork)):
            x3 += self.hiddenNetwork[i][0] * self.hiddenNetwork[i][3]

        self.outputNetwork[0][0] = sigmoid(x1)
        self.outputNetwork[1][0] = sigmoid(x2)
        self.outputNetwork[2][0] = sigmoid(x3)


        output = 1 * self.biasWeights[3]

        for i in range(len(self.outputNetwork)):
            output += self.outputNetwork[i][0] * self.outputNetwork[i][1]


        return sigmoid(output)


# def evaluateState(self, currentState):
#         output = 1 * self.biasWeights[2]

#         for i in range(len(self.outputNetwork)):
#             output += self.outputNetwork[i][0] * self.outputNetwork[i][1]

#         return sigmoid(output)
    
def sigmoid(x):
        return (1/(1 + e**(-x)))
    
def backPropagation(self, currentState, error, output):
        # might change 1 later

        errorTerm = error * output * (1 - output)

        topError = errorTerm * self.outputNetwork[0][1]
        bottomError = errorTerm * self.outputNetwork[1][1]

        topErrorTerm = topError * self.outputNetwork[0][0] * ( 1 - self.outputNetwork[0][0] )
        bottomErrorTerm = bottomError * self.outputNetwork[1][0] * ( 1 - self.outputNetwork[1][0] )
        
        # # may need to fix last part in parens
        # for i in range(len(self.hiddenNetwork)):
        #     for j in range(len(1, self.hiddenNetwork)):
        #         # self.hiddenNetwork[i][j] += self.learningRate * topError * ( output * (1 - output) * self.outputNetwork[0][0] )
        #         self.hiddenNetwork[i][]

        for i in range(len(self.hiddenNetwork)):
            self.hiddenNetwork[i][1] += self.learningRate * topErrorTerm * self.hiddenNetwork[i][0]
        self.biasWeights[0] += self.learningRate * topErrorTerm * 1
        
        for j in range(len(self.hiddenNetwork)):
            self.hiddenNetwork[j][2] += self.learningRate * bottomErrorTerm * self.hiddenNetwork[j][0]
        self.biasWeights[1] += self.learningRate * bottomErrorTerm * 1
        
        for k in range(len(self.outputNetwork)):
            self.outputNetwork[k][1] += self.learningRate * errorTerm * self.outputNetwork[k][0]
        self.biasWeights[2] += self.learningRate * errorTerm * 1



def evalFinal(self, currentState):
        NN_util = getOutput(self, currentState)
        trainingUtil = (heuristicStepsToGoal(currentState))/100
        #error = NN_util - trainingUtil
        error = trainingUtil - NN_util
        print("Error is: " + str(error))

        if abs(error) < 0.03:
             printWeights(self)

        backPropagation(self, currentState, error, NN_util)
        
def printWeights(self):
        print("Weights for hidden network: ")
        for i in range(len(self.hiddenNetwork)):
            for j in range(1, len(self.hiddenNetwork[0])):
                print(str(self.hiddenNetwork[i][j]))

        print()
        
        print("Weights for output network: ")
        for k in range(len(self.outputNetwork)):
            for m in range(1, len(self.outputNetwork[0])):
                print(str(self.outputNetwork[k][m]))

        print()

        print("Bias weights: ")
        for h in range(len(self.biasWeights)):
            print(str(self.biasWeights[h]))

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
    