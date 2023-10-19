import cv2
from PIL import Image
from ocr_box_module.ocr_box import OCR_Box


def draw_bounding_boxes(ocr_results:OCR_Box,image_path:str,draw_levels=[2],conf=60,id=False):
    '''Draw bounding boxes on image of type MatLike from cv2\n
    Return image with bounding boxes'''

    img = cv2.imread(image_path)
    box_stack = [ocr_results]
    while box_stack:
        current_node = box_stack.pop()
        if current_node.level in draw_levels:
            # only draw text boxes if confidence is higher than conf
            if current_node.level == 5 and current_node.conf < conf:
                continue
            (x, y, w, h) = (current_node.box.left, current_node.box.top, current_node.box.width, current_node.box.height)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if id and current_node.id:
                img = cv2.putText(img, str(current_node.id), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        for child in current_node.children:
            box_stack.append(child)
    return img


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


def get_image_info(image_path):
    '''Get image info'''
    image = Image.open(image_path)
    return {
        'width':image.width,
        'height':image.height
    }



