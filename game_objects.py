import pygame
import random
import math
import os
import sys
from perlin_noise import PerlinNoise

seed = random.randint(100000, 999999)
noise = PerlinNoise(100, seed)
noise_1 = PerlinNoise(100, seed + 10)

back_manager = None
windows = None
window_surface = pygame.Surface((0, 0))
tile_render = None
world_loader = None
cursor = None
window_width, window_height = 0, 0
main_camera = None
basic_font = None
big_font = None
game_escape = None
click = True

black = 0, 0, 0
white = 255, 255, 255
red = 255, 0, 0
l_grey = 100, 100, 100
yellow = 255, 255, 0
inv_bg = 154, 151, 166


def resize_image(img, mult):
    return pygame.transform.scale(img, (img.get_width() * mult, img.get_height() * mult))


class Timer:
    def __init__(self):
        self.dt = 0
        self.game_speed = 1
        self.tick_speed = 0

    def change(self, amount):
        return amount * self.dt * self.game_speed


timer = Timer()


button_names = {"exit": "Exit Game",
                "save": "Save Game",
                "load": "Load Game"}

button_images = []


class Window:
    def __init__(self, window_type, pos=(200, 200)):
        self.type = window_type
        self.rect = pygame.Rect(pos[0], pos[1], 0, 0)
        self.border_image = pygame.image.load("images/menu/window_border.png")
        self.border_source_images = {"corner": self.border_image.subsurface(0, 0, 6, 6),
                                     "verticals": self.border_image.subsurface(6, 0, 2, 2),
                                     "horizontals": self.border_image.subsurface(8, 0, 2, 2)}

        self.surface = pygame.Surface((0, 0))

        self.do_resize = {"corner": (0, 0),
                          "verticals": (0, 1),
                          "horizontals": (1, 0)}

        self.border_images = {}
        self.bg_rect_max_time = 0

        self.bg_rect_time = 0
        self.bg_rects = []
        self.things = []
        self.centered = False
        self.offset = [0, 0]
        self.size = 500, 500
        self.room = False
        if window_type == "inventory":
            self.inventory = Inventory(self)
        else:
            self.inventory = None
        self.network = None
        self.things_start_y = 60
        with open(f"windows/{window_type}.txt", "r") as file:
            for line in file:
                if line.endswith("\n"):
                    line = line[:-1]

                if line == "center":
                    self.centered = True
                elif line == "room":
                    self.room = True
                elif line == "money":
                    self.things.append(["money", None, pygame.Rect(0, 0, 0, 0)])
                if " " in line:
                    fields = line.split()
                    if fields[0] == "start":
                        self.things_start_y = int(fields[1])
                    if fields[0] == "label":
                        tx = basic_font.render(fields[1], True, white)
                        self.things.append(("label", tx, tx.get_rect()))
                    if fields[0] == "button":
                        self.things.append((fields[1], basic_font.render((button_names[fields[1]]), True, white), pygame.Rect(0, 0, 184, 60)))
                    if fields[0] == "size":
                        self.size = change_list(fields[1:], int)
                    if fields[0] == "pos":
                        vals = change_list(fields[1:], int)
                        self.rect.topleft = vals
                        self.offset = vals

        self.resize(self.size)
        self.click = True

    def resize(self, size):
        for img in self.border_source_images:
            new_size = [self.border_source_images[img].get_width() * 4, size[0] - 24][self.do_resize[img][0]],\
                       [self.border_source_images[img].get_height() * 4, size[1] - 24][self.do_resize[img][1]]
            self.border_images[img] = pygame.transform.scale(self.border_source_images[img], new_size).convert_alpha()
        self.surface = pygame.Surface(size)
        if not self.room:
            self.surface.set_alpha(200)
        self.bg_rect_max_time = (self.rect.width * self.rect.height) / 2500000
        self.rect.size = size

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.inventory is not None:

            self.inventory.update()
        if self.centered:
            self.rect.center = (window_width / 2) + self.offset[0], (window_height / 2) + self.offset[1]

        end_y = self.things_start_y
        for thing_num in range(len(self.things)):
            thing = self.things[thing_num]
            thing[2].center = self.rect.centerx, self.rect.y + end_y
            if thing[0] == "money":
                thing[1] = big_font.render(f"${money}", True, white)
                thing[2].size = thing[1].get_size()
            else:
                if thing[2].collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] and self.click:
                    self.click = False
                    if thing[0] == "exit":
                        pygame.quit()
                        sys.exit()
                    elif thing[0] == "load":
                        world_loader.load("worlds/test.txt")
                    elif thing[0] == "save":
                        world_loader.save("worlds/test.txt")

            end_y += 80

        if self.room:
            self.network.update()

        self.click = not pygame.mouse.get_pressed()[0]

    def draw(self):
        self.surface.fill(black)
        if self.room and self.network is not None:
            self.network.draw_room(self.surface)

        elif self.inventory is not None:
            self.inventory.draw()

        if not self.room:
            self.bg_rect_time -= timer.change(1)
            if self.bg_rect_time <= 0 and len(self.bg_rects) < 60:
                self.bg_rect_time = random.random() * self.bg_rect_max_time
                self.bg_rects.append(
                    [pygame.Rect(random.randint(0, self.rect.width), random.randint(0, self.rect.height),
                                 20, 20), 3])
                self.bg_rects[-1][0].center = self.bg_rects[-1][0].topleft

            for rect in self.bg_rects:
                rect[1] -= timer.change(1)
                if rect[1] > 0:
                    col = math.sin((rect[1] / 3) * math.pi) * 10
                    color = col, col, col
                    pygame.draw.rect(self.surface, color, rect[0])
                else:
                    self.bg_rects.remove(rect)

        window_surface.blit(self.surface, self.rect)
        mouse_pos = pygame.mouse.get_pos()
        for thing in self.things:
            if thing[0] in ["money", "label"]:
                window_surface.blit(thing[1], thing[2])
            else:
                window_surface.blit(button_images[int(thing[2].collidepoint(mouse_pos))], thing[2])
                text_rect = thing[1].get_rect()
                text_rect.center = thing[2].center
                window_surface.blit(thing[1], text_rect)
        for x in range(2):
            for y in range(2):
                window_surface.blit(self.border_images["corner"], (self.rect.x + (x * self.rect.width) - 12,
                                                                   self.rect.y + (y * self.rect.height) - 12))
        for edge in range(2):
            window_surface.blit(self.border_images["verticals"], (self.rect.x + (edge * self.rect.width) - 4,
                                                                 self.rect.y + 12))
            window_surface.blit(self.border_images["horizontals"], (self.rect.x + 12,
                                                                   self.rect.y + (edge * self.rect.height) - 4))

    def back(self):
        back_manager.remove(self)
        windows.remove(self)


