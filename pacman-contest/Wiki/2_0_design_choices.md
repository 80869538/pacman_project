# Design Choices

Four approaches have been explored in our implementation. They are Monte Carlo Tree Search, Monte Carlo Simulation with Goal Recognition, Heuristic Search and Q-learning with approximation function. Among them, the first two don't show promising behaviour and hence we only list them in [3. Approach Evolution and Experiments](/3_approach_evolution) and discuss the last two approaches in more detail in the following contents of this section.

## General Comments

The first two approaches are based on a simple reward system which enables the agent to find food and avoid ghost along the way. The last two approaches are based on the same set of state variables. In the case of the heuristic search those variables are expressed in the form of heuristic while in Q-learning, they are features.

The final goal of the competition is to win the game, to achieve this, some sub-goals are formalized which are expressed as searching goals in the heuristic approach and rewards in Q-learning.

The overall performance of the agents mostly depends on the number of rewards or the complexity of the heuristic.
## Comments per topic

## Heuristic Search

Among the four implementations, heuristic search achieves the best winning rate. However, it takes the longest time to generate action for each step on average. Especially, when the heuristic is not efficient enough to run the searching tree, a large searching space will be generated. 

## Monte Carlo

While Monte Carlo Tree Search can give a simulation result no matter how long the time constraints are, the appropriate depth of the searching tree is hard to determine.

## Goal recognition
It is based on a simple assumption that the opponent will always try to minimize our agent's profit. However, this hypothesis not always hold in some specific situation.

## Q-learning

Q-learning with linear approximation function is faster and even better than the heuristic approach in terms of escaping from ghosts, collaborating between two Pacman and chasing invaders. 



[Back Home](/home) | [Next page](/2_1_approach)