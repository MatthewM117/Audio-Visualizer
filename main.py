from AudioMetrics import *
import colorsys
import random
import pygame_gui
import tkinter as tk
from tkinter import filedialog
import wave
import contextlib

def random_colour():
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]

# librosa only supports WAV files
root = tk.Tk()
root.withdraw()

file_name = filedialog.askopenfilename()

song_name_one = file_name.split('.')
song_name = song_name_one[0].split('/')

with contextlib.closing(wave.open(file_name,'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)

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

circle_colour = (0, 0, 0)

poly = []
#polygon_colour_default = [52, 32, 150]
polygon_colour_default = [50, 205, 50]
polygon_bass_colour = polygon_colour_default.copy()
poly_colour = polygon_colour_default.copy()
polygon_colour_vel = [0, 0, 0]

background_colour = [0, 0, 0]

bass_average = 0
bass_trigger = -30
bass_trigger_started = 0
min_decibel = -80
max_decibel = 80

circle_x = int(screen_width / 2)
circle_y = int(screen_height / 2)

min_radius = 0
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

# rotate all the bars around the center circle
num = 0
for g in bars_tmp:
    gr = []
    for c in g:
        gr.append(
            #RotatedMeanSoundbar(num, circle_y, c, (255, 0, 255), angle=0, width=8, max_height=370))
            RotatedMeanSoundbar(circle_x + radius * math.cos(math.radians(angle - 90)), circle_y + radius * math.sin(math.radians(angle - 90)), c, (255, 0, 255), angle=angle, width=8, max_height=370))
        angle += angle_dt
        num += 100

    bars.append(gr)

pygame.mixer.music.load(file_name)
pygame.mixer.music.play(0)

def string_to_int_array(input_text):
    if not ',' in input_text:
        return None
    int_array = input_text.split(',')
    #int_array = [int(x.strip()) for x in int_array]

    new_array = []
    for x in int_array:
        try:
            new_array.append(int(x))
        except ValueError:
            print('Not valid integer.')
            return None
    return new_array

# gui

settings_screen_width = int(info.current_w / 1.2)
settings_screen_height = int(info.current_h / 1.2)
settings_window_size = (settings_screen_width, settings_screen_height)
gui_manager = pygame_gui.UIManager(settings_window_size)

# buttons 

toggle_circle_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 100), (200, 50)), text='Toggle Circular Shape', manager=gui_manager)
toggle_random_colours_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 150), (200, 50)), text='Toggle Random Colours', manager=gui_manager)
toggle_randomize_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((settings_screen_width - 250, 100), (200, 50)), text='Toggle Randomize', manager=gui_manager)

# colour input box

colour_text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((0, 50), (100, 50)), manager=gui_manager)
colour_preview_size = 25
colour_preview_rect = pygame.Rect(100, 60, colour_preview_size, colour_preview_size)
colour_preview_colour = polygon_colour_default

# custom bg input box
bg_text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((0, 525), (100, 50)), manager=gui_manager)

# custom angle input box
angle_text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((0, 300), (100, 50)), manager=gui_manager)

# custom radius input box
radius_text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((0, 450), (100, 50)), manager=gui_manager)

font = pygame.font.SysFont("Arial", 15)
text_surface = font.render("Choose base colour (r, g, b):", True, (255, 255, 255))

cust_font = pygame.font.SysFont("Arial", 20)
customization_title = cust_font.render("Customization", True, (255, 255, 255))

custom_angle_title = font.render("Custom Angle (degrees, 0-360):", True, (255, 255, 255))

angle_slider_text = font.render("Change Angle:", True, (255, 255, 255))

radius_slider_text = font.render("Change Radius:", True, (255, 255, 255))

custom_radius_text = font.render("Custom Radius (0-300):", True, (255, 255, 255))

custom_bg_text = font.render("Change Background Colour (r, g, b):", True, (255, 255, 255))

custom_width_text = font.render("Change Width:", True, (255, 255, 255))

