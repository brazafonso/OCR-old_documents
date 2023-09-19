import pytesseract
import cv2
import jellyfish
from pytesseract import Output
from PIL import Image
from aux_utils.page_tree import *
from aux_utils.image import *


def boxes_to_text(data_dict,conf=60):
    '''Convert data_dict to text'''
    text = ''
    for i in range(len(data_dict['text'])):
        if data_dict['level'][i] == 5 and data_dict['conf'][i] > conf:
            text += data_dict['text'][i] + ' '
        elif data_dict['level'][i] == 4:
            text += '\n'
        elif data_dict['level'][i] == 3:
            text += '\t'
    return text

def id_boxes(data_dict,level):
    '''Numbering boxes of specefic level'''
    id = 0
    data_dict['id'] = []
    for i in range(len(data_dict['text'])):
        if data_dict['level'][i] == level:
            data_dict['id'].append(id)
            id += 1
        else:
            data_dict['id'].append(None)
    return data_dict


def find_box_index(data_dict,id):
    '''Find index of box with id \'id\' in data_dict'''
    for i in range(len(data_dict['text'])):
        if data_dict['id'][i] == id:
            return i
    return None

def append_box(data_dict,box):
    '''Append box to data_dict'''
    for k in data_dict.keys():
        data_dict[k].append(box[k])
    return data_dict

def remove_data_dict_index(data_dict,index):
    '''Remove index from data_dict'''
    for k in data_dict.keys():
        data_dict[k].pop(index)
    return data_dict

