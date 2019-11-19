# feeding-frenzy
object-oriented programming, bloons tower defense type of game


To use Web UI, run python3 server.py and use your web browser to navigate to localhost:8000. 
If you make changes restart server.py to reload your code.


To place a zookeeper select the zookeeper type you want by clicking and then click on the board to place the zookeeper. You cannot have the zookeeper overlap with any other zookeepers, rocks or parts of the path. Then click again on the board to choose the direction of aim your zookeeper will throw food. 

If an animal is fed it and the food it was fed will be removed. A food can feed multiple animals if it overlaps with multiple animals. Multiple foods can feed a single animal and will all disapear if an animal overlaps with multiple foods in a given timestep of the game.

Different types of zookeepers have different prices, throw speeds and throw intervals:

|                 | Price | Throw Interval | Throw Speed |
| :-------------- |:-----:|:--------------:| :----------:|
Speedy Zookeeper: |   9   |       55       |     20      |
Thrifty Zookeeper:|   7   |       45       |      7      |
Cheery Zookeeper: |  10   |       35       |      2      |


Happy feeding!
