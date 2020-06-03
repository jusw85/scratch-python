#!/usr/bin/env python

import math
import random

import lib.fov as fov
import tcod as libtcod

# ############################################
# Constants
# ############################################

# Size of the window.
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
BAR_WIDTH = 20

# Size of the map.
MAP_WIDTH = 80
MAP_HEIGHT = 43

# Parameters for dungeon generator.
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

# Player parameters.
LIGHT_RADIUS = 20
PLAYER_HP = 10
PLAYER_POWER = 5
PLAYER_DEFENSE = 5

# Monster parameters.
TROLL_HP = 3
TROLL_POWER = 6
TROLL_DEFENSE = 1

# Visual paramters.
COLOUR_VISIBLE = libtcod.Color(192, 192, 128)
COLOUR_NOT_VISIBLE = libtcod.Color(64, 64, 64)
TROLL_COLOUR = libtcod.Color(24, 172, 92)
MONSTER_DEATH_COLOUR = libtcod.Color(192, 0, 0)
PLAYER_DEATH_COLOUR = libtcod.Color(192, 0, 0)


# ############################################
# Testing Functions
# ############################################


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1,
                         False, libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1,
                             False, libtcod.BKGND_SCREEN)

    # finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    msg = name + ': ' + str(value) + '/' + str(maximum)
    msg = bytes(msg, 'ascii')
    libtcod.console_print_ex(panel,
                             int(x + total_width / 2),
                             y,
                             libtcod.BKGND_NONE,
                             libtcod.CENTER,
                             msg)


dungeon = ["...........................................................",
           "...........................................................",
           "...........................................................",
           "...........................................................",
           "###########################################################",
           "#...........#.............................................#",
           "#...........#........#....................................#",
           "#.....................#...................................#",
           "#....####..............#..................................#",
           "#.......#.......................#####################.....#",
           "#.......#...........................................#.....#",
           "#.......#...........##..............................#.....#",
           "#####........#......##..........##################..#.....#",
           "#...#...........................#................#..#.....#",
           "#...#............#..............#................#..#.....#",
           "#...............................#..###############..#.....#",
           "#..............######...........#...................#.....#",
           "#..............#####............#...................#.....#",
           "#..............#####............#####################.....#",
           "#.........................................................#",
           "#.........................................................#",
           "###########################################################"]


def make_map2():
    global map
    map = [[Tile(False) for col in range(MAP_WIDTH)]
           for row in range(MAP_HEIGHT)]

    for row, row_actual in enumerate(dungeon):
        for col, col_actual in enumerate(row_actual):
            if dungeon[row][col] == '#':
                map[row][col] = Tile(True)


# ############################################
# Classes
# ############################################


class Object:
    """Represents a generic object on the screen."""

    def __init__(self, x, y, char, name, colour, blocks=False,
                 fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.colour = colour
        self.blocks = blocks
        self.fighter = fighter
        self.ai = ai
        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        if not is_blocked(self.y + dy, self.x + dx):
            self.x += dx
            self.y += dy

    def draw(self):
        if fov.map_is_in_fov(fov_map, self.y, self.x):
            libtcod.console_set_char_foreground(
                con, self.x, self.y, self.colour)
            libtcod.console_set_char(con, self.x, self.y, self.char)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def move_towards(self, target_y, target_x):
        dy = target_y - self.y
        dx = target_x - self.x
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def clear(self):
        libtcod.console_set_char(con, self.x, self.y, ' ')


class Tile:
    """Represents a tile on the map and it's properties."""

    def __init__(self, blocked, blocked_sight=None):
        self.blocked = blocked
        self.explored = False

        if blocked_sight is None:
            blocked_sight = blocked
        self.blocked_sight = blocked_sight


class Rect:
    """Represents a rectangle on the map. Used to characterise a room."""

    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def centre(self):
        centre_x = (self.x1 + self.x2) // 2
        centre_y = (self.y1 + self.y2) // 2
        return (centre_x, centre_y)

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Fighter:
    """Combat-related properties and methods. Used for composition with an Object."""

    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            print(
                self.owner.name.capitalize() +
                " attacks " +
                target.name +
                " for " +
                str(damage) +
                " hit points.")
            target.fighter.take_damage(damage)
        else:
            print(
                self.owner.name.capitalize() +
                " attacks " +
                target.name +
                " but it has no effect!")


class BasicMonster:
    """AI for a basic melee creep."""

    def take_turn(self):
        monster = self.owner
        if fov.map_is_in_fov(fov_map, monster.y, monster.x):
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.y, player.x)
            elif player.fighter.hp >= 0:
                monster.fighter.attack(player)


# ############################################
# Utility Functions
# ############################################


def is_blocked(y, x):
    if map[y][x].blocked:
        return True

    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False


# ############################################
# Map Generation Functions
# ############################################


def create_room(room):
    global map
    for row in range(room.y1, room.y2):
        for col in range(room.x1, room.x2):
            map[row][col].blocked = False
            map[row][col].blocked_sight = False


def create_h_tunnel(x1, x2, row):
    global map
    for col in range(min(x1, x2), max(x1, x2) + 1):
        map[row][col].blocked = False
        map[row][col].blocked_sight = False


def create_v_tunnel(y1, y2, col):
    global map
    for row in range(min(y1, y2), max(y1, y2) + 1):
        map[row][col].blocked = False
        map[row][col].blocked_sight = False


def make_map():
    global map, player
    map = [[Tile(True) for col in range(MAP_WIDTH)]
           for row in range(MAP_HEIGHT)]

    rooms = []
    num_rooms = 0

    for i in range(MAX_ROOMS):
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, MAP_WIDTH - w - 1)
        y = random.randint(1, MAP_HEIGHT - h - 1)
        new_room = Rect(x, y, w, h)

        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            create_room(new_room)
            (new_x, new_y) = new_room.centre()
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else:
                place_objects(new_room)
                (prev_x, prev_y) = rooms[num_rooms - 1].centre()
                if random.randint(0, 1) == 0:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            rooms.append(new_room)
            num_rooms += 1


