"""6.009 Fall 2019 Lab 9 -- 6.009 Zoo"""

from math import acos
# NO OTHER IMPORTS ALLOWED!

class Constants:
    """
    A collection of game-specific constants.

    You can experiment with tweaking these constants, but
    remember to revert the changes when running the test suite!
    """
    # width and height of keepers
    KEEPER_WIDTH = 30
    KEEPER_HEIGHT = 30

    # width and height of animals
    ANIMAL_WIDTH = 30
    ANIMAL_HEIGHT = 30

    # width and height of food
    FOOD_WIDTH = 10
    FOOD_HEIGHT = 10

    # width and height of rocks
    ROCK_WIDTH = 50
    ROCK_HEIGHT = 50

    # thickness of the path
    PATH_THICKNESS = 30

    TEXTURES = {
        'rock': '1f5ff',
        'animal': '1f418',
        'SpeedyZookeeper': '1f472',
        'ThriftyZookeeper': '1f46e',
        'CheeryZookeeper': '1f477',
        'food': '1f34e'
    }

    FORMATION_INFO = {'SpeedyZookeeper':
                       {'price': 9,
                        'interval': 55,
                        'throw_speed_mag': 20},
                      'ThriftyZookeeper':
                       {'price': 7,
                        'interval': 45,
                        'throw_speed_mag': 7},
                      'CheeryZookeeper':
                       {'price': 10,
                        'interval': 35,
                        'throw_speed_mag': 2}}

class NotEnoughMoneyError(Exception):
    """A custom exception to be used when insufficient funds are available
    to hire new zookeepers. You may leave this class as is."""
    pass

################################################################################
################################################################################