class WorldLoader:
    def __init__(self):
        self.loaded_chunk_positions = {}
        self.chunk_size = 10
        self.chunks = []
        self.chunk_buffer = []
        self.interact_chunks = []

    def full_load(self, file):
        with open(file, "r") as lines:
            self.chunk_to_line = {}
            for line in lines:
                if line == "\n":
                    break
                else:
                    print(line)

    def update(self, camera, cursor_pos):
        camera_iso_pos = reverse_tile_pos((window_width / 2, window_height / 2), camera)
        camera_chunk = (int(camera_iso_pos[0] / 20), int(camera_iso_pos[1] / 20))
        for x in range(camera_chunk[0] - 4, camera_chunk[0] + 5):
            for y in range(camera_chunk[1] - 4, camera_chunk[1] + 5):
                if (x, y) not in self.loaded_chunk_positions and (x, y) not in self.chunk_buffer:
                    self.chunk_buffer.append((x, y))

        if len(self.chunk_buffer) > 100:
            self.chunk_buffer = []

        for i in range(2):
            if self.chunk_buffer:
                x, y = self.chunk_buffer[0]
                if (x, y) not in self.loaded_chunk_positions:
                    new_chunk = Chunk((x, y))
                    self.loaded_chunk_positions[(x, y)] = new_chunk
                    self.chunks.append(new_chunk)
                    tile_render.chunks.add(new_chunk)
                    tile_render.chunks.change_layer(new_chunk, new_chunk.chunk_pos[0] + new_chunk.chunk_pos[1])
                self.chunk_buffer.remove(self.chunk_buffer[0])

        for chunk in self.chunks:
            chunk.update()

        cursor_pos = int(cursor_pos[0]), int(cursor_pos[1])
        cursor_chunk_pos = int(cursor_pos[0] / 20), int(cursor_pos[1] / 20)
        if cursor_chunk_pos in self.loaded_chunk_positions and cursor_chunk_pos in self.interact_chunks:
            self.loaded_chunk_positions[cursor_chunk_pos].interact_update(cursor_pos)

    def load(self, read_file):
        for chunk in reversed(world_loader.chunks):
            chunk.despawn()
        world_loader.chunk_buffer = []
        with open(read_file, "r") as file:
            for line in file:
                if line.startswith("<pos>"):
                    global main_camera
                    main_camera.pos = change_list(line.split()[1:], float)
                if line.startswith("<seed>"):
                    global noise
                    global noise_1
                    global seed
                    seed = int(line.split()[1])
                    noise = PerlinNoise(100, seed)
                    noise_1 = PerlinNoise(100, seed + 10)

        remove_window(game_escape)

    def save(self, save_file):

        def format_save(name, thing):
            r_str = f"<{name}>"
            if type(thing) in [list, tuple]:
                for item in thing:
                    r_str += " " + str(item)
            else:
                r_str += " " + str(thing)

            r_str += "\n"
            return r_str

        save_list = []

        def save(name, thing):
            save_list.append(format_save(name, thing))

        with open(save_file, "w") as file:
            save("pos", main_camera.pos)
            save("seed", seed)
            file.writelines(save_list)


