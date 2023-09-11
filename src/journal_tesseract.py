#!/usr/bin/env python3

import io
import cv2
import pytesseract
import os
import json
import PySimpleGUI as sg
from pytesseract import Output
from PIL import Image

current_path = os.path.dirname(os.path.realpath(__file__))

conf = {}



'''Tesseract levels:
1 - page
2 - block
3 - paragraph
4 - line
5 - word'''


def read_configs():
    '''Read program configs from config.json'''
    global current_path,conf
    if os.path.exists(f'{current_path}/conf/conf.json'):
        conf_file = open(f'{current_path}/conf/conf.json','r')
        conf = json.load(conf_file)
        conf_file.close()
        if not os.path.exists(conf['target_image_path']):
            conf['target_image_path'] = ''
    else:
        conf = {
            'target_image_path':'',
        }

def save_configs():
    '''Save program configs to config.json'''
    global current_path,conf
    conf_file = open(f'{current_path}/conf/conf.json','w')
    json.dump(conf,conf_file,indent=4)
    conf_file.close()

def analyze_text(data_dict):
    '''Analyse text from data_dict and return text data as dict'''

    normal_text_size = 0
    number_columns = 0

    n_boxes = len(data_dict['text'])
    text_sizes_n = {}
    left_margin_n = {}
    right_margin_n = {}
    
    # save text sizes and margins
    for i in range(n_boxes):
        if int(data_dict['conf'][i]) > 60 and data_dict['level'][i] == 5:
            text_size = data_dict['height'][i]
            if text_size not in text_sizes_n:
                text_sizes_n[text_size] = 0
            text_sizes_n[text_size] += 1

            left_margin = round(data_dict['left'][i],-1)
            if left_margin not in left_margin_n:
                left_margin_n[left_margin] = 0
            left_margin_n[left_margin] += 1

            right_margin = round((data_dict['left'][i] + data_dict['width'][i]),-1)
            if right_margin not in right_margin_n:
                right_margin_n[right_margin] = 0
            right_margin_n[right_margin] += 1
    
    normal_text_size = max(text_sizes_n, key=text_sizes_n.get)
    normal_text_gap = None

    # estimate normal text gap
    for i in range(n_boxes):
        if data_dict['level'][i] == 2:
            last_height = None
            line = None
            paragraph = None
            for j in range(i+1,n_boxes):
                # break if next block
                if data_dict['level'][j] == 2:
                    break
                if int(data_dict['conf'][j]) > 60 and data_dict['level'][j] == 5 and data_dict['height'][j] == normal_text_size:
                    if data_dict['par_num'][j] != paragraph:
                        paragraph = data_dict['par_num'][j]
                        line = data_dict['line_num'][j]
                        
                    if data_dict['line_num'][j] > line:
                        print('line',line,data_dict['line_num'][j],data_dict['top'][j],last_height,normal_text_size)
                        normal_text_gap = (data_dict['top'][j] - last_height - normal_text_size) // (data_dict['line_num'][j] - line)
                        break

                    last_height = data_dict['top'][j]
                    line = data_dict['line_num'][j]
            if normal_text_gap:
                break

    # estimate number of lines
    highest_normal_text  = None
    lowest_normal_text = None
    for i in range(n_boxes):
        if int(data_dict['conf'][i]) > 60 and data_dict['height'][i] == normal_text_size:
            if not highest_normal_text or data_dict['top'][i] <= highest_normal_text:
                highest_normal_text = data_dict['top'][i]
            if not lowest_normal_text or data_dict['top'][i]+normal_text_size >= lowest_normal_text:
                lowest_normal_text = data_dict['top'][i]+normal_text_size

    number_lines = (lowest_normal_text - highest_normal_text) // (normal_text_size + normal_text_gap)

    probable_columns = sorted([k for k in sorted(left_margin_n, reverse=True,key=left_margin_n.get) if left_margin_n[k]>=0.45*number_lines])
    number_columns = len(probable_columns)

    columns = []

    # create columns bounding boxes
    for i in range(len(probable_columns)):
        if i < len(probable_columns)-1:
            columns.append(((highest_normal_text,probable_columns[i]),(lowest_normal_text,probable_columns[i+1])))
        else:
            columns.append(((highest_normal_text,probable_columns[i]),(lowest_normal_text,max(right_margin_n.keys()))))
                


    text = f'''
    Normal text size: {normal_text_size}
    Max number of lines : {number_lines}
    Number of columns: {number_columns}
    Columns: {columns}
'''
    print('Analysed results:',text)

    return {
        'normal_text_size':normal_text_size,
        'number_lines':number_lines,
        'number_columns':number_columns,
        'columns':columns,
    }



