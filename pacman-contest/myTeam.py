# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent

import random,util
from game import Directions
import time
import math
from util import nearestPoint
from game import Actions
from game import Directions
import pickle
import sys
sys.path.append('teams/AIdiot/')

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'HeuristicAgent', second = 'HeuristicAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)


'''
Heuristic technology implementation
''' 
class HeuristicAgent(CaptureAgent):
 
  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    self.entrance = self.getEntrances(gameState)
    self.beenChased = False
    self.walls = gameState.getWalls()
    self.onDefence = False
    self.opponents = {}
    self.maxDepth = 1
    self.searchTree = {}
    self.isStuck = False
    for opponent in self.getOpponents(gameState):
      self.opponents[opponent] = {'position':None,'isPacman':False,'scaredTimmer':0}
    self.scaredTimer = 0
    self.isPacman = False
    
  
  def update(self,gameState):
    '''
    Update opponents' information including: 
    1. Whether they are pacman
    2. How long is the scaredTimer left
    3. Position (Guess if unobserveable)
    '''
    self.foodList = self.getFoodDistances(gameState)
    self.LegalActions = gameState.getLegalActions(self.index)
    self.LegalActions.remove('Stop')
    self.scaredTimer = gameState.getAgentState(self.index).scaredTimer
    self.isPacman = gameState.getAgentState(self.index).isPacman
    for opponent in self.getOpponents(gameState):
      
      opponentState = gameState.getAgentState(opponent)
      self.opponents[opponent]['isPacman'] = opponentState .isPacman
      self.opponents[opponent]['scaredTimmer'] = opponentState .scaredTimer
      
      #If the position of opponent can be observed
      if opponentState .getPosition() != None:
        self.opponents[opponent]['position'] =opponentState.getPosition()
        
      #If the opponent has eaten a food recently
      elif len(self.observationHistory) > 2 and self.numCarrying(self.getPreviousObservation(),opponent) <  self.numCarrying(self.getCurrentObservation(),opponent):
        previousFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
        currentFood = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
        self.opponents[opponent]['position'] = list(set(previousFood) - set(currentFood))[0]
        print("food been eaten by " + str(opponent))
    #determine whether to sitch to defence mode
    self.goDefence()
 
    
  def getEntrances(self,gameState):
    
    wallPosition = gameState.getWalls().asList()
    if self.red:
      middleLine = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
    else:
      middleLine = [((gameState.data.layout.width / 2) , y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
    
    
  def getDefenders(self,gameState):
    '''
    Get a list of defenders on opponent's board
    return empty list if there is none
    '''
    enemies=[gameState.getAgentState(opponent) for opponent in self.getOpponents(gameState)]
    defenders=[a for a in enemies if a.getPosition() != None and not a.isPacman]
    self.mostRecentDefenders = defenders
    return defenders
  
  def getFoodDistances(self, gameState):
    '''
    Return a list of distances representing the distance to each food
    we seek
    '''
    foods = [food for food in self.getFood(gameState).asList()]
    foodDistances = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), food) for food in foods] 
    return foodDistances
  
  def getCapsuleDistances(self,gameState):
    capsules = self.getCapsules(gameState)
    if len(capsules)==0:
      return []
    else:
      capsuleDistances = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), capsule) for capsule in capsules]
      return capsuleDistances

  def getSuccessor(self, gameState, action):

    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor
    
  def getTimeLeft(self, gameState):
      return gameState.data.timeleft
  
    
  def chooseAction(self, gameState):
    
    if self.getTimeLeft(gameState)/4 < min([self.getMazeDistance(gameState.getAgentPosition(self.index), food) for food in self.entrance]) +5 and self.numCarrying(gameState,self.index)>0:
      print('running out time')
      self.onDefence = True
      actions = self.aStarSearch(gameState,self.nearestEntrance,self.isGoalStateE)
      #in case no path finded
      if len(actions) == 0:
        return random.choice(self.LegalActions)
      return actions[0]
    
    actions = []

    self.update(gameState)
    foodLeft = len(self.foodList)
  
    if self.isStuck:
      actions = gameState.getLegalActions(self.index)
      actions.remove('Stop')
      return self.search(gameState,0.05)
   
    #Go defense mode if only two foods left, find path to the nearest entrance
    if foodLeft <= 2 and self.isPacman:
