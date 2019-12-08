## Challenges 

The biggest challenge of Pacman game comes from the large state space and the unpredictable opponent's behavior. And these two characteristics largely constrain the performance of all the approaches implemented in our implementation.

The ultimate goal of reaching the winning state is merely clear, it has to be broke up into sub-goals, which makes agents focus on finding the optimal path for each sub-goal.  However, even the agent can reach all sub-goal optimally, the final result can hardly be optimal.

## Conclusions and Learnings

In this project, we implemented four AI approaches. The first two behaves obviously worse than Heuristic Search and Q-learning and hence don't make into the final submission but we have tagged the commit for reference purpose. 

For the submitted two agents, we ran 100 rounds of the game between them and observed the heuristic have the winning rate of 70.8% which makes it the best approach of the four.  

We replayed all the matches between the two and identified two reasons of why Q-learning agent cannot beat Heuristic Searching agent:

1. Q-learning agent is more conservative, as we have demoed in section 3, it goes back to its territory more often, however, the heuristic agent only go back when get chased. As long as the heuristic agent can put food it carried back in the end, it definitely can get a higher score than the Q-learning agent.

2. The heuristic agent is better at route planning, which makes it take less step to reach a food than Q-learning agent

By implementing different techniques learned in class, we found that while Monte Carlo Tree Search works for this project conceptually, the searching depth is hard to decide. If it's too large, not many simulations can be taken within the time limit and the rewards far away have little effect on the current behavior, if too small, the searching may get cut off before it reaches a goal which makes it act randomly.



[Previous Page](/3_approach_evolution) | [Back Home](/)