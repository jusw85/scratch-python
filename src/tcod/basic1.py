import tcod as libtcod

# actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50


def handle_keys():
    global playerx, playery
    key = libtcod.console_wait_for_keypress(True)  # turn-based

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return True  # exit game

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP) or \
            libtcod.console_is_key_pressed(libtcod.KEY_KP8):
        playery -= 1
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or \
            libtcod.console_is_key_pressed(libtcod.KEY_KP2):
        playery += 1
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or \
            libtcod.console_is_key_pressed(libtcod.KEY_KP4):
        playerx -= 1
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or \
            libtcod.console_is_key_pressed(libtcod.KEY_KP6):
        playerx += 1
    elif key.vk == libtcod.KEY_KP7:
        playerx -= 1
        playery -= 1
    elif key.vk == libtcod.KEY_KP9:
        playerx += 1
        playery -= 1
    elif key.vk == libtcod.KEY_KP1:
        playerx -= 1
        playery += 1
    elif key.vk == libtcod.KEY_KP3:
        playerx += 1
        playery += 1


libtcod.console_set_custom_font(b'res/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, b'Python', False)

playerx = SCREEN_WIDTH // 2
playery = SCREEN_HEIGHT // 2

while not libtcod.console_is_window_closed():
    libtcod.console_set_default_foreground(0, libtcod.white)
    libtcod.console_put_char(0, playerx, playery, '@', libtcod.BKGND_NONE)
    libtcod.console_flush()
    libtcod.console_put_char(0, playerx, playery, ' ', libtcod.BKGND_NONE)

    exit = handle_keys()
    if exit:
        break
