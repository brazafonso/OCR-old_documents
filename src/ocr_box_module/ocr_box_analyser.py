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



# def is_empty_box(ocr_results,conf=60):
#     '''Check if box group is empty'''
#     text = ''
#     for i in range(len(ocr_results)):
#         if ocr_results[i].level == 5 and ocr_results[i].conf > conf:
#             text += ocr_results[i].text
#     if re.match(r'^\s*$',text):
#         return True
#     return False


# def is_delimiter(ocr_results):
#     '''Check if box group is a delimter'''
#     if is_empty_box(ocr_results):
#         ocr_box = ocr_results[0]
#         if ocr_box.box.width >= ocr_box.box.height*4 or ocr_box.box.height >= ocr_box.box.width*4:
#             return True
#     return False


# def boxes_to_text(ocr_results,conf=60):
#     '''Convert ocr_results to text'''
#     text = ''
#     for i in range(len(ocr_results)):
#         if ocr_results[i].level == 5 and ocr_results[i].conf > conf:
#             text += ocr_results[i].text + ' '
#         elif ocr_results[i].level == 4:
#             text += '\n'
#         elif ocr_results[i].level == 3:
#             text += '\t'
#     return text


# def find_box_id(ocr_results,id):
#     '''Find index of box with id \'id\' in ocr_results'''
#     for i in range(len(ocr_results['text'])):
#         if ocr_results[i].id == id:
#             return i
#     return None


# def order_text_boxes(ocr_results):
#     '''Order text boxes from left to right and top to bottom, using top and left values\n
#     Return ordered ocr_results with only text boxes'''
#     ocr_results_ordered = page_tree()
#     for ocr_box in ocr_results:
#         # only text boxes
#         if ocr_box.level == 5 and ocr_box.text.strip() != '':
#             ocr_results_ordered.insert(ocr_box)

#     #ocr_results_ordered.pretty_print()
#     return ocr_results_ordered.to_list()


def order_line_boxes(lines):
    '''Order line boxes from left to right and top to bottom, using top and left values\n'''
    ocr_results_ordered = page_tree()
    for line in lines:
        ocr_results_ordered.insert(line)

    #ocr_results_ordered.pretty_print()
    return ocr_results_ordered.to_list()



# def is_normal_text_size(normal_text_size,line=None,line_height=None,range=0.3):
#     '''Check if line height is within normal text size range'''
#     if line:
#         lmh = line_mean_height(line)
#     elif line_height:
#         lmh = line_height
#     if lmh >= normal_text_size*(1-range) and lmh <= normal_text_size*(1+range):
#         return True
#     return False


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
        'columns':columns,
        #'ordered_lines':order_line_boxes(lines),
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







# def simple_article_extraction_page(processed_result):
#     '''Do simple article extraction utilizing letter size and column continuity'''
#     articles_result = []
#     columns_text = [[] for i in range(processed_result['number_columns'])]
#     ordered_lines = processed_result['ordered_lines']

#     # separete text by columns
#     for i in range(len(ordered_lines)):
#         # check column to insert text
#         for j in range(processed_result['number_columns']):
#             # if text within column, add it to column text
#             line_box = {
#                 'left':ordered_lines[i].left, 
#                 'top':ordered_lines[i].top, 
#                 'right':ordered_lines[i].left+ordered_lines[i].width,
#                 'bottom':ordered_lines[i].top+ordered_lines[i].height
#             }
#             column_box = {
#                 'left':processed_result['columns'][j][0][0], 
#                 'top':processed_result['columns'][j][0][1], 
#                 'right':processed_result['columns'][j][1][0],
#                 'bottom':processed_result['columns'][j][1][1]
#             }
#             if line_box.box.is_inside_box(column_box.box):
#                 columns_text[j].append(ordered_lines[i])
#                 break
    
#     # create articles
#     current_article = {
#         'title':('',None),
#         'columns':[],
#         'higher_height':None,
#         'lower_height':None,
#         'text':[]
#     }
#     found_article_text = False
#     for column in range(len(columns_text)):
#         current_article['columns'].append(column)
#         current_article['lower_height'] = None
#         for i in range(len(columns_text[column])):

#             line = columns_text[column][i]
#             if not is_normal_text_size(processed_result['normal_text_size'],line_height=line['line_mean_height']) and line['par_num'] == 1 and line['line_num'] == 1:
#                 title = ' '.join([ocr_box.text for ocr_box in line['boxes']])
#                 title_height = line['line_mean_height']
#                 # new article title
#                 if title.strip() and not current_article['title'][0]:
#                     current_article['title'] = (title,title_height)
#                 # new article
#                 elif title.strip() and current_article['title'][1] < title_height and found_article_text:
#                     articles_result.append(current_article)

#                     current_article = {
#                         'title':(title,title_height),
#                         'columns':[column],
#                         'higher_height':None,
#                         'lower_height':None,
#                         'text':[]
#                     }
#                 # simple subtitle
#                 else:
#                     current_article['text'] += line['boxes']
            