def draw_bounding_boxes(data_dict,image_path,draw_levels=[2],conf=60,id=False):
    '''Draw bounding boxes on image of path \'image_path\'\n
    Return image with bounding boxes'''

    img = cv2.imread(image_path)
    print('Drawing bounding boxes')
    n_boxes = len(data_dict['text'])
    for i in range(n_boxes):
        if data_dict['level'][i] in draw_levels:
            # only draw text boxes if confidence is higher than conf
            if data_dict['level'][i] == 5 and data_dict['conf'][i] < conf:
                continue
            (x, y, w, h) = (data_dict['left'][i], data_dict['top'][i], data_dict['width'][i], data_dict['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if id and data_dict['id'][i]:
                img = cv2.putText(img, str(data_dict['id'][i]), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    return img


def get_group_boxes(data_dict,id):
    '''Get all boxes from the group of box with id \'id\'\n'''
    group_boxes = {k:[] for k in data_dict.keys()}
    parent_box = None
    for i in range(len(data_dict['text'])):
        current_box = {k:v for k in data_dict.keys() for v in [data_dict[k][i]]}
        if not parent_box:
            if data_dict['id'][i] == id:
                parent_box = current_box
                append_box(group_boxes,parent_box)
        # within group
        else:
            # child of box
            if data_dict['level'][i] > parent_box['level']:
                child_box = current_box
                append_box(group_boxes,child_box)
            # end of group
            else:
                break
    return group_boxes



def order_text_boxes(data_dict):
    '''Order text boxes from left to right and top to bottom, using top and left values\n
    Return ordered data_dict with only text boxes'''
    data_dict_ordered = page_tree()
    for i in range(len(data_dict['text'])):
        box = {k:v for k in data_dict.keys() for v in [data_dict[k][i]]}
        # only text boxes
        if box['level'] == 5 and box['text'].strip() != '':
            data_dict_ordered.insert(box)

    #data_dict_ordered.pretty_print()
    return data_dict_ordered.to_list()


def order_line_boxes(lines):
    '''Order line boxes from left to right and top to bottom, using top and left values\n'''
    data_dict_ordered = page_tree()
    for line in lines:
        data_dict_ordered.insert(line)

    #data_dict_ordered.pretty_print()
    return data_dict_ordered.to_list()

def get_line_boxes(data_dict):
    '''Gets all line boxes from data_dict\n
    Stores line boxes in a list of lists, where each list is a line with its text boxes'''
    line_boxes = []
    for i in range(len(data_dict['text'])):
        if data_dict['level'][i] == 4:
            line_text_boxes = get_line_text_boxes(data_dict,i)
            if line_text_boxes:
                line = {k:v for k in data_dict.keys() for v in [data_dict[k][i]]}
                line['line_mean_height'] = line_mean_height(line_text_boxes)
                line['boxes'] = line_text_boxes
                line_boxes.append(line)
                i+= len(line_text_boxes)
    return line_boxes




def get_line_text_boxes(data_dict,j):
    '''Return all boxes in line'''
    line_boxes = []
    if data_dict['level'][j] == 4:
        for i in range(j+1,len(data_dict['text'])):
            if data_dict['level'][i] == 5:
                if data_dict['conf'][i] > 60:
                    line_boxes.append({k:v for k in data_dict.keys() for v in [data_dict[k][i]] })
            else:
                break
    return line_boxes


def line_mean_height(line):
    '''Return mean height of line'''
    return sum([box['height'] for box in line]) / len(line)

def is_normal_text_size(normal_text_size,line=None,line_height=None,range=0.3):
    '''Check if line height is within normal text size range'''
    if line:
        line_mean_height = line_mean_height(line)
    elif line_height:
        line_mean_height = line_height
    if line_mean_height >= normal_text_size*(1-range) and line_mean_height <= normal_text_size*(1+range):
        return True
    return False


def analyze_text(data_dict):
    '''Analyse text from data_dict and return text data as dict\n
    Tries to find info about normal text size, number of lines and number of columns\n'''

    number_columns = 0

    n_boxes = len(data_dict['text'])
    lines = get_line_boxes(data_dict)
    text_sizes_n = {}
    left_margin_n = {}
    right_margin_n = {}

    normal_text_size = None
    
    # save text sizes and margins
    for line in lines:
        left_margin = round(line['left'],-1)
        if left_margin not in left_margin_n:
            left_margin_n[left_margin] = 0
        left_margin_n[left_margin] += 1

        right_margin = round((line['left'] + line['width']),-1)
        if right_margin not in right_margin_n:
            right_margin_n[right_margin] = 0
        right_margin_n[right_margin] += 1

        lmh = line['line_mean_height']
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
    for i in range(len(lines)):
        if last_block:
            if lines[i]['block_num'] == last_block and lines[i]['par_num'] == last_paragraph and lines[i]['line_num'] == last_line + 1 and is_normal_text_size(normal_text_size,line_height=lines[i]['line_mean_height']):
                if normal_text_gap:
                    normal_text_gap += lines[i]['top'] - last_top - normal_text_size
                    normal_text_gap /= 2
                else:
                    normal_text_gap = lines[i]['top'] - last_top - normal_text_size
            
        last_block = lines[i]['block_num']
        last_top = lines[i]['top']
        last_line = lines[i]['line_num']
        last_paragraph = lines[i]['par_num']

    # estimate number of lines
    highest_normal_text  = None
    lowest_normal_text = None

    ## find highest and lowest normal text
    for i in range(len(lines)):
        if is_normal_text_size(normal_text_size,line_height=lines[i]['line_mean_height']):
            if not highest_normal_text or lines[i]['top'] <= highest_normal_text:
                highest_normal_text = lines[i]['top']
            if not lowest_normal_text or lines[i]['top']+normal_text_size >= lowest_normal_text:
                lowest_normal_text = lines[i]['top']+normal_text_size
    number_lines = (lowest_normal_text - highest_normal_text) // (normal_text_size + normal_text_gap)


    # estimate number of columns
    probable_columns = sorted([k for k in sorted(left_margin_n, reverse=True,key=left_margin_n.get) if left_margin_n[k]>=0.45*number_lines])
    number_columns = len(probable_columns)

    columns = []

    # create columns bounding boxes
    for i in range(len(probable_columns)):
        if i < len(probable_columns)-1:
            left = probable_columns[i]*0.95
            right = probable_columns[i+1]*1.05
            top = highest_normal_text*0.95
            bottom = lowest_normal_text*1.05
            columns.append(((left,top),(right,bottom)))
        # last column
        else:
            left = probable_columns[i]*0.95
            right = max(right_margin_n.keys())*1.05
            top = highest_normal_text*0.95
            bottom = lowest_normal_text*1.05
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
        'ordered_lines':order_line_boxes(lines),
    }





def improve_bounds_precision(data_dict,target_image_path,progress_key,window):
    'Rerun tesseract on within the boundings of a text box to improve its width and height precision'
    progress_text = f'Progress: 0 / {len(data_dict["text"])}'
    window[progress_key].update(progress_text)
    window.refresh()
    original_img = Image.open(target_image_path)
    for i in range(len(data_dict['text'])):
        if data_dict['level'][i] == 5 and data_dict['conf'][i] > 60:
            (x, y, w, h) = (data_dict['left'][i], data_dict['top'][i], data_dict['width'][i], data_dict['height'][i])
            img = original_img.crop((x-0.2*w,y-0.2*h,x+w*1.2,y+h*1.2))
            new_values = pytesseract.image_to_data(img, output_type=Output.DICT,config='--psm 8',lang='por')
            # if data_dict['text'][i] == '(Continuado':
            #     file = open('temp.png','wb')
            #     img.save(file)
            #     file.close()
            #     break
            print(data_dict['text'][i])
            print(new_values['text'])
            print(new_values['conf'])
            for j in range(len(new_values['text'])):
                if new_values['level'][j] == 5 and jellyfish.levenshtein_distance(new_values['text'][j],data_dict['text'][i]) < len(data_dict['text'][i])*0.3:
                    print('Updated:',data_dict['text'][i],new_values['text'][j])
                    print(' Old:',data_dict['width'][i],data_dict['height'][i])
                    print(' New:',new_values['width'][j],new_values['height'][j])
                    data_dict['width'][i] = new_values['width'][j]
                    data_dict['height'][i] = new_values['height'][j]
                    break
        progress_text = f'Progress: {i} / {len(data_dict["text"])}'
        window[progress_key].update(progress_text)
        window.refresh()
    return data_dict



def search_text_img(image_path):
    '''Search for text in image of path saved on \'target_image_path\'\n
    Return dict with results in various formats, and image with bounding boxes'''

    img = Image.open(image_path)
    print('Using tesseract')
    data_dict = pytesseract.image_to_data(img, output_type=Output.DICT,lang='por',config='--psm 4')
    data_text = pytesseract.image_to_string(img,lang='por')
    data_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf',lang='por')
    data_xml = pytesseract.image_to_alto_xml(img,lang='por')
    print(data_dict.keys())

    print('Text search over')
    
    return {
        'data_dict':data_dict,
        'data_text':data_text,
        'data_pdf':data_pdf,
        'data_xml':data_xml
    }



def simple_article_extraction_page(processed_result):
    '''Do simple article extraction utilizing letter size and column continuity'''
    articles_result = []
    columns_text = [[] for i in range(processed_result['number_columns'])]
    ordered_lines = processed_result['ordered_lines']

    # separete text by columns
    for i in range(len(ordered_lines)):
        # check column to insert text
        for j in range(processed_result['number_columns']):
            # if text within column, add it to column text
            line_box = {
                'left':ordered_lines[i]['left'], 
                'top':ordered_lines[i]['top'], 
                'right':ordered_lines[i]['left']+ordered_lines[i]['width'],
                'bottom':ordered_lines[i]['top']+ordered_lines[i]['height']
            }
            column_box = {
                'left':processed_result['columns'][j][0][0], 
                'top':processed_result['columns'][j][0][1], 
                'right':processed_result['columns'][j][1][0],
                'bottom':processed_result['columns'][j][1][1]
            }
            if inside_box(line_box,column_box):
                columns_text[j].append(ordered_lines[i])
                break
    
    # create articles
    current_article = {
        'title':('',None),
        'columns':[],
        'higher_height':None,
        'lower_height':None,
        'text':[]
    }
    found_article_text = False
    for column in range(len(columns_text)):
        current_article['columns'].append(column)
        current_article['lower_height'] = None
        for i in range(len(columns_text[column])):

            line = columns_text[column][i]
            if not is_normal_text_size(processed_result['normal_text_size'],line_height=line['line_mean_height']) and line['par_num'] == 1 and line['line_num'] == 1:
                title = ' '.join([box['text'] for box in line['boxes']])
                title_height = line['line_mean_height']
                # new article title
                if title.strip() and not current_article['title'][0]:
                    current_article['title'] = (title,title_height)
                # new article
                elif title.strip() and current_article['title'][1] < title_height and found_article_text:
                    articles_result.append(current_article)

                    current_article = {
                        'title':(title,title_height),
                        'columns':[column],
                        'higher_height':None,
                        'lower_height':None,
                        'text':[]
                    }
                # simple subtitle
                else:
                    current_article['text'] += line['boxes']
            
            elif is_normal_text_size(processed_result['normal_text_size'],line_height=line['line_mean_height']):
                found_article_text = True
                current_article['text'] += line['boxes']
            else:
                current_article['text'] += line['boxes']

            if not current_article['higher_height'] or current_article['higher_height'] > line['top']:
                current_article['higher_height'] = line['top']
            if not current_article['lower_height'] or current_article['lower_height'] < line['top']+line['height']:
                current_article['lower_height'] = line['top']+line['height']

    # add last article
    if current_article['text']:
        articles_result.append(current_article)

    return articles_result


def block_bound_box_fix(data_dict):
    '''Fix block bound boxes\n'''
    i = 0
    current_box = None
    boxes_to_check = []
    boxes_to_check_id = []
    checked_boxes = []
    og_len = len([x for x in data_dict['level'] if x == 2])
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i < len(data_dict['level']):
        if data_dict['level'][i] == 2:
            if not current_box:
                current_box = {k:v for k in data_dict.keys() for v in [data_dict[k][i]]}
                current_box['right'] = current_box['left'] + current_box['width']
                current_box['bottom'] = current_box['top'] + current_box['height']
                i += 1
                continue
            # check if boxes are within each other
            if data_dict['id'][i] != current_box['id']:
                compare_box = {k:v for k in data_dict.keys() for v in [data_dict[k][i]]}
                compare_box['right'] = compare_box['left'] + compare_box['width']
                compare_box['bottom'] = compare_box['top'] + compare_box['height']

                # compared box inside current box
                if inside_box(compare_box,current_box):
                    data_dict = remove_data_dict_index(data_dict,i)
                    # remove all boxes inside compared block
                    while i < len(data_dict['level']) and data_dict['level'][i] != 2 :
                        data_dict = remove_data_dict_index(data_dict,i)

                    if compare_box['id'] in boxes_to_check_id:
                        boxes_to_check.pop(boxes_to_check_id.index(compare_box['id'])) 
                        boxes_to_check_id.remove(compare_box['id'])
                # current box inside compared box
                elif inside_box(current_box,compare_box):
                    i = find_box_index(data_dict,current_box['id'])
                    data_dict = remove_data_dict_index(data_dict,i)

                    # remove all boxes inside current block
                    while i < len(data_dict['level']) and data_dict['level'][i] != 2 :
                        data_dict = remove_data_dict_index(data_dict,i)
                    current_box = None
                else:
                    if compare_box['id'] not in checked_boxes and compare_box['id'] not in boxes_to_check_id:
                        boxes_to_check.append(compare_box)
                        boxes_to_check_id.append(compare_box['id'])
        i+=1
        # change box to next one
        if (i == len(data_dict['level']) and boxes_to_check) or (not current_box and boxes_to_check):
            i = 0
            current_box = boxes_to_check.pop(0)
            boxes_to_check_id.pop(0)
            checked_boxes.append(current_box['id'])


    print(f'''
    Initial number of boxes: {og_len}
    Final number of boxes: {len([x for x in data_dict['level'] if x == 2])}
    ''')
    return data_dict


def bound_box_fix(data_dict,level):
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_data_dict = {}
    if level == 2:
        new_data_dict = block_bound_box_fix(data_dict)

    return new_data_dict
    
    