default_angle = random.uniform(0, 360)
default_width = random.uniform(0, 500)

angle_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((0, 225), (200, 50)),
    start_value=default_angle,
    value_range=(0.0, 360.0),
    manager=gui_manager
)

radius_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((0, 375), (200, 50)),
    start_value=radius,
    value_range=(0.0, 300.0),
    manager=gui_manager
)

width_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((settings_screen_width - 250, 50), (200, 50)),
    start_value=default_width,
    value_range=(0.0, 500.0),
    manager=gui_manager
)

# settings

show_circle = True
morph = False
custom_angle = 0 # in degrees
custom_radius = -1 # -1 means use default radius
show_random_colours = True
show_settings = True
bar_width = 10
randomize = False

prev = custom_angle
prev_width = bar_width
first_time = True

custom_angle = default_angle
morph = True

change_angle_debounce = False

# time progress bar
pb_width = 300
pb_height = 20
pb_x = screen_width - 320
pb_y = screen_height - 50
pb_bg = [169, 169, 169]
pb_fg = [211, 211, 211]

def convert_to_minutes(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def draw_progress_bar(current_time, song_length, song_title):
    progress = current_time / song_length

    bar_progress = int(progress * pb_width)

    pygame.draw.rect(screen, pb_bg, (pb_x, pb_y, pb_width, pb_height)) # background bar

    pygame.draw.rect(screen, pb_fg, (pb_x, pb_y, bar_progress, pb_height)) # duration bar

    # Draw the current time
    current_time = math.floor(current_time)
    font = pygame.font.Font(None, 25)
    current_time_text = font.render(convert_to_minutes(current_time), True, [255, 255, 255])
    current_time_rect = current_time_text.get_rect()
    current_time_rect.center = (pb_x + bar_progress, pb_y + pb_height + 10)
    screen.blit(current_time_text, current_time_rect)

    # Draw the total time
    song_length = math.floor(song_length)
    total_time_text = font.render(convert_to_minutes(song_length), True, [255, 255, 255])
    total_time_rect = total_time_text.get_rect()
    total_time_rect.center = ((pb_x + pb_width) - 30, pb_y + pb_height - 30)
    screen.blit(total_time_text, total_time_rect)

    # Draw song name
    total_time_text = font.render(song_title[-1].replace('_', ' '), True, [255, 255, 255])
    total_time_rect = total_time_text.get_rect()
    total_time_rect.center = (pb_x + 60, pb_y + pb_height - 30)
    screen.blit(total_time_text, total_time_rect)

running = True
while running:
    bass_average = 0
    poly = []
    ticks = pygame.time.get_ticks()
    delta_time = (ticks - last_frame_ticks) / 1000.0
    last_frame_ticks = ticks
    time += delta_time
    screen.fill(background_colour)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element == toggle_circle_button:
                show_circle = not show_circle
            elif e.ui_element == toggle_random_colours_button:
                show_random_colours = not show_random_colours
            elif e.ui_element == toggle_randomize_button:
                randomize = not randomize

        elif e.type == pygame.KEYDOWN and e.key == pygame.K_h:
            show_settings = not show_settings

        elif e.type == pygame.KEYDOWN and e.key == pygame.K_q:
            running = False

        elif e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            #print(colour_text_box.text)
            if colour_text_box.is_focused:
                rgb_list = string_to_int_array(colour_text_box.text)
                if isinstance(rgb_list, list):
                    if all(isinstance(x, int) for x in rgb_list):
                        polygon_colour_default = rgb_list
                    else:
                        print("invalid colour")
                else:
                    print("invalid colour")

            elif bg_text_box.is_focused:
                rgb_list = string_to_int_array(bg_text_box.text)
                if isinstance(rgb_list, list):
                    if all(isinstance(x, int) for x in rgb_list):
                        background_colour = rgb_list
                    else:
                        print("invalid colour")
                else:
                    print("invalid colour")

            elif angle_text_box.is_focused:
                try:
                    custom_angle = float(angle_text_box.text)
                    angle_slider.set_current_value(custom_angle, False)
                    morph = True
                except ValueError:
                    print('Invalid float.')

            elif radius_text_box.is_focused:
                try:
                    custom_radius = float(radius_text_box.text)
                    radius_slider.set_current_value(custom_radius, False)
                except ValueError:
                    print('Invalid float.')
                
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
            if show_random_colours:
                polygon_bass_colour = random_colour()
            else:
                polygon_bass_colour = polygon_colour_default
            bass_trigger_started = 0

        if polygon_bass_colour is None:
            if show_random_colours:
                polygon_bass_colour = random_colour()
            else:
                polygon_bass_colour = polygon_colour_default
            change_angle_debounce = False
        
        new_radius = min_radius + int(bass_average * ((max_radius - min_radius) / (max_decibel - min_decibel)) + (max_radius - min_radius))
        radius_vel = (new_radius - radius) / 0.15

        if not change_angle_debounce and randomize:
            change_angle_debounce = True
            custom_angle = random.uniform(0, 360)
            angle_slider.set_current_value(custom_angle, False)
            bar_width = random.uniform(0, 500)
            width_slider.set_current_value(bar_width, False)
            custom_radius = random.uniform(0, 300)
            radius_slider.set_current_value(custom_radius, False)
            morph = True

        #if show_random_colours:
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

    num = 0
    for a in bars:
        if custom_radius != -1:
            radius = custom_radius
        for b in a:
            if show_circle:
                b.x, b.y = circle_x + radius * math.cos(math.radians(b.angle - 90)), circle_y + radius * math.sin(math.radians(b.angle - 90))
            else:
                b.x = num
                b.y = screen_height / 2
            b.update_bar()
            num += 100

            poly.append(b.rect.points[3])
            poly.append(b.rect.points[2])

    # morph the bars
    if morph:
        if custom_radius != -1:
            radius = custom_radius
        bars = []
        for g in bars_tmp:
            gr = []
            for c in g:
                gr.append(
                    RotatedMeanSoundbar(circle_x + radius * math.cos(math.radians(angle - 90)), circle_y + radius * math.sin(math.radians(angle - 90)), c, (255, 0, 255), angle=angle, width=bar_width, max_height=370))
                    #RotatedMeanSoundbar(0, 0, c, 0, 0, width=8, max_height=370))
                if custom_angle == 0:
                    angle += random.uniform(0, 360)
                else:
                    angle += custom_angle

            bars.append(gr)
        morph = False

    custom_angle = angle_slider.get_current_value()
    custom_radius = radius_slider.get_current_value()
    bar_width = width_slider.get_current_value()
    if custom_angle != prev and not first_time:
        morph = True
    
    if bar_width != prev_width and not first_time:
        morph = True

    prev = custom_angle
    prev_width = bar_width
    first_time = False

    pygame.draw.polygon(screen, poly_colour, poly)
    #pygame.draw.circle(screen, circle_colour, (circle_x, circle_y), int(radius))

    pygame.draw.rect(screen, colour_preview_colour, colour_preview_rect)

    if show_settings:
        gui_manager.update(delta_time)
        gui_manager.draw_ui(screen)

        # draw all the text
        screen.blit(text_surface, (0, 30))
        screen.blit(customization_title, (0, 0))
        screen.blit(custom_angle_title, (0, 280))
        screen.blit(angle_slider_text, (0, 205))
        screen.blit(radius_slider_text, (0, 355))
        screen.blit(custom_radius_text, (0, 430))
        screen.blit(custom_bg_text, (0, 505))
        screen.blit(custom_width_text, (settings_screen_width - 250, 30))

        draw_progress_bar(time, duration, song_name)

        colour_preview_colour = polygon_colour_default
    else:
        colour_preview_colour = background_colour

    pygame.display.flip()

pygame.quit()