# =============================================================================
#       for action in actions:
#         successors.append(self.getSuccessor(gameState, action))
#       values = [self.evaluate(successor,0) for successor in successors]
#     
#       maxValue = max(values)
#       bestActions = [a for a, v in zip(actions, values) if v == maxValue]
#       return random.choice(bestActions)
# =============================================================================

      
      self.onDefence = True
      actions = self.aStarSearch(gameState,self.nearestEntrance,self.isGoalStateE)
      #in case no path finded
      if len(actions) == 0:
        return random.choice(self.LegalActions)
      return actions[0]
    
    #switch to food finding mode if been scared
    if self.scaredTimer > 4:
        if self.aStarSearch(gameState,self.nearestFoodHeuristic,self.isGoalStateAnyNearest):
          return self.aStarSearch(gameState,self.nearestFoodHeuristic,self.isGoalStateAnyNearest)[0]
    

    if not self.onDefence:
      
      #detect if been chased
      if len(self.getDefenders(gameState)) >0:
        for  opponent in self.opponents:
          if self.isChased(gameState,opponent) and self.isPacman:
            self.beenChased = True
      if not self.isPacman:
        self.beenChased = False
      for opponent in self.opponents:
        if self.opponents[opponent]['scaredTimmer'] > 4:
          self.beenChased = False

      if self.beenChased :
        print("someone chasing " + str(self.index))
        #if having capsule, go to capsule. go to entrance otherwise
        if len(self.getCapsules(gameState)) > 0:
          actions = self.aStarSearch(gameState,self.nearestCapsule,self.isGoalCapsule)
          return actions[0]
        print('Going for nearest Entrance')
        actions = self.aStarSearch(gameState,self.nearestEntrance,self.isGoalStateE)

      if len(actions) == 0:
        actions = self.aStarSearch(gameState,self.nearestFoodHeuristic,self.isGoalState)
      return actions[0]
    
    else:
      
      print(str(self.index) + " is on defence")
      #If invader detected, approaching invader
      for opponent in self.opponents:
        if self.opponents[opponent]['isPacman']:
          print("invader detected")
          actions = self.aStarSearch(gameState,self.nearestInvader,self.isGoalStateD)
          if actions and len(actions) > 0:
            return actions[0]
          else:
            print('Going for nearest my food')
            return self.aStarSearch(gameState,self.nearestMyFood,self.isGoalStateMyFood)[0]
      print('Going for anynearest  food')   
      return self.aStarSearch(gameState,self.nearestFoodHeuristic,self.isGoalStateAnyNearest)[0]

    
  def isGoalStateMyFood(self,state):
    if state in self.getFoodYouAreDefending(self.getCurrentObservation()).asList() and state != self.getCurrentObservation().getAgentPosition(self.index):
      return True
    return False
    
  def isGoalStateAnyNearest(self,state):
    if state in self.getFood(self.getCurrentObservation()).asList():
      return True
    return False
  
  def nearestMyFood(self,position):
    '''heuristic based the distance to the nearest food'''
    if self.isGoalStateMyFood(position):
      return 0
    foodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()  
    myPos = position
    minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])

    return minDistance
 
  
  def getSuccessors(self, state):
    """
    Returns successor states, the actions they require, and a cost of 1.
  
     As noted in search.py:
         For a given state, this should return a list of triples,
     (successor, action, stepCost), where 'successor' is a
     successor to the current state, 'action' is the action
     required to get there, and 'stepCost' is the incremental
     cost of expanding to that successor
    """
  
    successors = []
    for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
        gameState = self.getCurrentObservation()
        x,y = state
        dx, dy = Actions.directionToVector(action)
        nextx, nexty = int(x + dx), int(y + dy)
        cost = 1
        if not self.walls[nextx][nexty]:
            nextState = (nextx, nexty)
            if len(self.getDefenders(gameState)) > 0:
               for opponent in self.opponents:
                    if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] and self.getMazeDistance(self.opponents[opponent]['position'],nextState) <2   and self.opponents[opponent]['scaredTimmer']<5:
                      cost = 99999
            successors.append( ( nextState, action, cost) )
  

  
    return successors
  
  def getTeammates(self):
    t = []
    gameState = self.getCurrentObservation()
    for teammate in self.getTeam(gameState):
      if teammate != self.index:
        t.append(teammate)
    return t
  
  def isTargeted(self,food):
    '''
    return if other teamates have targetd the food
    '''
    gameState = self.getCurrentObservation()
    for t in self.getTeammates():
      if self.getMazeDistance(gameState.getAgentPosition(t), food) < self.getMazeDistance(gameState.getAgentPosition(self.index), food):
        return True
    return False
  
  def goDefence(self):
    if len(self.getFood(self.getCurrentObservation()).asList()) <=2 :
      self.onDefence = True
      return
    for food in self.getFood(self.getCurrentObservation()).asList():
      if not self.isTargeted(food):    
        self.onDefence = False
        return
    self.onDefence = True
   
    
  def isGoalState(self,state):
    allGhost = True
    for opponent in self.opponents:
      if self.opponents[opponent]['isPacman']:
        allGhost = False
    if allGhost and state in self.getFood(self.getCurrentObservation()).asList():
      return True
    
    if state in self.getFood(self.getCurrentObservation()).asList() and not self.isTargeted(state):
      return True
    
    return False
  
  def isGoalStateE(self,state):
    return state in self.entrance and state != self.getCurrentObservation().getAgentPosition(self.index)
  
  def isGoalStateD(self,state):
    for opponent in self.opponents:
      if self.opponents[opponent]['position']:
        if self.opponents[opponent]['position'] == state and self.opponents[opponent]['isPacman'] and  self.scaredTimer == 0:
          return True
    return False
  
  def nearestEntrance(self,position):
    
    myPos = position
    minDistance = min([self.getMazeDistance(myPos, food) for food in self.entrance])
    if self.isGoalStateE(position):
      return 0
    for opponent in self.opponents:
      if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] :
        if self.getMazeDistance(self.opponents[opponent]['position'],  position) < 3 and self.opponents[opponent]['scaredTimmer']<5:
          return 9999

    return minDistance
  def isGoalCapsule(self,state):
    gameState = self.getCurrentObservation()
    if state in self.getCapsules(gameState):
      return True
    return False
      
  def nearestCapsule(self,position):
    '''heuristic based the distance to the nearest food'''
    gameState = self.getCurrentObservation()
    foodList = self.getCapsules(gameState) 
    myPos = position
    if self.isGoalState(position):
      return 0
    minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
    for opponent in self.opponents:
      if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] :
        if self.getMazeDistance(self.opponents[opponent]['position'],  position) < 3 and self.opponents[opponent]['scaredTimmer']<5 and self.getMazeDistance(self.opponents[opponent]['position'],  position) < 2 * minDistance :
          return 99999
    return minDistance
  def nearestFoodHeuristic(self,position):
    '''heuristic based the distance to the nearest food'''

    if self.isGoalState(position):
      return 0
    minDistance = min(self.foodList)
    for opponent in self.opponents:
      if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] :
        if self.getMazeDistance(self.opponents[opponent]['position'],  position) < 3 and self.opponents[opponent]['scaredTimmer']<5 and self.getMazeDistance(self.opponents[opponent]['position'],  position) < 2 * minDistance :
          return 99999
    

    return minDistance
  
  def nearestInvader(self,position):
     gameState = self.getCurrentObservation()
     myPos = position
     if self.isGoalStateD(position):
      return 0
     d = []
     for opponent in self.opponents:
       if self.opponents[opponent]['isPacman']  :
         if not self.opponents[opponent]['position']:
           d.append(gameState.getAgentDistances()[opponent])
         else: 
           d.append(self.getMazeDistance(self.opponents[opponent]['position'],myPos))
     return min(d)
        
  def aStarSearch(self,gameState,heuristic,isGoalState):
    """Search the node that has the lowest combined cost and heuristic first."""

    start =self.getCurrentObservation().getAgentState(self.index).getPosition()
    queue = util.PriorityQueue()
    queue.push(start,heuristic(start))
    #dictionary prev for traceback purpose
    prev = {start: {"prev":None,"action":None,"fn":heuristic(start), "gn":0}}
    closed = [start]
    while not queue.isEmpty():
        current = queue.pop()
        closed.append(current)
        if isGoalState(current):
                    actions = []
                    while prev[current]["prev"]:
                        actions.append(prev[current]["action"])
                        current = prev[current]["prev"]
                    actions.reverse()
                    return actions       
        successors = self.getSuccessors(current)
        
        for successor in successors:
            if successor[0] not in closed:
                if successor[0] in prev and prev[current]["gn"]+successor[2] + \
                heuristic(successor[0])< prev[successor[0]]["fn"]:
                    prev[successor[0]] = {"prev":current, 
                                          "action":successor[1],
                                          "fn":prev[current]["gn"]+ successor[2] + heuristic(successor[0]),
                                          "gn":prev[current]["gn"]+ successor[2]}
                elif successor[0] not in prev:
                    prev[successor[0]] = {"prev":current, 
                                          "action":successor[1],
                                          "fn":prev[current]["gn"]+ successor[2] + heuristic(successor[0]),
                                          "gn":prev[current]["gn"]+ successor[2]}
                queue.update(successor[0],prev[successor[0]]["fn"])
 
  
  
  '''
  This section determine whether pacman is chased.
  '''
  def recent(self):
    '''Return the last three states'''
    if len(self.observationHistory) > 4:
      recent = self.observationHistory[-3:]
    return recent
  
  def numCarrying(self,gameState,index):
    '''return the number of food carried by an agent'''
    return gameState.getAgentState(index).numCarrying
      
  def isChased(self,gameState,oppoent):
    '''
    Determine wether the agent is chased by an enemy
    If an opponent have been following us over the last three states return True
    '''
    if not self.isPacman :
      return False
    if not gameState.getAgentState(oppoent).getPosition():
      return False
    history = self.recent()
    distance =[]
    
    
    for i in range(len(history)-1):
      
      myLastPosition = history[i].getAgentState(self.index).getPosition()
      chaserNewPosition = history[i+1].getAgentState(oppoent).getPosition()
      if not chaserNewPosition:
        return False
      
      #ignore the opponent if it's too far away
      if self.getMazeDistance(chaserNewPosition, myLastPosition) > 5:
        return False
      
      distance.append(self.getMazeDistance(chaserNewPosition, myLastPosition))
      
    #the opponent is getting closer
    if len(distance)!=2 or distance[0] < distance[1] :
      return False

    return True
  
  def evaluate(self, gameState,depth):
    features = self.getFeatures(gameState)
    weights = self.getWeights(gameState)
    return features * weights 
  
  def getFeatures(self, gameState):
    features = util.Counter()

    features['Score'] = self.getScore(gameState)
    # Compute distance to the nearest food
    myPos = gameState.getAgentState(self.index).getPosition()
    
     
    for opponent in self.opponents:
      if self.opponents[opponent]['position'] and not self.opponents[opponent]['isPacman']:
         if self.getMazeDistance(myPos,self.opponents[opponent]['position']) < 2:
           features['distanceToOpponent'] = 1
    if gameState.getAgentState(self.index).isPacman:
      minDistance = min([self.getMazeDistance(myPos, food) for food in self.entrance]) 
      features['distanceToEntrance'] =   minDistance
    
    for opponent in self.opponents:
      if self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position']:
        features['invaderDistance'] = self.getMazeDistance(myPos,self.opponents[opponent]['position'])
    return features

  def getWeights(self, gameState):
    return {'distanceToOpponent':-1000,'Score':100,'distanceToEntrance':-5,'invaderDistance': -10}
    
  