def change_list(old_list, change_to):
    new_list = []
    for item in old_list:
        new_list.append(change_to(item))
    return new_list


def add_window(window):
    if window not in windows.windows:
        windows.add(window)
        back_manager.add(window)


def remove_window(window):
    if window in windows.windows:
        windows.remove(window)
    if window in back_manager.back_order:
        back_manager.remove(window)


zoom = 4

money = 0

tile_images = {}
tile_offsets = {}

room_images = {"normal": "room.png"}

debug_chunk_surf = None
debug = False

net_cursor = None


def load_images():
    global basic_font
    global button_images
    global room_images
    global net_cursor
    global big_font
    basic_font = pygame.font.Font("fonts/VCR_OSD_MONO_1.001.ttf", 18)
    big_font = pygame.font.Font("fonts/VCR_OSD_MONO_1.001.ttf", 40)
    for name in os.listdir("images/tiles"):
        tile_images[name] = pygame.image.load("images/tiles/" + name).convert_alpha()
        tile_offsets[name] = (0, 8 - tile_images[name].get_height())
    for room in room_images:
        room_images[room] = pygame.image.load(f"images/rooms/{room_images[room]}").convert_alpha()
    bi = resize_image(pygame.image.load("images/menu/button_small.png").convert_alpha(), 4)
    bi_1 = bi.copy()
    bi_1.fill((20, 20, 20), special_flags=pygame.BLEND_RGB_ADD)
    button_images = [bi, bi_1]
    net_cursor = Cursor(4)

    w_in = Window("inventory")
    add_window(w_in)
    back_manager.remove(w_in)

    w_sh = Window("shop")
    add_window(w_sh)
    back_manager.remove(w_sh)


low = 0
high = -1

image_time = 0.25
max_image_time = 0.25


