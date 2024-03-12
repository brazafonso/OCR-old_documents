import os
import cv2
from .box import *
from scipy import ndimage
import numpy as np


def get_concat_h(im1, im2,margin=0):
    '''Concatenate images horizontally'''
    dst = np.zeros((im1.shape[0], im1.shape[1] + im2.shape[1] + margin, 3), dtype=np.uint8)
    dst[:, :im1.shape[1], :] = im1
    dst[:, im1.shape[1] + margin:, :] = im2
    return dst


def split_page_columns(image_path,columns):
    '''Split image into columns images'''
    image = cv2.imread(image_path)
    columns_image = []
    for column in columns:
        columns_image.append(image[column[0][1]:column[1][1],column[0][0]:column[1][0]])
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
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY)
    return thresh


def get_image_info(image_path:str)->Box:
    '''Get image info'''
    image = cv2.imread(image_path)
    image_info = Box(0,len(image[0]),0,len(image))
    return image_info



def calculate_dpi(image_info:Box,dimensions:Box)->float:
    '''Calculate dpi'''
    dpi = (image_info.width/dimensions.width + image_info.height/dimensions.height) / 2
    return dpi



def create_vertical_aligned_pixel_set(pixels:list,image_shape:tuple,direction:str='clockwise'):
    '''Create pixel set
    
    Tries to create a set of pixels that are vertically aligned, with no great x variance
    Also does not add pixels that are too far apart from each other (using image shape)'''
    pixel_set = [pixels[0]]
    pixel_set_x_var_sum = 0
    for i in range(1,len(pixels)):
        if (direction == 'clockwise' and pixels[i][0] < pixel_set[-1][0]) or (direction == 'counter_clockwise' and pixels[i][0] > pixel_set[-1][0]):
            # check x distance relative to image shape
            if abs(pixels[i][0] - pixel_set[-1][0])/image_shape[1] <= 0.1:
                cw_set_x_avg = pixel_set_x_var_sum/(len(pixel_set))
                # check x variance
                if not pixel_set_x_var_sum or (abs(pixels[i][0] - pixel_set[-1][0]) <= cw_set_x_avg):
                    pixel_set_x_var_sum += abs(pixels[i][0] - pixel_set[-1][0])
                    pixel_set.append(pixels[i])
    return pixel_set


def calculate_rotation_direction(image_path:str,line_quantetization:int=200,debug=False):
    '''Calculate rotation direction (counter-clockwise or clockwise)
    
    On left margin of image compare the groups of ordered black pixels by x coordinate
    If the largest group is x descengin (from top to bottom) the direction is clockwise, else counter-clockwise'''
    test_path = image_path.split('/')[:-1]
    test_path = '/'.join(test_path)
    if not os.path.exists(f'{test_path}/test'):
        os.mkdir(f'{test_path}/test')
    test_path = f'{test_path}/test/{image_path.split("/")[-1]}'

    direction = 'clockwise'
    image = cv2.imread(image_path)
    # crop margin
    image = image[0:image.shape[0], 50:image.shape[1]]
    # grey scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # binarize, clean salt and pepper noise and dilate
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)[1]
    filtered = ndimage.median_filter(thresh, 10)
    dilation = cv2.dilate(filtered, np.ones((0,10),np.uint8),iterations=3)
    transformed_image = dilation

    if debug:
        cv2.imwrite(f'{test_path}_thresh.png',thresh)
        cv2.imwrite(f'{test_path}_filtered.png',filtered)
        cv2.imwrite(f'{test_path}_dilation.png',dilation)

    # calculate sets
    pixels = []
    step = math.floor(transformed_image.shape[0]/line_quantetization)

    for y in range(0,transformed_image.shape[0], step):
        for x in range(transformed_image.shape[1]):
            if transformed_image[y][x] == 255:
                pixels.append((x,y))
                break

    if debug:
    # draw pixels
        copy_image = cv2.imread(f'{test_path}_dilation.png')
        for pixel in pixels:
            cv2.circle(copy_image, pixel, 7, (0,0,255), -1)
        cv2.imwrite(f'{test_path}_pixels.png',copy_image)

    # make list of sets
    # each set is a list of pixels in x coordinates order (ascending or descending depending on rotation direction)
    clockwise_sets = []
    counter_clockwise_sets = []
    for i in range(1,len(pixels)):
        new_cw_set = create_vertical_aligned_pixel_set(pixels[i:],transformed_image.shape,'clockwise')
        new_ccw_set = create_vertical_aligned_pixel_set(pixels[i:],transformed_image.shape,'counter_clockwise')

        clockwise_sets.append(pixels_set_remove_outliers(new_cw_set,'clockwise'))
        counter_clockwise_sets.append(pixels_set_remove_outliers(new_ccw_set,'counter_clockwise'))


    # find biggest sets
    biggest_clockwise_set = max(clockwise_sets, key=len)
    biggest_counter_clockwise_set = max(counter_clockwise_sets, key=len)
    print('test','clockwise',len(biggest_clockwise_set))
    print('counter_clockwise',len(biggest_counter_clockwise_set))

    if debug:
    # draw biggest sets
        for pixel in biggest_clockwise_set:
            cv2.circle(image, pixel, 7, (0,0,255), -1)
        for pixel in biggest_counter_clockwise_set:
            cv2.circle(image, pixel, 7, (0,255,0), -1)
        cv2.imwrite(f'{test_path}_biggest_sets.png',image)

    if len(biggest_clockwise_set) >= len(biggest_counter_clockwise_set):
        direction = 'clockwise'
    else:
        direction = 'counter_clockwise'

    return direction


