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


def rotate_image_alt(image):
    '''Rotate image alt, based on longest hough line'''
    img_before = cv2.imread(image)

    
    img_gray = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
    img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
    cv2.imwrite(image+'_edges.png', img_edges)
    lines = cv2.HoughLinesP(img_edges, 1, math.pi / 180.0, 100, minLineLength=100, maxLineGap=10)
    
    # draw lines on image
    all_lines_img = cv2.imread(image)
    if (lines is not None):
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(all_lines_img, (x1, y1), (x2, y2), (255, 0, 0), 3)
    cv2.imwrite(image+'_all_lines.png', all_lines_img)


    image_info = get_image_info(image)
    # get longest line
    longest_line = None
    longest_line_distance = 0
    if (lines is not None):
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # not border
            if (x1 == image_info.left or x1 == image_info.right or x2 == image_info.left or x2 == image_info.right):
                continue
            line_distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if (longest_line is None):
                longest_line = (x1, y1, x2, y2)
                longest_line_distance = line_distance
            elif (line_distance > longest_line_distance):
                longest_line = (x1, y1, x2, y2)
                longest_line_distance = line_distance
    
    if not longest_line:
        return
    
    # get angle
    angle = math.degrees(math.atan2(longest_line[3] - longest_line[1], longest_line[2] - longest_line[0]))

    # if (median_angle >= 0):
    # 	img_rotated = ndimage.rotate(img_before, median_angle)
    # else:
    # 	img_rotated = ndimage.rotate(img_before, 180+median_angle)
    
    print("Angle is {}".format(angle))

    # showImage(img_rotated)
    img_rotated = ndimage.rotate(img_before, angle)
    
    cv2.imwrite(image+'_rotated_alt.png', img_rotated)

    # draw longest line
    cv2.line(img_before, (longest_line[0], longest_line[1]), (longest_line[2], longest_line[3]), (255, 0, 0), 3)
    cv2.imwrite(image+'_lines_alt.png', img_before)



def rotate_image_remove_outliers(set:list):
    '''Removes outliers from set'''

    aux_set = set
    removed_pixel = True
    # while outliers detected
    # remove outliers
    j = 0
    while removed_pixel and aux_set:
        j+=1
        new_set = []

        # average displacement of x coordinates
        x_avg = 0
        for i in range(1,len(aux_set)):
            x_avg += aux_set[i-1][0] - aux_set[i][0] 
        x_avg = x_avg / (len(aux_set)-1)

        # remove outlier pixels, using average displacement
        for i in range(1,len(aux_set)):
            if abs(aux_set[i-1][0] - aux_set[i][0] - x_avg) < x_avg:
                new_set.append(aux_set[i])

        #check first point
        if abs(aux_set[0][0] - aux_set[1][0] - x_avg) < x_avg:
            new_set = [aux_set[0]] + new_set

        if len(new_set) == len(aux_set):
            removed_pixel = False
        aux_set = new_set
    return new_set



def rotate_image(image:str,line_quantetization:int=100):
    '''Finds the angle of the image and rotates it
    
    Based on the study by: W. Bieniecki, Sz. Grabowski, W. Rozenberg 
    
    Steps:
    1. Crop image
    2. Grey Scale image
    3. Binarize image
    4. For each line (y coordinate; taking steps according to line_quantetization)
        4.1 Get first black pixel in each line
    5. Calculate best list of sets of pixels
        5.1 Pixeis are ordered from left to right or right to left
    6. Remove outliers from set
    7. Find angle
    8. Rotate image
    '''
    
    img = cv2.imread(image)
    # crop margin
    img = img[0:img.shape[0], 50:img.shape[1]]
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary_img = cv2.threshold(gray_img, 128, 255, cv2.THRESH_OTSU)

    # get first black pixel in each line of image
    ## analyses lines acording to line_quantetization
    pixels = []

    step = math.floor(binary_img[1].shape[0]/line_quantetization)

    for y in range(0,binary_img[1].shape[0], step):
        for x in range(binary_img[1].shape[1]):
            if binary_img[1][y][x] == 0:
                pixels.append((x,y))
                break
    
    # estimate rotation direction
    ## TODO

    # make list of sets
    # each set is a list of pixels in x coordinates order (ascending or descending depending on rotation direction)
    sets = []
    for i in range(1,len(pixels)-1):
        new_set = [pixels[i]]
        for j in range(i,len(pixels)):
            if pixels[j][0] < new_set[-1][0]:
                new_set.append(pixels[j])
        sets.append(new_set)


    set = []
    # choose set with most elements
    for s in sets:
        if not set:
            set = s
        elif len(s) > len(set):
            set = s

    og_img = cv2.imread(image)

    # draw points from set
    for p in set:
        cv2.circle(og_img, (p[0]+50, p[1]), 7, (255, 0, 0), -1)

    cv2.imwrite(image + '_points_1.png', og_img)


    new_set = rotate_image_remove_outliers(set)


    # get extreme points
    left_most_point = new_set[0]
    right_most_point = new_set[-1]
    
    # find angle
    angle = math.degrees(math.atan((right_most_point[1] - left_most_point[1]) / (right_most_point[0] - left_most_point[0])))

    print('angle',angle)

    rotation_angle = 90 - abs(angle)

    img = ndimage.rotate(img, rotation_angle)
    cv2.imwrite(image + '_rotated.png', img)

    og_img = cv2.imread(image)

    # draw points from set
    for p in new_set:
        cv2.circle(og_img, (p[0]+50, p[1]), 7, (255, 0, 0), -1)

    cv2.imwrite(image + '_points.png', og_img)
        

    





