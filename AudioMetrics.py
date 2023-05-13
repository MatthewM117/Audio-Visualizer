import math
import matplotlib.pyplot as pyplot
import numpy
import librosa.display
import pygame

def clamp(min, max, value):
    if value < min:
        return min
    
    if value > max:
        return max
    
    return value

def shift(coords, delta):
    return coords[0] + delta[0], coords[1] + delta[1]

def binary_search(array, value):
    '''
    standard binary search algorithm
    '''
    length = len(array)
    min = 0
    max = length - 1
    i = int(length / 2)
    done = False

    if value > array[length - 1]:
        return max
    
    if value < array[0]:
        return 0
    
    while not done:
        length = len(array)

        if min == length - 2:
            return length - 1
        
        if array[i] < value < array[i + 1] or array[i] == value:
            return i
        
        if array[i] > value:
            max = i
        else:
            min = i

        i = int((min + max) / 2)

def rotation_matrix(coords, theta):
    '''
    rotation matrix:
    R(theta) = | cosTheta    -sinTheta |
               | sinTheta    cosTheta  | 
    '''
    sinTheta = math.sin(theta)
    cosTheta = math.cos(theta)

    # return the rotation matrix multiplied by x and y
    return (cosTheta * coords[0] - sinTheta * coords[1], sinTheta * coords[0] + cosTheta * coords[1])


class AudioMetrics:
    def __init__(self):
        self.frequency_ratio = 0 # frequencies array
        self.time_ratio = 0 # time periods array
        self.spectrogram = None # a matrix composed of decibel values according to the above information

    def config(self, file_name):
        '''
        load all the info from the file
        '''
        time_series, sample_rate = librosa.load(file_name)

        amplitude_matrix = numpy.abs(librosa.stft(time_series, hop_length=512, n_fft=2048*4))

        self.spectrogram = librosa.amplitude_to_db(amplitude_matrix, ref=numpy.max) # amplitude to decibels

        frequencies = librosa.core.fft_frequencies(n_fft=2048*4)

        times = librosa.core.frames_to_time(numpy.arange(self.spectrogram.shape[1]), sr=sample_rate, hop_length=512, n_fft=2048*4)

        self.time_ratio = len(times)/times[len(times) - 1]

        self.frequency_ratio = len(frequencies)/frequencies[len(frequencies) - 1]

    def show(self):
        '''
        display the spectrogram/pyplot
        '''
        librosa.display.specshow(self.spectrogram, y_axis='log', x_axis='time')
        pyplot.title("spectrogram")
        pyplot.colorbar(format='%+2.0f dB')
        pyplot.tight_layout()
        pyplot.show()

    def get_db(self, time, frequency):
        '''
        return the specified decibel
        '''
        return self.spectrogram[int(frequency * self.frequency_ratio)][int(time * self.time_ratio)]
    
    def get_db_arr(self, time, frequencies):
        '''
        returns array of decibels at specified time
        '''
        db_array = []

        for i in frequencies:
            db_array.append(self.get_db(time, i))
        
        return db_array
    
class SoundBar:
    def __init__(self, x, y, frequency, colour, width=50, min_height=10, max_height=100, min_decibel=-80, max_decibel=0):
        self.x = x
        self.y = y
        self.frequency = frequency
        self.colour = colour
        self.width = width
        self.min_height = min_height
        self.max_height = max_height
        self.height = min_height
        self.min_decibel = min_decibel
        self.max_decibel = max_decibel
        self.decibel_height_ratio = (self.max_height - self.min_height) / (self.max_decibel - self.min_decibel)

    def update(self, dt, decibel):
        target_height = decibel * self.decibel_height_ratio + self.max_height
        speed = (target_height - self.height) / 0.1
        self.height += speed * dt
        self.height = clamp(self.min_height, self.max_height, self.height)

class MeanSoundBar(SoundBar):
    def __init__(self, x, y, rng, colour, width=50, min_height=10, max_height=100, min_decibel=-80, max_decibel=0):
        super().__init__(x, y, 0, colour, width, min_height, max_height, min_decibel, max_decibel)
        self.rng = rng
        self.mean = 0

    def super_update(self, dt, time, metrics):
        self.mean = 0
        for i in self.rng:
            self.mean += metrics.get_db(time, i)
        
        self.mean /= len(self.rng)
        self.update(dt, self.mean)

class RotatedMeanSoundbar(MeanSoundBar):
    def __init__(self, x, y, rng, colour, angle=0, width=50, min_height=10, max_height=100, min_decibel=-80, max_decibel=0):
        super().__init__(x, y, 0, colour, width, min_height, max_height, min_decibel, max_decibel)
        self.rect = None
        self.angle = angle
        self.rng = rng

    def update_bar(self):
        self.rect = Bar(self.x, self.y, self.width, self.height)
        self.rect.rotate(self.angle)

class Bar:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.points = []
        self.origin = [self.width / 2, 0]
        self.offset = [self.origin[0] + x, self.origin[1] + y]
        self.rotate(0)

    def rotate(self, angle):
        format = [
            (-self.origin[0], self.origin[1]),
            (-self.origin[0] + self.width, self.origin[1]),
            (-self.origin[0] + self.width, self.origin[1] - self.height),
            (-self.origin[0], self.origin[1] - self.height)
        ]

        self.points = [shift(rotation_matrix(coords, math.radians(angle)), self.offset) for coords in format]

    def draw(self, screen):
        pygame.draw.polygon(screen, (255, 255, 0), self.points)