def pixels_set_remove_outliers(set:list,direction:str='clockwise'):
    '''Removes outliers from set'''

    aux_set = set
    removed_pixel = True
    # while outliers detected
    # remove outliers
    j = 0
    x_avg = 0
    while removed_pixel and len(aux_set) > 1:
        j+=1
        new_set = []

        # average displacement of x coordinates
        x_avg = 0
        for i in range(1,len(aux_set)):
            x1 = aux_set[i-1][0]
            x2 = aux_set[i][0]
            if direction == 'counter_clockwise':
                x1,x2 = x2,x1
            x_avg +=  x1 - x2
                
        x_avg = x_avg / (len(aux_set)-1)

        # remove outlier pixels, using average displacement
        for i in range(1,len(aux_set)):
            x1 = aux_set[i-1][0]
            x2 = aux_set[i][0]
            if direction == 'counter_clockwise':
                x1,x2 = x2,x1

            if abs(x1 - x2 - x_avg) <= x_avg:
                new_set.append(aux_set[i])

        x1 = aux_set[0][0]
        x2 = aux_set[1][0]
        if direction == 'counter_clockwise':
            x1,x2 = x2,x1
        #check first point
        if abs(x1 - x2 - x_avg) <= x_avg:
            new_set = [aux_set[0]] + new_set

        if len(new_set) == len(aux_set):
            removed_pixel = False
        aux_set = new_set

    # print('iterations',j,aux_set,x_avg)

    return aux_set


def rotate_image_alt(image):
    '''Rotate image alt, based on longest hough line'''
    test_path = image.split('/')[:-1]
    test_path = '/'.join(test_path)
    if not os.path.exists(f'{test_path}/test'):
        os.mkdir(f'{test_path}/test')
    test_path = f'{test_path}/test/{image.split("/")[-1]}'

    img_before = cv2.imread(image)

    # crop image (remove all margins to leave center)
    img_before = img_before[100:img_before.shape[0]-100, 200:img_before.shape[1]-200] 
    
    img_gray = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
    img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
    cv2.imwrite(test_path+'_edges.png', img_edges)
    lines = cv2.HoughLinesP(img_edges, 1, math.pi / 180.0, 100, minLineLength=100, maxLineGap=10)
    
    # draw lines on image
    all_lines_img = cv2.imread(image)
    if (lines is not None):
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(all_lines_img, (x1, y1), (x2, y2), (255, 0, 0), 3)
    cv2.imwrite(test_path+'_all_lines.png', all_lines_img)


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
    angle = abs(math.degrees(math.atan2(longest_line[3] - longest_line[1], longest_line[2] - longest_line[0])))

    # if (median_angle >= 0):
    # 	img_rotated = ndimage.rotate(img_before, median_angle)
    # else:
    # 	img_rotated = ndimage.rotate(img_before, 180+median_angle)
    
    print("Angle is {}".format(angle))

    img = cv2.imread(image)
    # showImage(img_rotated)
    img_rotated = ndimage.rotate(img, 90-angle)
    
    cv2.imwrite(test_path+'_rotated_alt.png', img_rotated)

    # draw longest line
    cv2.line(img_before, (longest_line[0], longest_line[1]), (longest_line[2], longest_line[3]), (255, 0, 0), 3)
    cv2.imwrite(test_path+'_lines_alt.png', img_before)







def rotate_image(image:str,line_quantetization:int=100,direction:str='auto',debug=False):
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

    test_path = image.split('/')[:-1]
    test_path = '/'.join(test_path)
    if not os.path.exists(f'{test_path}/test'):
        os.mkdir(f'{test_path}/test')
    test_path = f'{test_path}/test/{image.split("/")[-1]}'
    
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
    if direction == 'auto' or direction not in ['clockwise', 'counter_clockwise']:
        direction = calculate_rotation_direction(image, debug=debug)
    print('direction',direction)

    # make list of sets
    # each set is a list of pixels in x coordinates order (ascending or descending depending on rotation direction)
    sets = []
    for i in range(1,len(pixels)-1):
        new_set = create_vertical_aligned_pixel_set(pixels[i:], binary_img[1].shape, direction)
        sets.append(new_set)


    set = []
    # choose set with most elements
    for s in sets:
        if not set:
            set = s
        elif len(s) > len(set):
            set = s

    print('set',len(set))
    og_img = cv2.imread(image)



    new_set = pixels_set_remove_outliers(set,direction)

    if len(new_set) < 2:
        return img
    
    # get extreme points
    left_most_point = new_set[0]
    right_most_point = new_set[-1]
    
    # find angle
    angle = math.degrees(math.atan((right_most_point[1] - left_most_point[1]) / (right_most_point[0] - left_most_point[0])))

    print('angle',angle)

    rotation_angle = 90 - abs(angle)
    if direction == 'counter_clockwise':
        rotation_angle = -rotation_angle
    img = ndimage.rotate(og_img, rotation_angle)


    ## test images
    if debug:
        cv2.imwrite(test_path + '_rotated.png', img)

        # draw points from set
        for p in set:
            cv2.circle(og_img, (p[0]+50, p[1]), 7, (255, 0, 0), -1)

        cv2.imwrite(test_path + '_points_1.png', og_img)

        og_img = cv2.imread(image)

        # draw points from set
        for p in new_set:
            cv2.circle(og_img, (p[0]+50, p[1]), 7, (255, 0, 0), -1)

        cv2.imwrite(test_path + '_points.png', og_img)

    return img
        

    





