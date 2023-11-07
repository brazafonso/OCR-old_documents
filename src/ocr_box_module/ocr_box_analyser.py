import re
import pytesseract
import cv2
import jellyfish
from pytesseract import Output
from PIL import Image
from aux_utils.page_tree import *
from aux_utils.image import *
from aux_utils.box import *
from ocr_box_module.ocr_box import *




def analyze_text(ocr_results:OCR_Box):
    '''Analyse text from ocr_results and return text data as dict\n
    Tries to find info about normal text size, number of lines and number of columns\n'''
    number_columns = 0

    lines = ocr_results.get_boxes_level(4)
    left_margin_n = {}
    right_margin_n = {}

    normal_text_size = None
    
    # save text sizes and margins
    for line in lines:
        left_margin = round(line.box.left,-1)
        if left_margin not in left_margin_n:
            left_margin_n[left_margin] = 0
        left_margin_n[left_margin] += 1

        right_margin = round((line.box.left + line.box.width),-1)
        if right_margin not in right_margin_n:
            right_margin_n[right_margin] = 0
        right_margin_n[right_margin] += 1

        lmh = line.calculate_mean_height()
        line.mean_height = lmh
        if normal_text_size:
            normal_text_size += lmh
            normal_text_size /= 2
        else:
            normal_text_size = lmh
    
    print('Left margin:',left_margin_n)
    print('Right margin:',right_margin_n)
    print('Lines:',len(lines))
    
    # estimate normal text size
    normal_text_gap = None

    last_block = None
    last_top = None
    last_line = None
    last_paragraph = None

    # estimate normal text gap
    for line in lines:
        if last_block:
            if line.block_num == last_block and line.par_num == last_paragraph and line.line_num == last_line + 1 and line.is_text_size(normal_text_size,mean_height=line.mean_height):
                if normal_text_gap:
                    normal_text_gap += line.box.top - last_top - normal_text_size
                    normal_text_gap /= 2
                else:
                    normal_text_gap = line.box.top - last_top - normal_text_size
            
        last_block = line.block_num
        last_top = line.box.top
        last_line = line.line_num
        last_paragraph = line.par_num

    # estimate number of lines
    highest_normal_text  = None
    lowest_normal_text = None

    ## find highest and lowest normal text
    for line in lines:
        if line.is_text_size(normal_text_size,mean_height=line.mean_height):
            if not highest_normal_text or line.box.top <= highest_normal_text:
                highest_normal_text = line.box.top
            if not lowest_normal_text or line.box.top+normal_text_size >= lowest_normal_text:
                lowest_normal_text = line.box.top+normal_text_size
    number_lines = (lowest_normal_text - highest_normal_text) // (normal_text_size + normal_text_gap)


    # estimate number of columns
    probable_columns = sorted([k for k in sorted(left_margin_n, reverse=True,key=left_margin_n.get) if left_margin_n[k]>=0.45*number_lines])
    number_columns = len(probable_columns)

    columns = []

    # create columns bounding boxes
    for i in range(len(probable_columns)):
        if i < len(probable_columns)-1:
            left = probable_columns[i]*0.98
            right = probable_columns[i+1]*1.02
            top = highest_normal_text*0.98
            bottom = lowest_normal_text*1.02
            columns.append(((left,top),(right,bottom)))
        # last column
        else:
            left = probable_columns[i]*0.98
            right = max(right_margin_n.keys())*1.02
            top = highest_normal_text*0.98
            bottom = lowest_normal_text*1.02
            columns.append(((left,top),(right,bottom)))
                


    text = f'''
    Normal text size: {normal_text_size}
    Normal text gap: {normal_text_gap}
    Max number of lines : {number_lines}
    Number of columns: {number_columns}
    Columns: {columns}
'''
    print('Analysed results:',text)

    return {
        'normal_text_size':normal_text_size,
        'normal_text_gap':normal_text_gap,
        'number_lines':number_lines,
        'number_columns':number_columns,
        'columns':columns
    }




def improve_bounds_precision(ocr_results,target_image_path,progress_key,window):
    'Rerun tesseract on within the boundings of a text box to improve its width and height precision'
    progress_text = f'Progress: 0 / {len(ocr_results["text"])}'
    window[progress_key].update(progress_text)
    window.refresh()
    original_img = Image.open(target_image_path)
    for i in range(len(ocr_results['text'])):
        if ocr_results[i].level == 5 and ocr_results[i].conf > 60:
            (x, y, w, h) = (ocr_results[i].left, ocr_results[i].top, ocr_results[i].width, ocr_results[i].height)
            img = original_img.crop((x-0.2*w,y-0.2*h,x+w*1.2,y+h*1.2))
            new_values = pytesseract.image_to_data(img, output_type=Output.DICT,config='--psm 8',lang='por')
            print(ocr_results[i].text)
            print(new_values['text'])
            print(new_values['conf'])
            for j in range(len(new_values['text'])):
                if new_values['level'][j] == 5 and jellyfish.levenshtein_distance(new_values['text'][j],ocr_results[i].text) < len(ocr_results[i].text)*0.3:
                    print('Updated:',ocr_results[i].text,new_values['text'][j])
                    print(' Old:',ocr_results[i].width,ocr_results[i].height)
                    print(' New:',new_values['width'][j],new_values['height'][j])
                    ocr_results[i].width = new_values['width'][j]
                    ocr_results[i].height = new_values['height'][j]
                    break
        progress_text = f'Progress: {i} / {len(ocr_results["text"])}'
        window[progress_key].update(progress_text)
        window.refresh()
    return ocr_results












