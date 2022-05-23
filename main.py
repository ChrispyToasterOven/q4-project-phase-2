import pygame
from pygame.locals import *
import game_objects
import sys

pygame.init()
main_clock = pygame.time.Clock()

window_width = 1920
window_height = 1080
game_objects.window_width, game_objects.window_height = window_width, window_height
window_surface = pygame.display.set_mode((window_width, window_height), pygame.FULLSCREEN, 16, 0)
pygame.display.set_caption("Lets get racist up in here!")
pygame.display.set_icon(pygame.image.load("middleagedthaddeuswojak128.png"))
game_objects.window_surface = window_surface

white = 255, 255, 255
black = 0, 0, 0
blue = 0, 0, 255
bg_blue = 0, 140, 150

basic_font = pygame.font.Font("fonts/VCR_OSD_MONO_1.001.ttf", 18)


class WindowManager:
    def __init__(self):
        self.windows = []
        self.selected_window = None

    def add(self, window):
        self.windows.append(window)
        self.selected_window = window

    def remove(self, window):
        self.windows.remove(window)
        self.selected_window = None

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and click:
            self.selected_window = None
            for window in self.windows:
                if window.rect.collidepoint(mouse_pos):
                    self.selected_window = window
            if self.selected_window in self.windows:
                self.windows.remove(self.selected_window)
                self.windows.append(self.selected_window)

        for window in self.windows:
            window.update()
            window.draw()


class BackManager:
    def __init__(self):
        self.back_order = []

    def go_back(self, obj=None):
        if window_manager.selected_window is not None and window_manager.selected_window in self.back_order:
            window_manager.selected_window.back()

        elif self.back_order:
            if obj is None:
                check_for_obj = self.back_order[-1]
            else:
                check_for_obj = obj
            while check_for_obj in self.back_order:
                self.back_order[-1].back()

    def add(self, obj):
        self.back_order.append(obj)

    def remove(self, obj):
        self.back_order.remove(obj)


timer = game_objects.timer
window_manager = WindowManager()
back_manager = BackManager()

game_objects.timer = timer
game_objects.back_manager = back_manager
game_objects.windows = window_manager

game_objects.load_images()

main_camera = game_objects.Camera()
game_objects.main_camera = main_camera
cursor = game_objects.Cursor(main=True)


game_escape = game_objects.Window("escape")
game_objects.game_escape = game_escape
world_loader = game_objects.WorldLoader()
game_objects.world_loader = world_loader
tile_render = game_objects.TileRender()
game_objects.tile_render = tile_render
game_objects.cursor = cursor


click = True
click_r = True
shift = True

while True:
    pygame.event.pump()
    window_surface.fill(bg_blue)
    if (pygame.mouse.get_pressed()[2] and click_r) or (pygame.key.get_pressed()[K_LSHIFT] and shift):
        back_manager.go_back()

    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                game_objects.add_window(game_escape)
            if event.key == K_F11:
                pygame.quit()
                sys.exit()
            if event.key == K_l:
                world_loader.load("worlds/test.txt")
            if event.key == K_F3:
                game_objects.debug = not game_objects.debug

    cursor.update(main_camera)
    world_loader.update(main_camera, cursor.pos)
    main_camera.update()
    tile_render.draw(main_camera)

    # balls7 = game_objects.tile_pos(pygame.mouse.get_pos(), main_camera)
    # pygame.draw.circle(window_surface, white, balls7, 10)
    # # print(pygame.mouse.get_pos())
    cursor.draw(window_surface)
    window_manager.update()
    for blit in game_objects.blit_buffer:
        window_surface.blit(blit[0], blit[1])
    game_objects.blit_buffer = []

    click = not pygame.mouse.get_pressed()[0]
    click_r = not pygame.mouse.get_pressed()[2]
    shift = not pygame.key.get_pressed()[K_LSHIFT]

    game_objects.click = click

    fps_text = basic_font.render(str(int(main_clock.get_fps())), True, white)
    window_surface.blit(fps_text, (0, window_height - 18))

    cursor_pos_text = basic_font.render(f"{int(cursor.pos[0])}, {int(cursor.pos[1])}", True, white)
    window_surface.blit(cursor_pos_text, (0, 0))

    pygame.display.update()
    timer.dt = main_clock.tick(timer.tick_speed) / 1000
