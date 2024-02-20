import cv2
from PIL import Image
from ocr_box_module.ocr_box import OCR_Box
from aux_utils.box import *
from scipy import ndimage
import numpy as np


def get_concat_h(im1, im2,margin=0):
    '''Concatenate images horizontally'''
    dst = Image.new('RGB', (im1.width + im2.width + margin, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width + margin, 0))
    return dst


def split_page_columns(image_path,columns):
    '''Split image into columns images'''
    image = Image.open(image_path)
    columns_image = []
    for column in columns:
        columns_image.append(image.crop((column[0][0],column[0][1],column[1][0],column[1][1])))
    return columns_image

def concatentate_columns(columns):
    '''Concatenate columns images horizontally in a single image'''
    image = None
    if columns:
        image = columns[0]
        for column in columns[1:]:
            image = get_concat_h(image,column,15)
    return image



def black_and_white(image_path):
    '''Convert image to black and white'''
    image = Image.open(image_path)
    image = image.convert('L')
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    return image


def get_image_info(image_path:str)->Box:
    '''Get image info'''
    image = Image.open(image_path)
    image_info = Box(0,image.width,0,image.height)
    return image_info



def calculate_dpi(image_info:Box,dimensions:Box)->float:
    '''Calculate dpi'''
    dpi = (image_info.width/dimensions.width + image_info.height/dimensions.height) / 2
    return dpi





def rotate_image(image:str,line_quantetization:int=200):
    '''Finds the angle of the image and rotates it
    
    Based on the study by: W. Bieniecki, Sz. Grabowski, W. Rozenberg '''
    
    img = cv2.imread(image)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary_img = cv2.threshold(gray_img, 128, 255, cv2.THRESH_OTSU)

    # get first black pixel in each line of image
    ## analyses lines acording to line_quantetization
    pixels = []

    for y in range(0,binary_img[1].shape[1], binary_img[1].shape[1]//line_quantetization):
        for x in range(binary_img[1].shape[0]):
            if binary_img[1][y][x] == 0:
                pixels.append((x,y))
                break
    
    # estimate rotation direction
    ## TODO

    # make to sets of pixels
    ## set with increasing x, from bottom to top
    ## second set, others
    set_1 = []
    set_2 = []

    for i in range(1,len(pixels)):
        if pixels[i][0] < pixels[i-1][0]:
            set_1.append(pixels[i])

    for pixel in pixels:
        if not pixel in set_1:
            set_2.append(pixel)

    set = None
    # choose more vertical set
    if len(set_1) > len(set_2):
        set = set_1
    else:
        set = set_2

    # average displacement of x coordinates
    x_avg = 0
    for i in range(len(set)-1):
        x_avg += set[i+1][0] - set[i][0]
    x_avg = x_avg / (len(set)-1)

    # remove outlier pixels, using average displacement
    new_set = [set[0]]
    for i in range(1,len(set)-1):
        if abs(set[i][0] - set[i-1][0] - x_avg) > 0.1*x_avg:
            new_set.append(set[i])

    # get extreme points
    left_most_point = new_set[0]
    right_most_point = new_set[-1]
    
    # find angle
    angle = math.degrees(math.atan((right_most_point[1] - left_most_point[1]) / (right_most_point[0] - left_most_point[0])))

    print('angle',angle)

    rotation_angle = 90 - abs(angle)

    img = ndimage.rotate(img, rotation_angle)
    cv2.imwrite(image + '_rotated.png', img)
        

    