class Chunk(pygame.sprite.Sprite):
    def __init__(self, chunk_pos):
        self._layer = 0
        pygame.sprite.Sprite.__init__(self)
        global low
        global high
        self.chunk_pos = chunk_pos
        self.pos = self.chunk_pos[0] * 20, self.chunk_pos[1] * 20
        self.images = [pygame.Surface((320, 160), pygame.SRCALPHA)]
        self.image_index = 0
        self.image_time = image_time
        self.max_image_time = max_image_time
        self.top_buffer = []
        self.grid = []
        water_positions = []
        self.click = True

        def draw_tile(rect, name):
            draw_pos = (rect.x + tile_offsets[name][0], rect.y + tile_offsets[name][1])
            if draw_pos[1] < 0:
                self.top_buffer.append((draw_pos, name))

            self.images[0].blit(tile_images[name], draw_pos)

        add_interact = False
        for y in range(20):
            self.grid.append([])
            for x in range(20):
                tile_num = 0
                tile_rect = pygame.Rect(0, 0, 16, 8)
                tile_rect.midtop = 160 + (x * 8) - (y * 8), (y * 4) + (x * 4)
                pos = ((self.pos[0] + x) / 10000, (self.pos[1] + y) / 10000)
                noise_pos_value = noise(pos)
                if noise_pos_value > 0:
                    if noise_pos_value > 0.017:
                        noise_pos_value_1 = noise_1(pos)
                        if noise_pos_value_1 > 0.25:
                            draw_tile(tile_rect, "building.png")
                            tile_num = 1
                            add_interact = True
                        else:
                            draw_tile(tile_rect, "grass.png")
                    else:
                        draw_tile(tile_rect, "sand.png")
                else:
                    col_mult = noise_pos_value
                    if col_mult < -0.05:
                        col_mult = -0.05
                    new_sand = tile_images["sand.png"].copy()
                    sub = (col_mult / -0.05) * 255
                    # print(sub)
                    new_sand.fill((sub, sub * 0.2, 0), special_flags=pygame.BLEND_RGB_SUB)
                    self.images[0].blit(new_sand, tile_rect)
                    water_positions.append((tile_rect, random.randint(0, 2)))
                self.grid[y].append(tile_num)
        if add_interact:
            world_loader.interact_chunks.append(self.chunk_pos)

        # print(low, high)

        if water_positions:
            self.animate = True
            for i in range(2):
                new = self.images[0].copy()
                self.images.append(new)
            for wotah in water_positions:
                area_int = wotah[1]
                for img in self.images:
                    img.blit(tile_images["water.png"], wotah[0], (16 * area_int, 0, 16, 8))
                    area_int += 1
                    if area_int > 2:
                        area_int = 0
        else:
            self.animate = False

        for img_index in range(len(self.images)):
            self.images[img_index] = resize_image(self.images[img_index], zoom)

        self.lower_chunks = [(0, 1), (1, 0)]
        self.debug_color = random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)
        self.debug_color_1 = [int(col * 2.55) for col in self.debug_color]
        self.chunk_num = random.randint(0, 255)

    def update(self):
        screen_center = window_width / 2, window_height / 2
        screen_center = reverse_tile_pos(screen_center, main_camera)
        dist_center = distance(self.pos, screen_center)
        if dist_center > 200:
            self.despawn()

    def interact_update(self, cursor_pos):
        if self.grid[cursor_pos[1] - self.pos[1]][cursor_pos[0] - self.pos[0]] > 0:
            pygame.draw.rect(window_surface, red, pygame.Rect(20, 20, 100, 100))
            if pygame.mouse.get_pressed()[0] and self.click and selected_window() is None:
                new_win = Window("network")
                add_window(new_win)
                new_win.network = Network(new_win)
        self.click = not pygame.mouse.get_pressed()[0]

    def draw(self, camera):
        global image_time
        if self.animate:
            self.image_time -= timer.change(1)
            if self.image_time <= 0:
                self.image_time = self.max_image_time
                self.image_index += 1
                if self.image_index > 2:
                    self.image_index = 0
            image_time = self.image_time

        for pos_diff in self.lower_chunks:
            check_chunk_pos = self.chunk_pos[0] + pos_diff[0], self.chunk_pos[1] + pos_diff[1]
            if check_chunk_pos in world_loader.loaded_chunk_positions:
                the_goofy_and_or_silly_lil_chunk_in_question = world_loader.loaded_chunk_positions[check_chunk_pos]
                if the_goofy_and_or_silly_lil_chunk_in_question.top_buffer:
                    for tile in the_goofy_and_or_silly_lil_chunk_in_question.top_buffer:
                        scaled_tile = resize_image(tile_images[tile[1]], zoom)
                        if debug:
                            scaled_tile.fill(self.debug_color, special_flags=pygame.BLEND_RGB_ADD)
                        new_pos = (tile[0][0] + (-160 + (320 * pos_diff[0]))) * zoom, (tile[0][1] + 80) * zoom
                        for img in self.images:
                            img.blit(scaled_tile, new_pos)
                            if debug:
                                img.blit(basic_font.render(str(the_goofy_and_or_silly_lil_chunk_in_question.chunk_num), True, the_goofy_and_or_silly_lil_chunk_in_question.debug_color), new_pos)
                self.lower_chunks.remove(pos_diff)

        draw_pos = ((((self.pos[0] / 2) - (self.pos[1] / 2)) * 16) - 160 - camera.pos[0]) * zoom, ((((self.pos[1] / 4) + (self.pos[0] / 4)) * 16) - camera.pos[1]) * zoom
        window_surface.blit(self.images[self.image_index], draw_pos)
        if debug:
            debug_rect = pygame.Rect(draw_pos[0], draw_pos[1], 320 * zoom, 160 * zoom)
            if pygame.mouse.get_pressed()[0] and debug_rect.collidepoint(pygame.mouse.get_pos()):
                global debug_chunk_surf
                debug_chunk_surf = self.images[0]
            pygame.draw.rect(window_surface, self.debug_color_1, debug_rect, 2)
            pygame.draw.line(window_surface, self.debug_color[1], debug_rect.midleft, debug_rect.midtop, 2)
            pygame.draw.line(window_surface, self.debug_color[1], debug_rect.midtop, debug_rect.midright, 2)
            window_surface.blit(basic_font.render(str(self._layer), True, black), draw_pos)
            window_surface.blit(basic_font.render(str(self.chunk_num), True, self.debug_color_1), (draw_pos[0] + 60, draw_pos[1]))

    def despawn(self):
        world_loader.chunks.remove(self)
        tile_render.chunks.remove(self)
        del world_loader.loaded_chunk_positions[self.chunk_pos]
        if self.chunk_pos in world_loader.chunk_buffer:
            world_loader.chunk_buffer.remove(self.chunk_pos)
        if self in world_loader.interact_chunks:
            world_loader.interact_chunks.remove(self)