def search_text_img():
    '''Search for text in image of path saved on \'target_image_path\''''
    global conf

    img = cv2.imread(conf['target_image_path'])
    print('Using tesseract')
    data_dict = pytesseract.image_to_data(img, output_type=Output.DICT)
    data_text = pytesseract.image_to_string(img)
    data_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
    data_xml = pytesseract.image_to_alto_xml(img)
    print(data_dict.keys())

    n_boxes = len(data_dict['text'])

    print('Drawing bounding boxes')
    for i in range(n_boxes):
        if int(data_dict['conf'][i]) > 60:
            (x, y, w, h) = (data_dict['left'][i], data_dict['top'][i], data_dict['width'][i], data_dict['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    print('Text search over')
    
    cv2.imwrite(f'{current_path}/result.jpg',img)

    result_dict_file = open(f'{current_path}/result.json','w')
    json.dump(data_dict,result_dict_file,indent=4)
    result_dict_file.close()

    result_file = open(f'{current_path}/result.txt','w')
    result_file.write(data_text)
    result_file.close()

    data_text_processed = analyze_text(data_dict)
    result_file = open(f'{current_path}/result_processed.json','w')
    json.dump(data_text_processed,result_file,indent=4)
    result_file.close()

    result_pdf = open(f'{current_path}/result.pdf','wb')
    result_pdf.write(data_pdf)
    result_pdf.close()

    result_xml = open(f'{current_path}/result.xml','wb')
    result_xml.write(data_xml)
    result_xml.close()


def get_concat_h(im1, im2):
    '''Concatenate images horizontally'''
    dst = Image.new('RGB', (im1.width + im2.width + 15, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width + 15, 0))
    return dst


def split_page_columns(image_path,columns):
    '''Split image into columns images'''
    image = Image.open(image_path)
    width, height = image.size
    print('Image size:',width,height)
    columns_image = []
    for column in columns:
        columns_image.append(image.crop((column[0][1],column[0][0],column[1][1],column[1][0])))
    return columns_image

def concatentate_columns(columns):
    '''Concatenate columns images horizontally'''
    image = columns[0]
    for column in columns[1:]:
        image = get_concat_h(image,column)
    return image




def main():
    global conf,current_path
    layout = [
        [
            sg.FileBrowse(file_types=(("IMG Files", "*.jpg"),),initial_folder=f'{current_path}/../docs/jornais/',button_text="Choose Image",key='browse_file',target='target_input'),
            sg.Input(default_text='' if not conf['target_image_path'] else conf['target_image_path'],key='target_input',enable_events=True),
            sg.Button("Search Text",key='button_tesseract')
        ],
        [
            sg.Text('Target: '),
            sg.Image(filename=None,visible=False,key='target_image_path')
        ],
        [
            sg.Button("Result",key='button_result'),
            sg.Image(filename=None,visible=False,key='result_img'),
            sg.Multiline(size=(50,10),visible=False,key='result_text',disabled=True),
            sg.Multiline(size=(50,10),visible=False,key='result_text2',disabled=True),
            sg.Image(filename=None,visible=False,key='result_columns')
        ],
        [
            sg.Button("Close",key='button_close')
        ]
    ]

    window = sg.Window(title="Simple tesseract",layout=layout,use_default_focus=False,finalize=True,resizable=True)
    target = conf['target_image_path']

    if target:
        image = Image.open(target)
        image.thumbnail((800, 800))
        bio = io.BytesIO()
        image.save(bio, format="png")
        window['target_image_path'].update(data=bio.getvalue(),visible=True)
        window.refresh()

    while True:
        event, values = window.read()
        print(event)

        if event == 'target_input':
            target = values['target_input']
            if target and target.strip() != '' and target.endswith(('jpg','png')):
                # update target image
                image = Image.open(target)
                image.thumbnail((800, 800))
                bio = io.BytesIO()
                image.save(bio, format="png")
                window['target_image_path'].update(data=bio.getvalue(),visible=True)
                window.refresh()
        if event == 'button_tesseract':
            target = values['target_input']
            print('Target:',target)
            if  target and target.strip() != '' and target.endswith(('jpg','png')):
                conf['target_image_path'] = target
                save_configs()
                search_text_img()
        elif event == 'button_result':
            if os.path.exists(f'{current_path}/result.jpg'):
                # update result image
                image = Image.open(f'{current_path}/result.jpg')
                image.thumbnail((800, 800))
                bio = io.BytesIO()
                image.save(bio, format="png")
                window['result_img'].update(data=bio.getvalue(),visible=True)

                #update result text
                result_text = open(f'{current_path}/result.txt','r').read()
                window['result_text'].update(result_text,visible=True)
                processed_result = json.load(open(f'{current_path}/result_processed.json','r'))
                window['result_text2'].update(processed_result,visible=True)

                #update result columns
                columns_image = split_page_columns(target if target else f'{current_path}/result.jpg',processed_result['columns'])
                columns_image = concatentate_columns(columns_image)
                columns_image.thumbnail((800, 800))
                bio2 = io.BytesIO()
                columns_image.save(bio2,format='png')
                window['result_columns'].update(data=bio2.getvalue(),visible=True)
                window.refresh()
        elif event == "button_close" or event == sg.WIN_CLOSED:
            break
    window.close()






if __name__ == '__main__':
    read_configs()
    print('Configs:',conf)
    main()