def place_objects(room):
    num_monsters = random.randint(0, MAX_ROOM_MONSTERS)
    for i in range(num_monsters):
        x = random.randint(room.x1, room.x2)
        y = random.randint(room.y1, room.y2)
        if not is_blocked(y, x):
            fighter_component = Fighter(
                hp=TROLL_HP,
                defense=TROLL_DEFENSE,
                power=TROLL_POWER,
                death_function=monster_death)
            ai_component = BasicMonster()
            monster = Object(x, y, 'T', 'troll', TROLL_COLOUR, blocks=True,
                             fighter=fighter_component, ai=ai_component)
            objects.append(monster)


# ############################################
# Drawing Functions
# ############################################


def render_all():
    global fov_map, fov_recompute

    if fov_recompute:
        fov_recompute = False
        fov.map_compute_fov(fov_map, player.y, player.x,
                            LIGHT_RADIUS, fov.RECURSIVE_SHADOWCASTING)
        for row in range(MAP_HEIGHT):
            for col in range(MAP_WIDTH):
                visible = fov.map_is_in_fov(fov_map, row, col)
                wall = map[row][col].blocked_sight
                draw = False

                if not visible:
                    if map[row][col].explored:
                        draw = True
                        libtcod.console_set_char_foreground(
                            con, col, row, COLOUR_NOT_VISIBLE)
                else:
                    draw = True
                    libtcod.console_set_char_foreground(
                        con, col, row, COLOUR_VISIBLE)
                    map[row][col].explored = True

                if draw:
                    if wall:
                        libtcod.console_set_char(con, col, row, '#')
                    else:
                        libtcod.console_set_char(con, col, row, '.')

    for object in objects:
        if object != player:
            object.draw()
    player.draw()

    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    # prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)

    # blit the contents of "panel" to the root console
    libtcod.console_blit(
        panel,
        0,
        0,
        SCREEN_WIDTH,
        PANEL_HEIGHT,
        0,
        0,
        PANEL_Y)


# ############################################
# Game Functions
# ############################################


def player_death(player):
    global game_state
    print("You died!")
    game_state = 'dead'
    player.char = '%'
    player.colour = PLAYER_DEATH_COLOUR


def monster_death(monster):
    print(monster.name.capitalize() + " is dead!")
    monster.char = '%'
    monster.colour = MONSTER_DEATH_COLOUR
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = "remains of " + monster.name
    monster.send_to_back()


# ############################################
# Player Functions
# ############################################


def player_attack_move(dx, dy):
    x = player.x + dx
    y = player.y + dy

    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)


def handle_keys():
    global fov_recompute
    fov_recompute = True

    key = libtcod.console_wait_for_keypress(True)
    if (key.vk == libtcod.KEY_ESCAPE):
        return "exit"
    elif (key.vk == libtcod.KEY_ENTER and (key.lalt or key.ralt)):
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    if game_state == 'playing':
        if (key.vk == libtcod.KEY_RIGHT or
                key.vk == libtcod.KEY_KP6):
            player_attack_move(1, 0)
        elif (key.vk == libtcod.KEY_LEFT or
              key.vk == libtcod.KEY_KP4):
            player_attack_move(-1, 0)
        elif (key.vk == libtcod.KEY_UP or
              key.vk == libtcod.KEY_KP8):
            player_attack_move(0, -1)
        elif (key.vk == libtcod.KEY_DOWN or
              key.vk == libtcod.KEY_KP2):
            player_attack_move(0, 1)
        elif (key.vk == libtcod.KEY_KP7):
            player_attack_move(-1, -1)
        elif (key.vk == libtcod.KEY_KP9):
            player_attack_move(1, -1)
        elif (key.vk == libtcod.KEY_KP1):
            player_attack_move(-1, 1)
        elif (key.vk == libtcod.KEY_KP3):
            player_attack_move(1, 1)
        elif (key.vk == libtcod.KEY_KP5):
            pass
        else:
            fov_recompute = False
            return 'skip-turn'


# ############################################
# Initialisation and Main Loop
# ############################################

libtcod.console_set_custom_font(b"res/terminal10x16_gs_ro.png",
                                libtcod.FONT_LAYOUT_ASCII_INROW |
                                libtcod.FONT_TYPE_GREYSCALE)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, b"Hello World",
                          renderer=libtcod.RENDERER_SDL)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
libtcod.console_set_default_background(con, libtcod.Color(0, 0, 0))
libtcod.console_set_default_foreground(con, libtcod.Color(127, 127, 127))
libtcod.console_clear(con)

fighter_component = Fighter(
    hp=PLAYER_HP,
    defense=PLAYER_DEFENSE,
    power=PLAYER_POWER,
    death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.Color(127, 127, 127), blocks=True,
                fighter=fighter_component)
objects = [player]

make_map()

fov_map = fov.map_new(MAP_WIDTH, MAP_HEIGHT)
for row in range(MAP_HEIGHT):
    for col in range(MAP_WIDTH):
        fov.map_set_properties(fov_map, row, col, map[row][col].blocked_sight)

fov_recompute = True
game_state = 'playing'
player_action = None

while not libtcod.console_is_window_closed():
    render_all()
    libtcod.console_flush()
    for object in objects:
        object.clear()
    player_action = handle_keys()
    if player_action == "exit":
        break

    if game_state == 'playing' and player_action != 'skip-turn':
        for object in objects:
            if object.ai:
                object.ai.take_turn()