class TileRender:
    def __init__(self):
        self.chunks = pygame.sprite.LayeredUpdates()

    def draw(self, camera):
        for chunk in self.chunks:
            chunk.draw(camera)

        if debug:
            if debug_chunk_surf is not None:
                window_surface.blit(debug_chunk_surf, (0, 0))


def selected_window():
    return windows.selected_window


class Camera:
    def __init__(self, window_mode=False, pos=(0, 0)):
        self.pos = list(pos)
        self.original_cam_pos = pos
        self.original_mouse_pos = (0, 0)
        self.rect = pygame.Rect(0, 0, 1920, 1080)
        self.click = True
        self.window_mode = window_mode

    def update(self, window=None):
        self.move(window)

    def move(self, window):
        mouse_pos = pygame.mouse.get_pos()
        zoom_1 = zoom
        if self.window_mode and window is not None:
            zoom_1 = window.network.zoom
        mouse_pos = mouse_pos[0] / zoom_1, mouse_pos[1] / zoom_1
        l_down = pygame.mouse.get_pressed()[1] and (((not self.window_mode) and selected_window() is None) or (self.window_mode and selected_window() == window))
        # set initial point
        if l_down and self.click:
            self.original_cam_pos = self.pos
            self.original_mouse_pos = mouse_pos

        if l_down:
            self.pos = [self.original_cam_pos[0] - (mouse_pos[0] - self.original_mouse_pos[0]),
                        self.original_cam_pos[1] - (mouse_pos[1] - self.original_mouse_pos[1])]
            self.rect.topleft = self.pos

        self.click = not pygame.mouse.get_pressed()[1]


