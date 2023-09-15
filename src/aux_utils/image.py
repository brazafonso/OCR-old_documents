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