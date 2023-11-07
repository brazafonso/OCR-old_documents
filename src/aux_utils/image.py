import cv2
from PIL import Image
from ocr_box_module.ocr_box import OCR_Box
from aux_utils.box import *


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