class Cursor:
    def __init__(self, size=zoom, main=False):
        self.no_window = main
        self.pos = [0, 0]
        self.image = pygame.image.load("images/other_ui/cursor.png").convert_alpha()
        self.image = resize_image(self.image, size)
        self.rect = self.image.get_rect()

    def update(self, camera, window=None, net_zoom=zoom):
        mouse_pos = pygame.mouse.get_pos()
        if window is not None:
            mouse_pos = mouse_pos[0] - window.rect.x, mouse_pos[1] - window.rect.y

        first_pos = reverse_tile_pos(mouse_pos, camera, net_zoom)
        self.pos = first_pos
        self.rect.midtop = tile_pos((int(first_pos[0]), int(first_pos[1])), camera, net_zoom)

    def draw(self, surface):
        cond = (not self.no_window) or (self.no_window and selected_window() is None)
        if cond:
            surface.blit(self.image, self.rect)


net_cam = Camera(False, (-160, -97))


class Device:
    def __init__(self, folder, device):
        self.image = pygame.image.load(f"images/{folder}/{device}.png").convert_alpha()
        self.rect = self.image.get_rect()
        height = self.rect.width / 2
        self.offset = [0, -self.rect.height + height]
        self.rect.height = height

        self.inv_rect = self.image.get_rect()
        self.inv_image = pygame.Surface((self.inv_rect.width + 8, self.inv_rect.height + 8))
        self.inv_image.fill(inv_bg)
        self.inv_rect.center = self.inv_image.get_width() / 2, self.inv_image.get_height() / 2
        pygame.draw.rect(self.inv_image, white, self.inv_rect, 2)
        self.inv_image.blit(self.image, self.inv_rect)
        self.inv_rect = self.inv_image.get_rect()

    def draw_world(self, surface):
        surface.blit(self.image, (self.rect.x - self.offset[0], self.rect.y - self.offset[1]))

    def update_inv(self, pos):
        self.inv_rect.topleft = pos

    def draw_inv(self, window):
        blit_after_window(self.inv_image, (self.inv_rect.x + window.rect.x, self.inv_rect.y + window.rect.y))


blit_buffer = []


def blit_after_window(*args):
    blit_buffer.append(args)


class Inventory:
    class DeviceList:
        def __init__(self, folder):
            self.devices = [Device(folder, "rack"), Device(folder, "switch")]

        def update(self):
            end_y = 40
            for d in self.devices:
                d.update_inv((40, end_y))
                end_y += d.inv_rect.height + 20

        def draw(self, window):
            for d in self.devices:
                d.draw_inv(window)

    def __init__(self, window):
        self.room_devices = self.DeviceList("room_devices")
        self.window = window

    def update(self):
        if selected_window() is not None:
            if selected_window().room or selected_window() == self.window:
                self.room_devices.update()
            else:
                pass
        else:
            pass

    def draw(self):
        if selected_window() is not None:
            if selected_window().room or selected_window() == self.window:
                self.room_devices.draw(self.window)
            else:
                pass
        else:
            pass