# =============================================================================
#   def simulation(self,gameState,depth):
#     if depth >1:
#       return 0
#     actions = gameState.getLegalActions(self.index)
#     actions.remove('Stop')
#     successors = []
#     for action in actions:
#       successors.append(self.getSuccessor(gameState, action))
#     values = [self.evaluate(successor,depth+1) for successor in successors]
#     maxValue = max(values)
#     return maxValue
#   
# =============================================================================
  
  
    
  def search(self,gameState,timeOut):
    
    timeElapse = 0
    start = time.time()
    while timeElapse < timeOut:
      
      
      self.simulate(gameState,0)
      
      end = time.time()
      timeElapse = end-start
   
   
    return self.selectNextAction(gameState)
  
  def simulate(self,gameState,depth):
    #print("simulate state at position " + str(gameState.getAgentPosition(self.index)) + " in depth" + str(depth) )
    
    if depth > self.maxDepth :
      return self.evaluate(gameState,0)
    leagalActions = gameState.getLegalActions(self.index)
    leagalActions.remove('Stop')
    
    if gameState not in self.searchTree:
      self.searchTree[gameState] = {"N":0,"actions":{}}
      for action in leagalActions :
        self.searchTree[gameState]["actions"][action] = {"N":0,"Q":0,"visited":False}
    
      return self.rollout(gameState,None,depth)

    bestAction = self.getUnexploredAction(gameState)

    if bestAction == None:
   
      bestAction = self.selectBestAction(gameState)
      
    next_state,reward = self.sample(gameState,bestAction)
    

   
    R = reward + 0.9 * self.simulate(next_state,depth+1) 
    
    self.searchTree[gameState]["N"] += 1
    self.searchTree[gameState]["actions"][bestAction]["N"] += 1
    self.searchTree[gameState]["actions"][bestAction]["Q"] += (R-self.searchTree[gameState]["actions"][bestAction]["Q"])/self.searchTree[gameState]["actions"][bestAction]["N"]
    self.searchTree[gameState]["actions"][bestAction]["visited"] = True
    return R
    
  def getUnexploredAction(self,state):
    for action in self.searchTree[state]["actions"]:
      if not self.searchTree[state]["actions"][action]["visited"]:
       
        return action
    return None
  
  def selectNextAction(self,state):
    maxQ = -math.inf
    
    for action in self.searchTree[state]["actions"]:
      if self.searchTree[state]["actions"][action]['Q'] > maxQ:
        maxQ = self.searchTree[state]["actions"][action]['Q']
        maxA = action
    print( self.searchTree[state]["actions"])

    Qsa = maxA

    return Qsa
  
  def selectBestAction(self,state):
    bestAction = None
    maxutc = -math.inf
    Ns = self.searchTree[state]["N"]
    #print(self.searchTree[state])
    for action in self.searchTree[state]["actions"]:
      
      Qsa = self.searchTree[state]["actions"][action]["Q"]
      Nsa = self.searchTree[state]["actions"][action]["N"]

      
      utc = Qsa + 1.5*(math.log2(Ns)/Nsa)**0.5
      
      if utc>maxutc:
        maxutc = utc
        bestAction = action
    return bestAction
  
  
  def isTerminal(self,gameState):


    for opponent in self.opponents:
      if opponent and gameState.getAgentPosition(self.index) == gameState.getAgentPosition(opponent):
        return True

    return False
  
  def rollout(self,gameState,pre_best,depth):
    
    if depth > self.maxDepth :
      return self.evaluate(gameState,0)
    bestAction = self.rolloutPolicy(gameState,pre_best)
    next_gameState, reward = self.sample(gameState,bestAction)
  

    R = reward + 0.9 * self.rollout(next_gameState,bestAction,depth+1)
    return R
  
  def rolloutPolicy(self, gameState,pre_best):
    actions = gameState.getLegalActions(self.index)
    actions.remove('Stop')
    
    if pre_best and pre_best in actions :
      actions.remove(Directions.REVERSE[pre_best])
    return random.choice(actions)
  

      
  def sample(self,gameState,action):
    next_gameState = gameState.generateSuccessor(self.index,action)

    return next_gameState,0
  
  

