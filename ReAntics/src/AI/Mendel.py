import random
import sys
import math
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

BASE_FITNESS = 1.1 #Guarentees a fitness value of at least 0.1

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "GeneticAlg")
        self.popSize = 50 #Must be divisible by 2
        self.pop = [Gene(1) for _ in range(self.popSize)]
        self.popIdx = 0
        self.gameNum = 0
        self.totalGames = 20
        self.prevFood = [0, 0]
        self.totFood = [0, 0]
        self.numTurns = 1
        self.epochs = 1
        self.isFCalc = False

    def nextGen(self):        
        weights = [x for x in range(1, len(self.pop) + 1)]
        self.pop.sort(key=lambda x: x.fitness)

        print("PERFORMANCE")
        for i in range(0,len(self.pop)):
            print("FITNESS: ", self.pop[i].fitness, "SEQ: ", self.pop[i].seq);
        
        newPop = []
        for _ in range(math.floor(self.popSize/2)):
            newPop.extend(self.getBestGenes(weights))
        self.pop = newPop

    def getBestGenes(self, weights):
        parent1 = random.choices(self.pop, weights, k=1)[0]
        parent2 = random.choices(self.pop, weights, k=1)[0]
        gene1 = Gene(self.epochs, parent1, parent2)
        gene2 = Gene(self.epochs, parent2, parent1)
        #gene3 = Gene(self.epochs, parent1, parent2, True)
        #gene4 = Gene(self.epochs, parent2, parent1, True)
        return [gene1, gene2] #[gene1, gene2, gene3, gene4]
        
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            return self.pop[self.popIdx].seq[:11]
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            if not self.pop[self.popIdx].adjusted:
                self.pop[self.popIdx].adjustCollisions(currentState)
            return self.pop[self.popIdx].seq[11:]
        else:
            return [(0, 0)]
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        if not self.isFCalc:
            self.calcFitness(currentState)
            self.isFCalc = True
        
        moves = listAllLegalMoves(currentState)
        selectedMove = moves[random.randint(0,len(moves) - 1)];

        #don't do a build move if there are already 3+ ants
        numAnts = len(currentState.inventories[currentState.whoseTurn].ants)
        while (selectedMove.moveType == BUILD and numAnts >= 3):
            selectedMove = moves[random.randint(0,len(moves) - 1)];

        if selectedMove.moveType == END:
            self.numTurns += 1
            self.isFCalc = False
        return selectedMove
    
    def calcFitness(self, currentState):
        myInv = getCurrPlayerInventory(currentState)
        enInv = getEnemyInv(None, currentState)
        self.totFood[0] += max(myInv.foodCount - self.prevFood[0], 0)
        self.totFood[1] += max(enInv.foodCount - self.prevFood[1], 0)
        self.prevFood[0] = myInv.foodCount
        self.prevFood[1] = enInv.foodCount
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        if hasWon:
            self.pop[self.popIdx].fitness += 1 / self.totalGames
        self.pop[self.popIdx].fitness += self.getFitness()
        self.updateAttr()

    def updateAttr(self):
        self.prevFood = [0, 0]
        self.totFood = [0, 0]
        self.numTurns = 1
        self.isFCalc = False
        self.gameNum += 1

        if self.gameNum >= self.totalGames:
            self.gameNum = 0
            self.popIdx += 1

            if self.popIdx >= self.popSize:
                self.popIdx = 0
                self.nextGen()

                self.epochs += 1
                print("EPOCHS:", self.epochs)

    def getFitness(self):
        fitness = (10 * self.totFood[0] - self.totFood[1]) / self.numTurns
        return (BASE_FITNESS + fitness) / self.totalGames
                
class Gene:
    def __init__(self, generationNum, parent1=None, parent2=None, smartSplice=False):
        self.generationNum = generationNum
        self.foodCoords = [11, 12]
        self.fitness = 0
        self.adjusted = False
        self.mutationChance = 0.5
        
        if parent1 == None or parent2 == None:
            self.seq = [self.generateRandomCoords(i) for i in range(13)]
        else:
            if smartSplice:
                spliceIdx = self.foodCoords[0]
            else:
                spliceIdx = random.randint(0, len(parent1.seq) - 1)
            self.seq = parent1.seq[:spliceIdx] + parent2.seq[spliceIdx:]
            
        self.mutateSeq()
        self.adjustCollisions()

    def generateRandomCoords(self, idx):
        if idx in self.foodCoords:
            return (random.randint(0, 9), random.randint(6, 9))
        return (random.randint(0, 9), random.randint(0, 3))

    def mutateSeq(self):
        for idx, coord in enumerate(self.seq):
            if random.random() <= self.mutationChance / (self.generationNum):
                self.seq[idx] = self.generateRandomCoords(idx)
                
    def adjustCollisions(self, currentState=None):
        usedSpaces = []
        if (currentState is not None):
            grass = getConstrList(currentState, None, (GRASS,))
            constrs = getConstrList(currentState, 1 - currentState.whoseTurn,
                                   (ANTHILL, TUNNEL))
            usedSpaces.extend([g.coords for g in grass if g.coords[1] >= 6])
            usedSpaces.extend([c.coords for c in constrs])
        
        myUnusedSpaces = self.getUnusedSpaces(usedSpaces, 0, 3)
        enUnusedSpaces = self.getUnusedSpaces(usedSpaces, 6, 9)
        for idx, coord in enumerate(self.seq):
            if coord in usedSpaces:
                if idx in self.foodCoords:
                    randIdx = random.randint(0, len(enUnusedSpaces)-1)
                    coord = enUnusedSpaces[randIdx]
                    self.seq[idx] = coord
                    del enUnusedSpaces[randIdx]
                else:
                    randIdx = random.randint(0, len(myUnusedSpaces)-1)
                    coord = myUnusedSpaces[randIdx]
                    self.seq[idx] = coord
                    del myUnusedSpaces[randIdx]
            usedSpaces.append(coord)
            
    def getUnusedSpaces(self, usedSpaces, yMin, yMax):
        unusedSpaces = []
        for i in range(9):
            for j in range(yMin, yMax + 1):
                coord = (i, j)
                if coord not in usedSpaces and coord not in self.seq:
                    unusedSpaces.append(coord)
        return unusedSpaces
