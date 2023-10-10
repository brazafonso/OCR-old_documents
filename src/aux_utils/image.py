from PIL import Image


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

def within_vertical_boxes(box1,box2):
    '''Check if boxes are within each other vertically'''
    if box1['top'] >= box2['top'] and box1['bottom'] <= box2['bottom']:
        return True
    elif box2['top'] >= box1['top'] and box2['bottom'] <= box1['bottom']:
        return True
    return False

def within_horizontal_boxes(box1,box2):
    '''Check if boxes are within each other horizontally'''
    if box1['left'] <= box2['left'] and box1['right'] >= box2['right']:
        return True
    elif box2['left'] <= box1['left'] and box2['right'] >= box1['right']:
        return True
    return False


def same_level_box(box1,box2):
    '''Check if two boxes are in the same level (horizontal and/or vertical)'''
    if within_horizontal_boxes(box1,box2) or within_vertical_boxes(box1,box2):
        return True
    return False


def is_inside_box(box,container):
    '''Check if box is inside container'''
    if box['left'] >= container['left'] and box['right'] <= container['right'] and box['top'] >= container['top'] and box['bottom'] <= container['bottom']:
        return True
    return False


def intersects_box(box1,box2):
    '''Check if box intersects another box'''
    intercept_vertical = (box1['top'] <= box2['top'] and box1['bottom'] >= box2['top']) or (box2['top'] <= box1['top'] and box2['bottom'] >= box1['top'])
    intercept_horizontal = (box1['left'] <= box2['right'] and box1['right'] >= box2['left']) or (box1['left'] <= box2['right'] and box1['right'] >= box2['right'])
    if intercept_horizontal and intercept_vertical:
        return True
    return False

def intersect_area_box(box1,box2):
    '''Get intersect area box between two boxes'''
    area_box = {
        'left':0,
        'right':0,
        'top':0,
        'bottom':0
    }
    
    if box1['left'] <= box2['left']:
        area_box['left'] = box2['left']
    else:
        area_box['left'] = box1['left']

    if box1['right'] >= box2['right']:
        area_box['right'] = box2['right']
    else:
        area_box['right'] = box1['right']

    if box1['top'] <= box2['top']:
        area_box['top'] = box2['top']
    else:
        area_box['top'] = box1['top']

    if box1['bottom'] >= box2['bottom']:
        area_box['bottom'] = box2['bottom']
    else:
        area_box['bottom'] = box1['bottom']
    return area_box

def remove_box_area(box,area):
    '''Remove area from box (only if intersect)'''
    intersect = intersects_box(box,area)
    inside = is_inside_box(box,area)
    if intersect and not inside:
        # Remove area from box
        ## area to the right
        if area['right'] > box['right']:
            box['right'] = area['left']
        ## area to the left
        if area['left'] < box['left']:
            box['left'] = area['right']
        ## area to the top
        if area['top'] > box['top']:
            box['bottom'] = area['top']
        ## area to the bottom
        if area['bottom'] < box['bottom']:
            box['top'] = area['bottom']
    return box
    

def box_is_smaller(box1,box2):
    '''Check if box1 is smaller than box2'''
    if (box1['right'] - box1['left']) * (box1['bottom'] - box1['top']) < (box2['right'] - box2['left']) * (box2['bottom'] - box2['top']):
        return True
    return False


def black_and_white(image_path):
    '''Convert image to black and white'''
    image = Image.open(image_path)
    image = image.convert('L')
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    return image


def get_image_info(image_path):
    '''Get image info'''
    image = Image.open(image_path)
    return {
        'width':image.width,
        'height':image.height
    }


def get_box_orientation(box):
    '''Get box orientation'''
    if box['width'] > box['height']:
        return 'horizontal'
    elif box['width'] < box['height']:
        return 'vertical'
    else:
        return 'square'
    
def is_aligned(box1,box2,orientation='horizontal',error_margin=0.1):
    '''Check if boxes are aligned'''
    if orientation == 'horizontal':
        if abs(1 - box1['top']/box2['top']) <= error_margin:
            return True
    elif orientation == 'vertical':
        if abs(1 - box1['left']/box2['left']) <= error_margin:
            return True
    return False


def join_boxes(box1,box2):
    '''Join two boxes'''
    box = {
        'left':0,
        'right':0,
        'top':0,
        'bottom':0
    }
    box['left'] = min(box1['left'],box2['left'])
    box['right'] = max(box1['right'],box2['right'])
    box['top'] = min(box1['top'],box2['top'])
    box['bottom'] = max(box1['bottom'],box2['bottom'])
    box['height'] = box['bottom'] - box['top']
    box['width'] = box['right'] - box['left']
    return box