#             elif is_normal_text_size(processed_result['normal_text_size'],line_height=line['line_mean_height']):
#                 found_article_text = True
#                 current_article['text'] += line['boxes']
#             else:
#                 current_article['text'] += line['boxes']

#             if not current_article['higher_height'] or current_article['higher_height'] > line['top']:
#                 current_article['higher_height'] = line['top']
#             if not current_article['lower_height'] or current_article['lower_height'] < line['top']+line['height']:
#                 current_article['lower_height'] = line['top']+line['height']

#     # add last article
#     if current_article['text']:
#         articles_result.append(current_article)

#     return articles_result


def update_index_greater_id(ocr_results,value,id):
    '''Update index of boxes with id greater than \'id\' in ocr_results'''
    for i in range(len(ocr_results)):
        if ocr_results[i].id and ocr_results[i].index and ocr_results[i].id > id:
            ocr_results[i].index += value
    return ocr_results



def block_bound_box_fix(ocr_results,image_info):
    '''Fix block bound boxes\n'''
    i = 0
    current_box = None
    blocks = ocr_results.get_boxes_level(2)
    boxes_to_check = {}
    checked_boxes = []
    og_len = len(blocks)
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i< len(blocks):
        # get current box to analyse
        if not current_box and blocks[i].id not in checked_boxes:
            if (not blocks[i].is_empty()) or blocks[i].is_delimiter():
                current_box = blocks[i]
                i+=1
            else:
                ocr_results.remove_box_id(blocks[i].id)
                blocks.pop(i)
            continue
        # check if boxes are within each other
        if current_box and blocks[i].id != current_box.id:
            #print('Comparing boxes',current_box.id,blocks[i].id)
            compare_box = blocks[i]

            # compared box inside current box
            if compare_box.box.is_inside_box(current_box.box):
                ocr_results.remove_box_id(compare_box.id)
                if compare_box.id in boxes_to_check: 
                    del boxes_to_check[compare_box.id]
            # current box inside compared box
            elif current_box.box.is_inside_box(compare_box.box):
                ocr_results.remove_box_id(current_box.id)
                current_box = None
            # boxes intersect (with same level, so as to be able to merge seemlessly)
            elif current_box.box.intersects_box(compare_box.box) and current_box.box.same_level_box(compare_box.box):
                intersect_area = current_box.box.intersect_area_box(compare_box.box)
                # update boxes so that they don't intersect
                # smaller box is reduced
                if current_box.box.box_is_smaller(compare_box.box):
                    current_box.box.remove_box_area(intersect_area)
                else:
                    compare_box.box.remove_box_area(intersect_area)
            else:
                if compare_box.id not in checked_boxes and compare_box.id not in boxes_to_check:
                    boxes_to_check[compare_box.id] = compare_box
        i+=1
        # change current box to next one
        if (i == len(blocks) and boxes_to_check) or (not current_box and boxes_to_check):
            current_box = None
            keys = list(boxes_to_check.keys())
            # get next not empty block
            while not current_box and boxes_to_check:
                id = keys.pop(0)
                current_box = boxes_to_check[id]
                del boxes_to_check[id]
                checked_boxes.append(current_box.id)
                # check if box is empty
                # remove if true
                if current_box.is_empty() and not current_box.is_delimiter():
                    ocr_results.remove_box_id(current_box.id)
                    current_box = None
                i = 0


    print(f'''
    Initial number of boxes: {og_len}
    Final number of boxes: {len(ocr_results.get_boxes_level(2))}
    ''')
    return ocr_results


def bound_box_fix(ocr_results,level,image_info):
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_ocr_results = {}
    if level == 2:
        new_ocr_results = block_bound_box_fix(ocr_results,image_info)

    return new_ocr_results


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

    

def estimate_journal_header(ocr_results,image_info):
    '''Estimate journal header blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''

    header = None

    # get delimiter blocks
    search_area = Box(0,image_info['width'],0,image_info['height']*0.5) 
    delimiters = ocr_results.get_delimiters(search_area=search_area)

    
    if delimiters:
        # get widthest delimiter
        widthest_delimiter = sorted(delimiters,key=lambda x: x.box.width)[-1]
        
        # widder than treshold
        if widthest_delimiter.box.width >= image_info['width']*0.3:
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





def estimate_journal_columns(ocr_results,image_info,header=None,footer=None):
    '''Estimate journal columns blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''
    columns = []
    # defining margins of search area
    upper_margin = 0
    lower_margin = image_info['height']
    if header:
        upper_margin = header.bottom
    if footer:
        lower_margin = footer.top

    # get delimiter blocks
    search_area = Box(0,image_info['width'],upper_margin,lower_margin)
    delimiters = ocr_results.get_delimiters(search_area=search_area,orientation='vertical')

    if delimiters:
        # joint aligned delimiters
        column_delimiters = join_aligned_delimiters(delimiters,orientation='vertical')
        print('Delimiters:',column_delimiters)
        right_margin = Box(image_info['width'],image_info['width'],upper_margin,lower_margin)
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
    
    print('Columns:',columns)
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
        'columns':columns
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