class Game:
    def __init__(self, game_info):
        """Initializes the game.

        `game_info` is a dictionary formatted in the following manner:
          { 'width': The width of the game grid, in an integer (i.e. number of pixels).
            'height': The height of the game grid, in an integer (i.e. number of pixels).
            'rocks': The set of tuple rock coordinates.
            'path_corners': An ordered list of coordinate tuples. The first
                            coordinate is the starting point of the path, the
                            last point is the end point (both of which lie on
                            the edges of the gameboard), and the other points
                            are corner ("turning") points on the path.
            'money': The money balance with which the player begins.
            'spawn_interval': The interval (in timesteps) for spawning animals
                              to the game.
            'animal_speed': The magnitude of the speed at which the animals move
                            along the path, in units of grid distance traversed
                            per timestep.
            'num_allowed_unfed': The number of animals allowed to finish the
                                 path unfed before the player loses.
          }
        """
        self.width = game_info["width"]
        self.height = game_info["height"]
        self.rocks = set() # set of rock objects
        self.path_corners = set(game_info["path_corners"]) # set of coordinate tuples
        self.money = game_info["money"]
        self.spawn_interval = game_info["spawn_interval"]
        self.spawn_counter = 0
        self.animal_speed = game_info["animal_speed"]
        self.num_allowed_remaining = game_info["num_allowed_unfed"]
        self.status = 'ongoing'
        self.end = game_info["path_corners"][-1]
        self.start = game_info["path_corners"][0]
        for rock in game_info["rocks"]: # add every rock's border
            self.rocks.add(Rock(rock)) # creates rock object and adds
        self.occupied_spaces = self.rocks.copy() # set of forms: rocks, zookeepers and path segments = cannot place things here
        for n in range(0, len(game_info["path_corners"])-1): # add paths to occupied space
            corner_one = game_info["path_corners"][n]
            corner_two = game_info["path_corners"][n+1]
            if abs(corner_one[0]-corner_two[0]) > abs(corner_one[1]-corner_two[1]): # horizontal path segment
                center_x = corner_one[0] + ((corner_two[0]-corner_one[0])//2)
                center_y = corner_one[1]
                path_w = abs(corner_one[0]-corner_two[0]) + Constants.PATH_THICKNESS
                path_h = Constants.PATH_THICKNESS
            else: # vertical path segment
                center_x = corner_one[0]
                center_y = corner_one[1] + ((corner_two[1]-corner_one[1])//2)
                path_w = Constants.PATH_THICKNESS
                path_h = abs(corner_one[1]-corner_two[1]) + Constants.PATH_THICKNESS
            self.occupied_spaces.add(Path_Segment((center_x, center_y), path_w, path_h))
        self.path = {} # dictionary of every coordinate in path for game mapped to direction it moves in 
        last_movement = 'end'
        for n in range(len(game_info["path_corners"])-1, 0, -1): 
            corner_one = game_info["path_corners"][n-1]
            corner_two = game_info["path_corners"][n]
            if abs(corner_one[0]-corner_two[0]) > abs(corner_one[1]-corner_two[1]): # horizontal path segment
                if corner_one[0]<corner_two[0]: # right moving segment
                    movement = 'right'
                else: # left moving segment
                    movement = 'left'
            else: # vertical path segment
                if corner_one[1]<corner_two[1]: # down moving segment
                    movement = 'down'
                else: # up moving segment
                    movement = 'up'
            self.path[corner_two] = last_movement
            last_movement = movement
            if n == 1: # start corner = corner_one
                self.path[corner_one] = movement
        self.animals = set() # set of animal objects in the game
        self.zookeepers = set() # set of Zookeeper objects in the game
        self.active_food = set() # set of food objects in the game
        self.current_zookeeper_type = None
        
    def render(self):
        """Renders the game in a form that can be parsed by the UI.

        Returns a dictionary of the following form:
          { 'formations': A list of dictionaries in any order, each one
                          representing a formation. The list should contain 
                          the formations of all animals, zookeepers, rocks, 
                          and food. Each dictionary has the key/value pairs:
                             'loc': (x, y), 
                             'texture': texture, 
                             'size': (width, height)
                          where `(x, y)` is the center coordinate of the 
                          formation, `texture` is its texture, and `width` 
                          and `height` are its dimensions. Zookeeper
                          formations have an additional key, 'aim_dir',
                          which is None if the keeper has not been aimed, or a 
                          tuple `(aim_x, aim_y)` representing a unit vector 
                          pointing in the aimed direction.
            'money': The amount of money the player has available.
            'status': The current state of the game which can be 'ongoing' or 'defeat'.
            'num_allowed_remaining': The number of animals which are still
                                     allowed to exit the board before the game
                                     status is `'defeat'`.
          }
        """
        d = {}
        formations = [form.render_form() for form in self.rocks] + [form.render_form() for form in self.animals] + [form.render_form() for form in self.active_food] + [form.render_form() for form in self.zookeepers]
        d['formations'] = formations
        d['money'] = self.money
        d['status'] = self.status
        d['num_allowed_remaining'] = self.num_allowed_remaining
        return d

    def timestep(self, mouse=None):
        """Simulates the evolution of the game by one timestep.

        In this order:
            (0. Do not take any action if the player is already defeated.)
            1. Compute any changes in formation locations, then remove any
                off-board formations.
            2. Handle any food-animal collisions, and remove the fed animals
                and eaten food.
            3. Throw new food if possible.
            4. Spawn a new animal from the path's start if needed.
            5. Handle mouse input, which is the integer coordinate of a player's
               click, the string label of a particular zookeeper type, or `None`.
            6. Redeem one unit money per animal fed this timestep.
            7. Check for the losing condition to update the game status if needed.
        """
    # 0 Do not take any action if the player is already defeated.
        if self.status != 'defeat':
        # 1 Compute any changes in formation locations, then remove any off-board formations.
            off_animals = set()
            for animal in self.animals: # moving all animals
                animal_loc = animal.move_animal(self.path_corners, self.path, self.end)
                if animal_loc == None:
                    off_animals.add(animal)
            for removed_animal in off_animals:
                self.num_allowed_remaining -= 1
                self.animals.remove(removed_animal) # remove off board animal
            off_food = set()
            for food in self.active_food: # moving all food in game
                if food.move_food(self.width, self.height): # if off board remove formation
                    off_food.add(food)
            for removed_food in off_food:    
                self.active_food.remove(removed_food)
        # 2 Handle any food-animal collisions, and remove the fed animals and eaten food.
            used_food = set()
            fed_animals = set()
            money_earned = 0
            for animal in self.animals:
                for food in self.active_food:
                    if animal.check_overlap(food.loc, food.size): # return True if overlapping
                        money_earned += 1
                        used_food.add(food)
                        fed_animals.add(animal)
            self.active_food = self.active_food.difference(used_food)   # get rid of eaten food  -= used_food
            self.animals = self.animals.difference(fed_animals) # get rid of fed animals  -= fed_animals
        # 3 Throw new food if possible.
            for zookeeper in self.zookeepers:
                if zookeeper.current_interval%zookeeper.interval == 0: # shoot time!
                    if zookeeper.aim_dir != None: # has been aimed
                        for animal in self.animals:
                            if zookeeper.check_line_of_sight(animal.make_border()):
                                self.active_food.add(Food(zookeeper.loc, zookeeper.aim_dir, zookeeper.throw_speed_mag))
                                break
                zookeeper.current_interval += 1 # increments 1 for every zookeeper each timestep
        # 4 Spawn a new animal from the path's start if needed.
            if self.spawn_counter%self.spawn_interval == 0: # spawn time!
                new_spawn = Animal(self.start, self.path[self.start], self.animal_speed)
                self.animals.add(new_spawn)
            self.spawn_counter += 1 # update counter always
        # 5 Handle mouse input, which is the integer coordinate of a player's click, the string label of a particular zookeeper type, or `None`.
            # assigning zookeeper type:
            if type(self.current_zookeeper_type) == type(None) or type(self.current_zookeeper_type) == str: # deals with indecisive players
                if type(mouse) == str: # actively clicking on zookeeper type
                    self.current_zookeeper_type = mouse
            # assigning zookeeper placement, check $, check if location is valid, 
            if type(self.current_zookeeper_type) == str:
                if type(mouse) == tuple: # actively clicking on board, choosing placement
                # previously selected zookeeper and is now placing them
                    if Constants.FORMATION_INFO[self.current_zookeeper_type]['price'] <= self.money: # check if player has enough money
                        # has enough proceed:
                        not_overlapping = True
                        for form in self.occupied_spaces:
                            if form.check_overlap(mouse, (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT)):
                                not_overlapping = False
                        if not_overlapping: # valid placement
                            # make Zookeeper object, assign to current_zookeeper_type
                            self.money -= Constants.FORMATION_INFO[self.current_zookeeper_type]['price'] # decrease money because of purchase
                            self.current_zookeeper_type = Zookeeper(mouse, self.current_zookeeper_type) # make zookeeper object
                            self.occupied_spaces.add(self.current_zookeeper_type) # add zookeeper  to occupied spaces
                            self.zookeepers.add(self.current_zookeeper_type) # add to set of zookeepers
                        else: pass # invalid placement   
                    else: raise NotEnoughMoneyError # not enough money
            # previously placed zookeeper, now choosing aim direction
            elif type(self.current_zookeeper_type) is Zookeeper: 
                if type(mouse) == tuple: # actively clicking on board, choosing aim direction
            # You should ignore the click if it is at the exact coordinate of that zookeeper
                    if mouse != self.current_zookeeper_type.loc: # not coordinate of that zookeeper so assign aim direction
                        a,b = self.current_zookeeper_type.loc
                        c,d = mouse
                        self.current_zookeeper_type.aim_dir = ((c-a)/(((c-a)**2+(d-b)**2)**0.5),(d-b)/(((c-a)**2+(d-b)**2)**0.5))
                        # making throw line once!
                        x, y = self.current_zookeeper_type.loc
                        v_x, v_y = self.current_zookeeper_type.aim_dir
                        throw_line = set()
                        for i in range(1,int(1+(self.width**2+self.height**2)**0.5)): # longest possible throw on any given graph
                            throw_line.add((int(x+v_x*i), int(y+v_y*i)))
                        self.current_zookeeper_type.throw_line = throw_line
                        self.current_zookeeper_type = None
                    else: pass # ignore the click if it is at the exact coordinate of that zookeeper.
        # 6 Redeem one unit money per animal fed this timestep.
            self.money += money_earned
        # 7 Check for the losing condition to update the game status if needed.
            if self.num_allowed_remaining < 0: # lost game, defeated
                self.status = 'defeat'
################################################################################
################################################################################

class Formation:
    def __init__(self, loc, texture, size):
        self.loc = loc # (x, y)
        self.texture = texture # texture
        self.size = size # (width, height)

    def render_form(self):
        return {'loc': self.loc, 'texture': self.texture, 'size': self.size}

    def check_overlap(self, loc2, size2): # Shared edges and corners do not count as intersections.
        loc1 = self.loc
        size1 = self.size
        x1 = loc1[0]
        y1 = loc1[1]
        w1 = size1[0]//2
        h1 = size1[1]//2
        x2 = loc2[0]
        y2 = loc2[1]
        w2 = size2[0]//2
        h2 = size2[1]//2
        if (max(x1,x2)-min(x1,x2)<w1+w2) and (max(y1,y2)-min(y1,y2)<h1+h2): # overlapping
            return True
        else: return False # if not overlapping

class Path_Segment(Formation):
    def __init__(self, loc, w, h):
        super().__init__(loc, None, (w, h))

class Zookeeper(Formation):
    def __init__(self, loc, zookeeper_type):
        super().__init__(loc, Constants.TEXTURES[zookeeper_type], (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT))
        self.aim_dir = None # None if the keeper has not been aimed, or a tuple `(aim_x, aim_y)` representing a unit vector pointing in the aimed direction.
        self.interval = Constants.FORMATION_INFO[zookeeper_type]['interval'] 
        self.throw_speed_mag = Constants.FORMATION_INFO[zookeeper_type]['throw_speed_mag'] 
        self.current_interval = 0
        self.throw_line = None

    def render_form(self):
        return {'loc': self.loc, 'texture': self.texture, 'size': self.size, 'aim_dir': self.aim_dir}

    def check_line_of_sight(self, animal_border): # returns True if in line of sight, False otherwise
        if len(self.throw_line.intersection(animal_border)) != 0: # intersection found!
            return True
        else: 
            return False # not intersecting animal

class Rock(Formation):
    def __init__(self, loc):
        super().__init__(loc, Constants.TEXTURES['rock'], (Constants.ROCK_WIDTH, Constants.ROCK_HEIGHT))

class Food(Formation):
    def __init__(self, loc, aim_direction, speed):
        super().__init__(loc, Constants.TEXTURES['food'], (Constants.FOOD_WIDTH, Constants.FOOD_HEIGHT))
        self.aim_dir = aim_direction
        self.speed = speed
    
    def move_food(self, w, h): # updates self.loc, returns True if off board, False if still on board
        x, y = self.loc
        v_x, v_y = self.aim_dir
        self.loc = (x+v_x*self.speed, y+v_y*self.speed)
        if self.loc[0]<0 or self.loc[1]<0 or self.loc[0]>w or self.loc[1]>h: # off board
            return True
        else: return False

class Animal(Formation):
    def __init__(self, loc, direction, animal_speed):
        super().__init__(loc, Constants.TEXTURES['animal'], (Constants.ANIMAL_WIDTH, Constants.ANIMAL_HEIGHT))
        self.direction = direction     
        self.speed = animal_speed
        self.moves = animal_speed

    def move_animal(self, path_corners, path, end):
        while self.moves > 0: # still moves to be made
            if self.loc == end: # done, off board
                self.loc = None
                self.moves = 0
                break 
            x, y = self.loc
            if self.direction == 'right':
                potential_loc = (x+1,y)
            elif self.direction == 'left':
                potential_loc = (x-1,y)
            elif self.direction == 'up':
                potential_loc = (x,y-1)
            else:   # self.direction = 'down'
                potential_loc = (x,y+1)
            if potential_loc not in path_corners: # valid move
                self.loc = potential_loc
                self.moves -= 1
            else: # corner! still make move tho!
                self.loc = potential_loc
                self.moves -= 1
                self.direction = path[potential_loc] # find new direction to move in!
        self.moves = self.speed # reset moves left for next time
        return self.loc

    def make_border(self): 
        object_width, object_height = self.size
        x = self.loc[0]
        y = self.loc[1]
        w = object_width//2
        h = object_height//2  
        border = {(x-w,n) for n in range(y-h,y+h+1)}
        a = {(x+w,n) for n in range(y-h,y+h+1)}
        b = {(n,y-h) for n in range(x-w, x+w+1)}
        c = {(n,y+h) for n in range(x-w, x+w+1)}
        border.update(a)
        border.update(b)
        border.update(c)
        return border # set of tuples of coordinates of object's border

################################################################################
################################################################################



if __name__ == '__main__':
   pass
