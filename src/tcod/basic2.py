#!/usr/bin/env python

import math
import random

import tcod as libtcod

# Size of the window.
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# Size of the map.
MAP_WIDTH = 80
MAP_HEIGHT = 45

# Parameters for dungeon generator.
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30


class Object:
    """
    Represents a generic object on the screen.
    """

    def __init__(self, x, y, char, colour):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour

    def move(self, dx, dy):
        if not map[self.y + dy][self.x + dx].blocked:
            self.x += dx
            self.y += dy

    def draw(self):
        libtcod.console_set_char_foreground(con, self.x, self.y, self.colour)
        libtcod.console_set_char(con, self.x, self.y, self.char)

    def clear(self):
        libtcod.console_set_char(con, self.x, self.y, ' ')


class Tile:
    """
    Represents a tile on the map and it's properties.
    """

    def __init__(self, blocked, blocked_sight=None):
        self.blocked = blocked

        if blocked_sight is None:
            blocked_sight = blocked
        self.blocked_sight = blocked_sight
        self.visible = False


class Rect:
    """
    Represents a rectangle on the map. Used to characterise a room.
    """

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
                (prev_x, prev_y) = rooms[num_rooms - 1].centre()
                if random.randint(0, 1) == 0:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            rooms.append(new_room)
            num_rooms += 1


def render_all():
    map_compute_fov(map, player.x, player.y, 5)
    # fov.map_compute_fov(map, player.y, player.x, 5, fov.BASIC)

    for row in range(MAP_HEIGHT):
        for col in range(MAP_WIDTH):
            if map[row][col].visible:
                wall = map[row][col].blocked_sight
                if wall:
                    libtcod.console_set_char(con, col, row, '#')
                else:
                    libtcod.console_set_char(con, col, row, '.')

    for object in objects:
        object.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


def handle_keys():
    key = libtcod.console_wait_for_keypress(True)
    if (key.vk == libtcod.KEY_ESCAPE):
        return "exit"
    elif (key.vk == libtcod.KEY_RIGHT or
          key.vk == libtcod.KEY_KP6):
        player.move(1, 0)
    elif (key.vk == libtcod.KEY_LEFT or
          key.vk == libtcod.KEY_KP4):
        player.move(-1, 0)
    elif (key.vk == libtcod.KEY_UP or
          key.vk == libtcod.KEY_KP8):
        player.move(0, -1)
    elif (key.vk == libtcod.KEY_DOWN or
          key.vk == libtcod.KEY_KP2):
        player.move(0, 1)
    elif (key.vk == libtcod.KEY_KP7):
        player.move(-1, -1)
    elif (key.vk == libtcod.KEY_KP9):
        player.move(1, -1)
    elif (key.vk == libtcod.KEY_KP1):
        player.move(-1, 1)
    elif (key.vk == libtcod.KEY_KP3):
        player.move(1, 1)


def map_compute_fov(map, x, y, max_radius=0):
    for row in range(MAP_HEIGHT):
        for col in range(MAP_WIDTH):
            within_range = (math.fabs(col - x) <= max_radius and
                            math.fabs(row - y) <= max_radius)
            if within_range:
                map[row][col].visible = True
            else:
                map[row][col].visible = False
    scan(1, 1.0, 0.0)


def scan(depth, startslope, endslope):
    """
    init x
    init y
    while current slope has not reached endslope do
        if (x,y) within visual range:
            if (x,y) blocked and prior not blocked then:
                scan(depth+1, startslope, new endslope)
            if (x,y) not blocked and prior blocked then:
                new startslope
            set (x,y) visible
        progress (x,y)

    regress(x,y)

    if (depth < visual range) and (x,y) not blocked:
        scan(depth+1, startslop, endslope)
    """

    pass


# ############################################
# Initialisation and Main Loop
# ############################################

libtcod.console_set_custom_font(b"res/terminal.png")
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, b"Hello World",
                          renderer=libtcod.RENDERER_SDL)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.console_set_default_background(con, libtcod.black)
libtcod.console_set_default_foreground(con, libtcod.grey)
libtcod.console_clear(con)

player = Object(25, 23, '@', libtcod.grey)
# npc = Object(10, 10, '@', libtcod.yellow)
objects = [player]

make_map()

while not libtcod.console_is_window_closed():
    render_all()
    libtcod.console_flush()
    for object in objects:
        object.clear()
    action = handle_keys()
    if action == "exit":
        break