class Network:
    def __init__(self, window):
        self.camera = Camera(True)
        self.click = True
        self.zoom = 4
        self.image = None
        self.change_room()
        self.selected = False
        self.rooms = []
        self.room_icons = []
        self.window = window
        self.selected_room = [1, 0]
        for y in range(6):
            self.rooms.append([])
            self.room_icons.append([])
            for x in range(6):
                self.room_icons[y].append(None)
                if y < 2 and x < 2:
                    self.rooms[y].append(("normal", []))
                else:
                    self.rooms[y].append(("", []))

        self.room_sel_rect = pygame.Rect(15, self.window.rect.height - (len(self.rooms) * 26) - 15, (len(max(self.rooms, key=self.room_max_key)) * 22) + 5, (len(self.rooms) * 26) + 15)

    def room_max_key(self, r):
        return len(r)

    def draw_room(self, surface):
        surface.blit(self.image, (-(self.camera.rect.x + 160) * self.zoom, -(self.camera.rect.y + 97) * self.zoom))
        if self.selected:
            if not self.collide_room_grid():
                net_cursor.draw(surface)
            if debug:
                window_surface.blit(basic_font.render(str((change_list(net_cursor.pos, int))), True, white), (window_width - 200, 0))

        for y in range(len(self.rooms)):
            for x in range(len(self.rooms[y])):
                room = self.rooms[y][x][0] != ""
                col = [l_grey, yellow][int(self.selected_room == [x, y])]

                pygame.draw.rect(surface, col, self.room_icons[y][x][0], int(not room) * 2)
                if self.room_icons[y][x][1]:
                    pygame.draw.rect(surface, white, self.room_icons[y][x][0], 2)

    def change_room(self):
        self.image = room_images["normal"].copy()
        for y in range(20):
            p_1, p_2 = tile_pos((0, y), net_cam, 1), tile_pos((20, y), net_cam, 1)
            pygame.draw.line(self.image, l_grey, p_1, p_2)
        for x in range(20):
            p_1, p_2 = tile_pos((x, 0), net_cam, 1), tile_pos((x, 20), net_cam, 1)
            pygame.draw.line(self.image, l_grey, p_1, p_2)

        self.image = resize_image(self.image, self.zoom)

    def update(self):
        for y in range(len(self.rooms)):
            for x in range(len(self.rooms[y])):
                i_rect = pygame.Rect(19 + (x * 22), self.window.rect.height - 35 - (y * 26), 20, 20)
                m_pos = pygame.mouse.get_pos()
                i_mouse = i_rect.collidepoint((m_pos[0] - self.window.rect.x, m_pos[1] - self.window.rect.y)) and self.rooms[y][x][0] != ""
                self.room_icons[y][x] = i_rect, i_mouse
                if i_mouse and pygame.mouse.get_pressed()[0] and click:
                    self.selected_room = [x, y]

        self.camera.update(self.window)
        if selected_window() == self.window:

            if not self.collide_room_grid():
                net_cursor.update(self.camera, self.window, self.zoom)
            self.selected = True
            self.camera.update()
        else:
            self.selected = False

    def collide_room_grid(self):
        m_pos = pygame.mouse.get_pos()
        return self.room_sel_rect.collidepoint((m_pos[0] - self.window.rect.x, m_pos[1] - self.window.rect.y))


def tile_pos(pos, camera, different_zoom=zoom):
    """Screen position to isometric position"""
    return (((pos[0] * 8) - (pos[1] * 8)) * different_zoom) - (camera.pos[0] * different_zoom), (((pos[1] * 4) + (pos[0] * 4)) * different_zoom) - (camera.pos[1] * different_zoom)


def reverse_tile_pos(pos, camera, different_zoom=zoom):
    """Isometric position to screen position"""
    pos = pos[0] + (camera.pos[0] * different_zoom), pos[1] + (camera.pos[1] * different_zoom)
    # return ((pos[0] * 2) + (pos[1] * 4)) / zoom, ((pos[1] * 2) + (pos[0] * 4)) / zoom
    return ((pos[0] / 16) + (pos[1] / 8)) / different_zoom, -(-(pos[1] / 8) + (pos[0] / 16)) / different_zoom


def mouse_tile_pos():
    mx, my = pygame.mouse.get_pos()
    return mx * zoom


def distance(point1, point2):
    return abs(math.sqrt(((point2[0] - point1[0]) ** 2) + ((point2[1] - point1[1]) ** 2)))