class QLearningAgent1(CaptureAgent):
 
  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    self.action_list = [Directions.STOP]
    self.epsilon = 0.05
    self.alpha = 0.01
    self.discountFactor = 0.8
    self.R = 0
    self.totalFood = len(self.getFood(gameState).asList())
    self.width = self.getFood(gameState).width
    self.height = self.getFood(gameState).height
    self.entrance = self.getEntrances(gameState)
    self.onDefence = False
    self.start = gameState.getAgentState(self.index).getPosition()
    self.opponents  = {}
    for opponent in self.getOpponents(gameState):
      self.opponents[opponent] = {'position':None,'isPacman':False,'scaredTimmer':0}
    self.allGhost = False
    
    for teammate in self.getTeam(gameState):
      if teammate != self.index:
        self.teammate = teammate
    
    self.notTargetedfood = []
    

    with open('weights1', "rb") as f:
     self.weights = pickle.load(f)
    
  def getEntrances(self,gameState):
    
    wallPosition = gameState.getWalls().asList()
    if self.red:
      middleLine = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
    else:
      middleLine = [((gameState.data.layout.width / 2) , y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
     
  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor
    
  def getQ(self, gameState, action):
    features = self.getFeatures(gameState, action)

    
    return features * self.weights
  
  def getMaxQ(self, gameState):
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    q = [self.getQ(gameState,action) for action in legalActions]
   
    return max(q)
  
  def getMaxA(self, gameState):
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    q = [(self.getQ(gameState,action),action) for action in legalActions]

    return max(q)[1]
  
  def recent(self):
    '''Return the last three states'''
    if len(self.observationHistory) > 4:
      recent = self.observationHistory[-3:]
    return recent
  
  def update(self,gameState):
    self.isPacman = gameState.getAgentState(self.index).isPacman
    
    allGhost = True
    
    for opponent in self.getOpponents(gameState):
      
      opponentState = gameState.getAgentState(opponent)
      self.opponents[opponent]['isPacman'] = opponentState .isPacman
      self.opponents[opponent]['scaredTimmer'] = opponentState .scaredTimer
      
      if opponentState .isPacman:
        allGhost = False
      #If the position of opponent can be observed
      
      if opponentState .getPosition() != None:
        self.opponents[opponent]['position'] =opponentState.getPosition()
        
      #If the opponent has eaten a food recently
      elif len(self.observationHistory) > 2 and self.numCarrying(self.getPreviousObservation(),opponent) <  self.numCarrying(self.getCurrentObservation(),opponent):
        previousFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
        currentFood = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
        self.opponents[opponent]['position'] = list(set(previousFood) - set(currentFood))[0]
        print("food been eaten by " + str(opponent))
      else:
        
        self.opponents[opponent]['position'] = None
        
    self.allGhost = allGhost

    
    if len(self.notTargetedfood) == 0:
      self.onDefence = True
     
  def updateWeights(self, gameState, action, nextState, reward):
    self.R +=  reward
    if self.getPreviousObservation() is None:
      return
    features = self.getFeatures(gameState, action)
    for feature in features:
      correction = ( reward + self.discountFactor*self.getMaxQ(nextState))-self.getQ(gameState, action)
      self.weights[feature] = self.weights[feature] + self.alpha*correction * features[feature]
      
  def final(self, gameState):
    print('weights after training: ' + str(self.weights))
    with open('weights1', "wb") as f:
       pickle.dump(self.weights,f)
    
    with open('R1', "rb") as f:
       R = pickle.load(f)
    R.append(self.R)
    with open('R1', "wb") as f:
       
       pickle.dump(R,f)
    print(R)
       
  def getPreviousAction(self):
    return self.action_list[-1]
  
  def nearestGhostDistance(self,gameState):
    
    distance = []
    myPos = gameState.getAgentState(self.index).getPosition()
    for opponent in self.opponents:
      
      if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] and self.opponents[opponent]['scaredTimmer'] < 5:
        distance.append(self.getMazeDistance(myPos, self.opponents[opponent]['position']))
    if len(distance) > 0:
      return min(distance)
    else:
      return None
    
  def nearestInvaderDistance(self,gameState):
    
    distance = []
    myPos = gameState.getAgentState(self.index).getPosition()
    for opponent in self.opponents:
      if self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position']:
        distance.append(self.getMazeDistance(myPos, self.opponents[opponent]['position']))
    if len(distance) > 0:
      return min(distance)
    else:
      return None
    
  def numCarrying(self,gameState,index):
    '''return the number of food carried by an agent'''
    return gameState.getAgentState(index).numCarrying
  
  def isChased(self,gameState,oppoent):
    '''
    Determine wether the agent is chased by an enemy
    If an opponent have been following us over the last three states return True
    '''
    if not self.isPacman :
      return False
    if not gameState.getAgentState(oppoent).getPosition():
      return False
    history = self.recent()
    distance =[]
    
    
    for i in range(len(history)-1):
      
      myLastPosition = history[i].getAgentState(self.index).getPosition()
      chaserNewPosition = history[i+1].getAgentState(oppoent).getPosition()
      if not chaserNewPosition:
        return False
      
      #ignore the opponent if it's too far away
      if self.getMazeDistance(chaserNewPosition, myLastPosition) > 6:
        return False
      
      distance.append(self.getMazeDistance(chaserNewPosition, myLastPosition))
      
    #the opponent is getting closer
    if len(distance)!=2 or distance[0] < distance[1] :
      return False
  
    return True
  
  
  def nearestEntrance(self,gameState):
    
    myPos = gameState.getAgentState(self.index).getPosition()
    minDistance = min([self.getMazeDistance(myPos, food) for food in self.entrance])
    return minDistance
  
  def isTargeted(self,food):
    '''
    return if other teamates have targetd the food
    '''
    gameState = self.getCurrentObservation()
    
    if self.getMazeDistance(gameState.getAgentPosition(self.teammate), food) < self.getMazeDistance(gameState.getAgentPosition(self.index), food):
      return True
    return False
  

    
  def updateFoodState(self):
    
    notTargetedfood = []
    foodList = self.getFood(self.getCurrentObservation()).asList()
    if len(foodList) <=2 :
      self.notTargetedfood = []
      return
    for food in foodList:
      if not self.isTargeted(food):
        notTargetedfood.append(food) 
      self.notTargetedfood = notTargetedfood
    
  
  def getRewards(self, gameState):
    
    if self.getPreviousObservation() is None:
      return 0
    reward = 0
    previousState = self.getPreviousObservation()
    previousFood = self.getFood(previousState).asList()
    myPosition = gameState.getAgentPosition(self.index)
    currentFood = self.getFood(gameState).asList()
    
    if myPosition in previousFood and myPosition not in currentFood:
      reward = 2
      print("agent eat food")
      

    if self.getScore(gameState) >  self.getScore(previousState):
      reward =  (self.getScore(previousState) - self.getScore(gameState)) *2
  
    for opponent in self.opponents:
     if previousState.getAgentPosition(opponent):
      if not self.opponents[opponent]['isPacman'] and self.getMazeDistance(myPosition,self.start) < 4 and self.getMazeDistance(previousState.getAgentPosition(self.index), previousState.getAgentPosition(opponent))<2:
        reward = -self.numCarrying(previousState,self.index) * 5 -10
        print("agent been eaten")
      elif previousState.getAgentState(opponent).isPacman and not gameState.getAgentState(opponent).isPacman and myPosition == previousState.getAgentPosition(opponent):
        reward = 30
        print("eat agent")
    

    
    return reward
 
  def getFeatures(self, gameState, action):
    
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    
    currentFoodList =  self.getFood(gameState).asList()
    
    if successor.getAgentPosition(self.index) in currentFoodList :
      features['foodLeft'] = 1
    
    if len(currentFoodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()

      minDistance = min([self.getMazeDistance(myPos, food) for food in currentFoodList])
        
      features['distanceToFood'] = -minDistance/(self.width*self.height)
    
    ghostDis = self.nearestGhostDistance(successor)
    
    if ghostDis :

      features['distanceToGhost'] = ghostDis/(self.width*self.height)
      
    invaderDis = self.nearestInvaderDistance(successor)
    if invaderDis:
 
      features['distanceToInvader'] = -invaderDis/(self.width*self.height)

    entranceDis = self.nearestEntrance(successor)
    if self.beenChased or self.foodLeft <= 2 :
      features['foodLeft'] = 0
      features['distanceToFood'] = 0
      
      if len(self.getCapsules(gameState))!=0 and gameState.getAgentState(self.index).isPacman:
        entranceDis = min([self.getMazeDistance(successor.getAgentState(self.index).getPosition(), capsule) for capsule in self.getCapsules(gameState)])
      features['distanceToEntrance'] = -entranceDis/(self.width*self.height)
      
      if invaderDis:
 
        features['distanceToInvader'] = -invaderDis/(self.width*self.height)
    features['bias'] = 1
      

    

   

    
    
    
    
      
    
    features.divideAll(10.0)

    return features
  

 
  def chooseAction(self,gameState):
    
    self.foodLeft = len(self.getFood(gameState).asList())
    
    self.update(gameState)

    for  opponent in self.opponents:
      if self.isChased(gameState,opponent) and self.isPacman:
        self.beenChased = True
        
    if not self.isPacman:
      self.beenChased = False
      
    for opponent in self.opponents:
      if self.opponents[opponent]['scaredTimmer'] > 4:
        self.beenChased = False
    if self.beenChased:
      print("someone chasing " + str(self.index))
      
    previousState = self.getPreviousObservation()
    previousAction = self.getPreviousAction()
    reward = self.getRewards(gameState)
    self.updateWeights(previousState, previousAction, gameState, reward)
    
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    if random.random()<self.epsilon:
      action = random.choice(legalActions)
    else:
      action = self.getMaxA(gameState)
      
    self.action_list.append(action)
    return action
  
  
class QLearningAgent2(CaptureAgent):
 
  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    self.action_list = [Directions.STOP]
    self.epsilon = 0.05
    self.alpha = 0.01
    self.discountFactor = 0.8
    self.R = 0
    self.start = gameState.getAgentState(self.index).getPosition()
    self.totalFood = len(self.getFood(gameState).asList())
    self.width = self.getFood(gameState).width
    self.height = self.getFood(gameState).height
    self.entrance = self.getEntrances(gameState)
    self.onDefence = False
    
    self.opponents  = {}
    for opponent in self.getOpponents(gameState):
      self.opponents[opponent] = {'position':None,'isPacman':False,'scaredTimmer':0}
    self.allGhost = False
    
    for teammate in self.getTeam(gameState):
      if teammate != self.index:
        self.teammate = teammate
    
    self.notTargetedfood = []
    

    with open('weights2', "rb") as f:
     self.weights = pickle.load(f)
    
  def getEntrances(self,gameState):
    
    wallPosition = gameState.getWalls().asList()
    if self.red:
      middleLine = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
    else:
      middleLine = [((gameState.data.layout.width / 2) , y) for y in range(0, gameState.data.layout.height)]
      return [entrance for entrance in middleLine if entrance not in wallPosition]
     
  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor
    
  def getQ(self, gameState, action):
    features = self.getFeatures(gameState, action)

    
    return features * self.weights
  
  def getMaxQ(self, gameState):
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    q = [self.getQ(gameState,action) for action in legalActions]
   
    return max(q)
  
  def getMaxA(self, gameState):
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    q = [(self.getQ(gameState,action),action) for action in legalActions]

    return max(q)[1]
  
  def recent(self):
    '''Return the last three states'''
    if len(self.observationHistory) > 4:
      recent = self.observationHistory[-3:]
    return recent
  
  def update(self,gameState):
    self.isPacman = gameState.getAgentState(self.index).isPacman
    
    allGhost = True
    
    for opponent in self.getOpponents(gameState):
      
      opponentState = gameState.getAgentState(opponent)
      self.opponents[opponent]['isPacman'] = opponentState .isPacman
      self.opponents[opponent]['scaredTimmer'] = opponentState .scaredTimer
      
      if opponentState .isPacman:
        allGhost = False
      #If the position of opponent can be observed
      
      if opponentState .getPosition() != None:
        self.opponents[opponent]['position'] =opponentState.getPosition()
        
      #If the opponent has eaten a food recently
      elif len(self.observationHistory) > 2 and self.numCarrying(self.getPreviousObservation(),opponent) <  self.numCarrying(self.getCurrentObservation(),opponent):
        previousFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
        currentFood = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
        self.opponents[opponent]['position'] = list(set(previousFood) - set(currentFood))[0]
        print("food been eaten by " + str(opponent))
      else:
        
        self.opponents[opponent]['position'] = None
        
    self.allGhost = allGhost
    self.updateFoodState()
    
    if len(self.notTargetedfood) == 0:
      self.onDefence = True
     
  def updateWeights(self, gameState, action, nextState, reward):
    self.R += reward
    if self.getPreviousObservation() is None:
      return
    features = self.getFeatures(gameState, action)
    for feature in features:
      correction = ( reward + self.discountFactor*self.getMaxQ(nextState))-self.getQ(gameState, action)
      self.weights[feature] = self.weights[feature] + self.alpha*correction * features[feature]
    
      
  def final(self, gameState):
    print('weights after training: ' + str(self.weights))
    with open('weights2', "wb") as f:
       pickle.dump(self.weights,f)
    with open('R2', "rb") as f:
       R = pickle.load(f)
    R.append(self.R)
    with open('R2', "wb") as f:
       pickle.dump(R,f)
    print(R)
       
  def getPreviousAction(self):
    return self.action_list[-1]
  
  def nearestGhostDistance(self,gameState):
    
    distance = []
    myPos = gameState.getAgentState(self.index).getPosition()
    for opponent in self.opponents:
      
      if not self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position'] and self.opponents[opponent]['scaredTimmer'] < 5:
        distance.append(self.getMazeDistance(myPos, self.opponents[opponent]['position']))
    if len(distance) > 0:
      return min(distance)
    else:
      return None
    
  def nearestInvaderDistance(self,gameState):
    
    distance = []
    myPos = gameState.getAgentState(self.index).getPosition()
    for opponent in self.opponents:
      if self.opponents[opponent]['isPacman'] and self.opponents[opponent]['position']:
        distance.append(self.getMazeDistance(myPos, self.opponents[opponent]['position']))
    if len(distance) > 0:
      return min(distance)
    else:
      return None
    
  def numCarrying(self,gameState,index):
    '''return the number of food carried by an agent'''
    return gameState.getAgentState(index).numCarrying
  
  def isChased(self,gameState,oppoent):
    '''
    Determine wether the agent is chased by an enemy
    If an opponent have been following us over the last three states return True
    '''
    if not self.isPacman :
      return False
    if not gameState.getAgentState(oppoent).getPosition():
      return False
    history = self.recent()
    distance =[]
    
    
    for i in range(len(history)-1):
      
      myLastPosition = history[i].getAgentState(self.index).getPosition()
      chaserNewPosition = history[i+1].getAgentState(oppoent).getPosition()
      if not chaserNewPosition:
        return False
      
      #ignore the opponent if it's too far away
      if self.getMazeDistance(chaserNewPosition, myLastPosition) > 6:
        return False
      
      distance.append(self.getMazeDistance(chaserNewPosition, myLastPosition))
      
    #the opponent is getting closer
    if len(distance)!=2 or distance[0] < distance[1] :
      return False
  
    return True
  
  
  def nearestEntrance(self,gameState):
    
    myPos = gameState.getAgentState(self.index).getPosition()
    minDistance = min([self.getMazeDistance(myPos, food) for food in self.entrance])
    return minDistance
  
  def isTargeted(self,food):
    '''
    return if other teamates have targetd the food
    '''
    gameState = self.getCurrentObservation()
    
    if self.getMazeDistance(gameState.getAgentPosition(self.teammate), food) < self.getMazeDistance(gameState.getAgentPosition(self.index), food):
      return True
    return False
  

    
  def updateFoodState(self):
    
    notTargetedfood = []
    foodList = self.getFood(self.getCurrentObservation()).asList()
    if len(foodList) <=2 :
      self.notTargetedfood = []
      return
    for food in foodList:
      if not self.isTargeted(food):
        notTargetedfood.append(food) 
      self.notTargetedfood = notTargetedfood
    
  
  def getRewards(self, gameState):
    
    if self.getPreviousObservation() is None:
      return 0
    reward = 0
    previousState = self.getPreviousObservation()
    previousFood = self.getFood(previousState).asList()
    myPosition = gameState.getAgentPosition(self.index)
    currentFood = self.getFood(gameState).asList()
    
    if myPosition in previousFood and myPosition not in currentFood:
      reward = 5
      print("agent eat food")
      

    if self.getScore(gameState) >  self.getScore(previousState):
      reward =  (self.getScore(previousState) - self.getScore(gameState)) *2
  
    for opponent in self.opponents:
      if previousState.getAgentPosition(opponent):
        if not self.opponents[opponent]['isPacman'] and self.getMazeDistance(myPosition,self.start) < 4 and self.getMazeDistance(previousState.getAgentPosition(self.index), previousState.getAgentPosition(opponent))<2:
          reward = -self.numCarrying(previousState,self.index) * 10 -30
          print("agent been eaten")
      elif previousState.getAgentState(opponent).isPacman and not gameState.getAgentState(opponent).isPacman and myPosition == previousState.getAgentPosition(opponent):
        reward = 30
        print("eat agent")
    
    return reward
 
  def getFeatures(self, gameState, action):
    
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    currentFoodList =  self.getFood(gameState).asList()
    
    if successor.getAgentPosition(self.index) in currentFoodList :
      features['foodLeft'] = 1
    
    if len(currentFoodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      if len(self.notTargetedfood) >0:
        minDistance = min([self.getMazeDistance(myPos, food) for food in self.notTargetedfood])
      else:
        minDistance = min([self.getMazeDistance(myPos, food) for food in currentFoodList])
        
      features['distanceToFood'] =- minDistance/(self.width*self.height)
    
    ghostDis = self.nearestGhostDistance(successor)
    
    if ghostDis  :

      features['distanceToGhost'] = ghostDis/(self.width*self.height)
      
    invaderDis = self.nearestInvaderDistance(successor)
    if invaderDis:
 
      features['distanceToInvader'] = -invaderDis/(self.width*self.height)

    entranceDis = self.nearestEntrance(successor)
    if self.beenChased or self.foodLeft <= 2 :
      features['foodLeft'] = 0
      features['distanceToFood'] = 0
      
      if len(self.getCapsules(gameState))!=0 and gameState.getAgentState(self.index).isPacman:
        entranceDis = min([self.getMazeDistance(successor.getAgentState(self.index).getPosition(), capsule) for capsule in self.getCapsules(gameState)])
      features['distanceToEntrance'] = -entranceDis/(self.width*self.height)
      
      if invaderDis:
 
        features['distanceToInvader'] = -invaderDis/(self.width*self.height)
    features['bias'] = 1
    
    features.divideAll(10.0)
    return features
  

 
  def chooseAction(self,gameState):
    
    self.foodLeft = len(self.getFood(gameState).asList())
    
    self.update(gameState)

    for  opponent in self.opponents:
      if self.isChased(gameState,opponent) and self.isPacman:
        self.beenChased = True
        
    if not self.isPacman:
      self.beenChased = False
      
    for opponent in self.opponents:
      if self.opponents[opponent]['scaredTimmer'] > 4:
        self.beenChased = False
    if self.beenChased:
      print("someone chasing " + str(self.index))
      
    previousState = self.getPreviousObservation()
    previousAction = self.getPreviousAction()
    reward = self.getRewards(gameState)
    self.updateWeights(previousState, previousAction, gameState, reward)
    
    legalActions = gameState.getLegalActions(self.index)
    legalActions.remove('Stop')
    if random.random()<self.epsilon:
      action = random.choice(legalActions)
    else:
      action = self.getMaxA(gameState)
      
    self.action_list.append(action)
    return action
 
 
  

    
  