def join_aligned_delimiters(delimiters:list[OCR_Box],orientation='horizontal'):
    '''Join aligned delimiters\n'''
    aligned_delimiters = []
    for delimiter in delimiters:
        delimiter_box = delimiter.box
        delimiter_box.right = delimiter_box.left + delimiter_box.width
        delimiter_box.bottom = delimiter_box.top + delimiter_box.height
        if not aligned_delimiters:
            aligned_delimiters.append(delimiter_box)
        else:
            joined = False
            for aligned in aligned_delimiters:
                if delimiter_box.is_aligned(aligned,orientation):
                    aligned.join(delimiter_box)
                    joined = True
                    break
            if not joined:
                aligned_delimiters.append(delimiter_box)
    return aligned_delimiters

    

def estimate_journal_header(ocr_results:OCR_Box,image_info:Box):
    '''Estimate journal header blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''

    header = None

    # get delimiter blocks
    search_area = Box(0,image_info.width,0,image_info.height*0.5) 
    delimiters = ocr_results.get_delimiters(search_area=search_area)

    
    if delimiters:
        # get widthest delimiter
        widthest_delimiter = sorted(delimiters,key=lambda x: x.box.width)[-1]
        
        # widder than treshold
        if widthest_delimiter.box.width >= image_info.width*0.3:
            header = {
            'left':None,
            'top':None,
            'width':None,
            'height':None,
            'right':None,
            'bottom':None,
            'boxes':[]
            }
                
            # update header
            header['left'] = widthest_delimiter.box.left
            header['right'] = widthest_delimiter.box.left + widthest_delimiter.box.width
            header['top'] = widthest_delimiter.box.top
            header['bottom'] = widthest_delimiter.box.top + widthest_delimiter.box.height

            # get header boxes
            header_boxes = []
            blocks = ocr_results.get_boxes_level(2)
            for block in blocks:
                # delimiter block above delimiter
                if ( block.box.top + block.box.height) < widthest_delimiter.box.top:
                    header_boxes.append(block)
                    block_right = block.box.left + block.box.width
                    # update header info
                    if header['left'] > block.box.left:
                        header['left'] = block.box.left
                    if header['top'] > block.box.top:
                        header['top'] = block.box.top
                    if header['right'] < block_right:
                        header['right'] = block_right
            
            header = Box(header['left'],header['right'],header['top'],header['bottom'])

    return header





def estimate_journal_columns(ocr_results,image_info:Box,header=None,footer=None):
    '''Estimate journal columns blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''
    columns = []
    # defining margins of search area
    upper_margin = 0
    lower_margin = image_info.height
    if header:
        upper_margin = header.bottom
    if footer:
        lower_margin = footer.top

    # get delimiter blocks
    search_area = Box(0,image_info.width,upper_margin,lower_margin)
    delimiters = ocr_results.get_delimiters(search_area=search_area,orientation='vertical')

    if delimiters:
        # joint aligned delimiters
        column_delimiters = join_aligned_delimiters(delimiters,orientation='vertical')
        right_margin = Box(image_info.width,image_info.width,upper_margin,lower_margin)
        column_delimiters.append(right_margin)
        # sort delimiters
        column_delimiters = sorted(column_delimiters,key=lambda x: x.left)
        # estimate column boxes
        for i in range(len(column_delimiters)):
            left = 0
            if i > 0:
                left = column_delimiters[i-1].right
            column_box = Box(left,column_delimiters[i].right,upper_margin,lower_margin)
            columns.append(column_box)
    
    return columns

    
def estimate_journal_template(ocr_results,image_info):
    '''Tries to estimate a journal's template, such as header and different columns'''
    # get header boxes
    header = estimate_journal_header(ocr_results,image_info)
    #TODO: get footer boxes
    footer = None
    # get columns
    columns = estimate_journal_columns(ocr_results,image_info,header,footer)

    return {
        'header':header,
        'columns':columns,
        'footer':footer
    }


def draw_journal_template(journal_data,image_path):
    '''Draw bounding boxes on journal image of path \'image_path\'\n'''

    img = cv2.imread(image_path)

    # draw header
    if journal_data['header']:
        header = journal_data['header']
        (x, y, w, h) = (header.left, header.top, header.width, header.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # draw columns
    for column in journal_data['columns']:
        (x, y, w, h) = (column.left, column.top, column.width, column.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return img


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