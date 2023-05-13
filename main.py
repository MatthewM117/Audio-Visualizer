from AudioMetrics import *
import colorsys
import random
import pygame_gui

def random_colour():
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]

# librosa only supports WAV, FLAC, and OGG files
file_name = "bojack.wav"

metrics = AudioMetrics()
metrics.config(file_name)

pygame.init()
info = pygame.display.Info()
screen_width = int(info.current_w / 1.2)
screen_height = int(info.current_h / 1.2)
screen = pygame.display.set_mode([screen_width, screen_height])
ticks = pygame.time.get_ticks()
last_frame_ticks = ticks
time = 0

circle_colour = (40, 40, 40)

poly = []
polygon_colour_default = [255, 255, 255]
polygon_bass_colour = polygon_colour_default.copy()
poly_colour = polygon_colour_default.copy()
polygon_colour_vel = [0, 0, 0]

bass_average = 0
bass_trigger = -30
bass_trigger_started = 0
min_decibel = -80
max_decibel = 80

circle_x = int(screen_width / 2)
circle_y = int(screen_height / 2)

min_radius = 100
max_radius = 150
radius = min_radius
radius_vel = 0

bass = {"start": 50, "stop": 100, "count": 12}
heavy_area = {"start": 120, "stop": 250, "count": 40}
low_mids = {"start": 251, "stop": 2000, "count": 50}
high_mids = {"start": 2001, "stop": 6000, "count": 20}

frequency_groups = [bass, heavy_area, low_mids, high_mids]

bars = []
bars_tmp = []

length = 0

for group in frequency_groups:
    g = []
    s = group["stop"] - group["start"]
    count = group["count"]
    reminder = s % count
    step = int(s / count)
    rng = group["start"]

    for i in range(count):
        array = None

        if reminder > 0:
            reminder -= 1
            array = numpy.arange(start=rng, stop=rng + step + 2)
            rng += step + 3
        else:
            array = numpy.arange(start=rng, stop=rng + step + 1)
            rng += step + 2

        g.append(array)

        length += 1

    bars_tmp.append(g)

angle_dt = 360 / length
angle = 0

for g in bars_tmp:
    gr = []
    for c in g:
        gr.append(
            RotatedMeanSoundbar(circle_x + radius * math.cos(math.radians(angle - 90)), circle_y + radius * math.sin(math.radians(angle - 90)), c, (255, 0, 255), angle=angle, width=8, max_height=370))
        angle += angle_dt

    bars.append(gr)

pygame.mixer.music.load(file_name)
pygame.mixer.music.play(0)

def string_to_int_array(input_text):
    int_array = input_text.split(',')
    int_array = [int(x.strip()) for x in int_array]
    return int_array

# gui

settings_screen_width = int(info.current_w / 2.2)
settings_screen_height = int(info.current_h / 2.2)
settings_window_size = (settings_screen_width, settings_screen_height)
gui_manager = pygame_gui.UIManager(settings_window_size)

hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 0), (100, 50)), text='Say Hello', manager=gui_manager)

colour_text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((0, 50), (100, 50)), manager=gui_manager)
colour_preview_size = 25
colour_preview_rect = pygame.Rect(100, 60, colour_preview_size, colour_preview_size)
colour_preview_colour = polygon_colour_default

running = True
while running:
    bass_average = 0
    poly = []
    ticks = pygame.time.get_ticks()
    delta_time = (ticks - last_frame_ticks) / 1000.0
    last_frame_ticks = ticks
    time += delta_time
    screen.fill(circle_colour)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element == hello_button:
                print('Hello world!')

        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            print(colour_text_box.text)
            polygon_colour_default = string_to_int_array(colour_text_box.text)
            colour_preview_colour = string_to_int_array(colour_text_box.text)

        gui_manager.process_events(e)

    for a in bars:
        for b in a:
            b.super_update(delta_time, pygame.mixer.music.get_pos() / 1000.0, metrics)

    for b in bars[0]:
        bass_average += b.mean

    bass_average /= len(bars[0])

    if bass_average > bass_trigger:
        if bass_trigger_started == 0:
            bass_trigger_started = pygame.time.get_ticks()
        
        if (pygame.time.get_ticks() - bass_trigger_started) / 1000.0 > 2:
            polygon_bass_colour = random_colour()
            bass_trigger_started = 0

        if polygon_bass_colour is None:
            polygon_bass_colour = random_colour()
        
        new_radius = min_radius + int(bass_average * ((max_radius - min_radius) / (max_decibel - min_decibel)) + (max_radius - min_radius))
        radius_vel = (new_radius - radius) / 0.15

        polygon_colour_vel = [(polygon_bass_colour[x] - poly_colour[x]) / 0.15 for x in range(len(poly_colour))]
    
    elif radius > min_radius:
        bass_trigger_started = 0
        polygon_bass_colour = None
        radius_vel = (min_radius - radius) / 0.15
        polygon_colour_vel = [(polygon_colour_default[x] - poly_colour[x]) / 0.15 for x in range(len(poly_colour))]
    
    else:
        bass_trigger_started = 0
        poly_colour = polygon_colour_default.copy()
        polygon_bass_colour = None
        polygon_colour_vel = [0, 0, 0]
        radius_vel = 0
        radius = min_radius

    radius += radius_vel * delta_time

    for x in range(len(polygon_colour_vel)):
        value = polygon_colour_vel[x] * delta_time + poly_colour[x]
        poly_colour[x] = value

    for a in bars:
        for b in a:
            b.x, b.y = circle_x + radius * math.cos(math.radians(b.angle - 90)), circle_y + radius * math.sin(math.radians(b.angle - 90))
            b.update_bar()

            poly.append(b.rect.points[3])
            poly.append(b.rect.points[2])

    pygame.draw.polygon(screen, poly_colour, poly)
    pygame.draw.circle(screen, circle_colour, (circle_x, circle_y), int(radius))

    pygame.draw.rect(screen, colour_preview_colour, colour_preview_rect)

    gui_manager.update(delta_time)
    gui_manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()