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


def inside_box(box,container):
    '''Check if box is inside container'''
    if box['left'] >= container['left'] and box['right'] <= container['right'] and box['top'] >= container['top'] and box['bottom'] <= container['bottom']:
        return True
    return False


def intercept_box(box1,box2):
    '''Check if box intercepts container'''
    intercept_vertical = (box1['top'] >= box2['bottom'] and box1['bottom'] <= box2['bottom']) or (box1['top'] >= box2['top'] and box1['bottom'] <= box2['top'])
    intercept_horizontal = (box1['left'] <= box2['right'] and box1['right'] >= box2['right']) or (box1['left'] <= box2['left'] and box1['right'] >= box2['left'])
    if intercept_horizontal and intercept_vertical:
        return True
    return False

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