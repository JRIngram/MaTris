MaTris
======

A clone of Tetris made using Pygame. Licensed under the GNU GPLv3. Works with both Python 2 and 3.

Run `python matris.py` to start the game.

Requires
========
Requires python 2.x or python 3.x


Requires pip: `sudo apt install python-pip` or `sudo apt install python3-pip`

Requires pygame: `sudo pip install pygame` or `sudo pip3 install pygame`

Demo
====
![Demo](demo.png)

Coveted by academia
========================
In 2013, my game [was used](http://eprints.ucm.es/22631/1/REMIRTA.pdf) by someone in Madrid to test "remote execution of multimedia interactive real-time applications". The next year, [a study in Denmark](https://www.academia.edu/6262472/Improving_game_experience_using_dynamic_difficulty_adjustment_based_on_physiological_signals) called "Improving game experience using dynamic diﬃculty adjustment" asked participants to "self-rate their valence and arousal [sic]" playing MaTris! Who would've thunk it? In 2016, people in Stanford [were using the game](http://cs231n.stanford.edu/reports/2016/pdfs/121_Report.pdf) to try out deep reinforcement learning, although apparently the result was not as "respectable" as it could've been. Not a problem in Korea, apparently, where students [are expected](http://nlp.chonbuk.ac.kr/AML/AML_assignment_2.pdf) to accomplish it! That stuff is way above my head, but perhaps my life will be spared during the singularity?

# Artificial Intelligence Extension
An artificial intelligence mode has been created. This mode is ran by default. To return to a manual game play mode, `agent_mode` in the class `Matris` in `matris.py` needs to be set to `False`.

The logic of this mostly resides in `agent.py` although modifcations have been made to `matris.py` to allow for the agent to interact with the game.

## Random Mode
Currently the `agent_mode` only causes the agent to randomly place blocks, with little intelligence. This will be built upon in future, but for now acts as a proof of concept in that it proves that tetromino placement can be controlled by an agent and valid placements can be found.

## agent.py
### board
This class acts as a representation of the current Tetris board and stores various stats about the board. This class is given to the agent so that the agent can interpret the game state.

### agent
This stores the current tetromino and a representation of the board. It then uses the information it has about the current game state to make a choice about where to place the current tetromino.

![agent.py UML Diagram](agent_uml.jpg)
