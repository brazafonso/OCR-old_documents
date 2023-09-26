#!/usr/bin/env python3
'''Journal tesseract - A simple tesseract based text search for journal pages for article extraction'''
import io
import cv2
import os
import json
import pandas as pd
import PySimpleGUI as sg
from pytesseract import Output
from PIL import Image
from aux_utils.page_tree import *
from aux_utils.image import *
from extend_tesseract.box_analyser import *

current_path = os.path.dirname(os.path.realpath(__file__))
result_path = f'{current_path}/results'

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


def update_search_block_og(window,target_image=None):
    '''GUI - Update search block for original image'''
    global result_path
    if target_image and os.path.exists(f'{result_path}/result.json'):
        data_dict = json.load(open(f'{result_path}/result.json','r'))
        data_dict = id_boxes(data_dict,2)
        image = draw_bounding_boxes(data_dict,target_image,[2],id=True)
        image = Image.fromarray(image)
        bio = io.BytesIO()
        image.save(bio, format="png")
        # get available block ids
        block_ids = []
        for i in range(len(data_dict['text'])):
            if data_dict['level'][i] == 2:
                block_ids.append(data_dict['id'][i])
        window['search_block_og'].update(values=block_ids,value=block_ids[0],disabled=False)
        window['result_img_search_block_og'].update(data=bio.getvalue(),visible=True)
        window.refresh()
        window['column_fix_window'].contents_changed()

def update_search_block_fixed(window,target_image=None):
    '''GUI - Update search block for fixed image'''
    global result_path
    if target_image and os.path.exists(f'{result_path}/fixed/result_fixed.json'):
        data_dict = json.load(open(f'{result_path}/fixed/result_fixed.json','r'))
        data_dict = id_boxes(data_dict,2)
        image = draw_bounding_boxes(data_dict,target_image,[2],id=True)
        image = Image.fromarray(image)
        bio = io.BytesIO()
        image.save(bio, format="png")
        # get available block ids
        block_ids = []
        for i in range(len(data_dict['text'])):
            if data_dict['level'][i] == 2:
                block_ids.append(data_dict['id'][i])
        window['search_block_fixed'].update(values=block_ids,value=block_ids[0],disabled=False)
        window['result_img_search_block_fixed'].update(data=bio.getvalue(),visible=True)
        window.refresh()
        window['column_fix_window'].contents_changed()



def save_results(data_dict,image_path):
    '''Saves results gathered from data_dict to files'''
    global result_path

    img = draw_bounding_boxes(data_dict,image_path)
    # create result files

    # create result image
    cv2.imwrite(f'{result_path}/result.jpg',img)

    # save result data
    result_dict_file = open(f'{result_path}/result.json','w')
    json.dump(data_dict,result_dict_file,indent=4)
    result_dict_file.close()

    result_csv_file = open(f'{result_path}/result.csv','w')
    df = pd.DataFrame(data_dict)
    df.to_csv(result_csv_file)
    result_csv_file.close()
    
    # save result processed data
    data_processed = analyze_text(data_dict)
    result_file = open(f'{result_path}/result_processed.json','w')
    json.dump(data_processed,result_file,indent=4)
    result_file.close()


def run_tesseract(image_path):
    '''GUI - Run text search on target image'''
    global result_path,conf

    results = search_text_img(image_path)
    data_dict = results['data_dict']
    data_text = results['data_text']
    data_pdf = results['data_pdf']
    data_xml = results['data_xml']
    
    # save results

    # save results from data_dict
    save_results(data_dict,image_path)

    # save result simple text
    result_file = open(f'{result_path}/result.txt','w')
    result_file.write(data_text)
    result_file.close()


    # save result pdf and xml
    result_pdf = open(f'{result_path}/result.pdf','wb')
    result_pdf.write(data_pdf)
    result_pdf.close()

    result_xml = open(f'{result_path}/result.xml','wb')
    result_xml.write(data_xml)
    result_xml.close()

    del results

def run_tesseract_results(window):
    '''GUI - Show results of text search on target image'''
    global result_path,conf
    target_image = conf['target_image_path']

    # update result image
    image = Image.open(f'{result_path}/result.jpg')
    image.thumbnail((800, 800))
    bio = io.BytesIO()
    image.save(bio, format="png")
    window['result_img'].update(data=bio.getvalue(),visible=True)
    
    #update result text
    result_text = open(f'{result_path}/result.txt','r').read()
    window['result_text'].update(result_text,visible=True)

    processed_result = json.load(open(f'{result_path}/result_processed.json','r'))
    window['result_text2'].update(processed_result,visible=True)

    #update result columns
    columns_image = split_page_columns(target_image if target_image else f'{result_path}/result.jpg',processed_result['columns'])
    columns_image = concatentate_columns(columns_image)
    if columns_image:
        columns_image.thumbnail((800, 800))
        bio2 = io.BytesIO()
        columns_image.save(bio2,format='png')
        window['result_columns'].update(data=bio2.getvalue(),visible=True)
    window.refresh()


def run_extract_articles():
    '''GUI - Extract articles from text search results'''
    processed_result = json.load(open(f'{result_path}/result_processed.json','r'))
    extracted_articles = simple_article_extraction_page(processed_result)

    file = open(f'{result_path}/extracted_articles.json','w')
    json.dump(extracted_articles,file,indent=4)
    file.close()

    file = open(f'{result_path}/extracted_articles.txt','w')
    # write articles to file in plain text, keeping some indentation
    for article in extracted_articles:
        file.write(f'|{article["title"][0]}|\n\n')
        last_t = None
        for t in article['text']:
            if last_t:
                if last_t['par_num'] != t['par_num'] or last_t['block_num'] != t['block_num']:
                    last_t = None
                    file.write('\n')
                else:
                    if last_t['line_num'] != t['line_num']:
                        file.write('\n')
                    else:
                        file.write(' ')
            file.write(f'{t["text"]}')
            last_t = t
        file.write('\n\n')
    file.close()
    


def main():
    global conf,current_path

    column_target = [
        [
            sg.Image(filename=None,visible=False,key='target_image_path')
        ]
    ]
    progress = ''

    # main window layout
    main_layout = [
        [
            sg.FileBrowse(file_types=(("IMG Files", "*.jpg"),("IMG Files", "*.png")),initial_folder=f'{current_path}/../docs/jornais/',button_text="Choose Image",key='browse_file',target='target_input'),
            sg.Input(default_text='' if not conf['target_image_path'] else conf['target_image_path'],key='target_input',enable_events=True),
            sg.Button("Search Text",key='button_tesseract')
        ],
        [
            sg.Text('Target: '),
            sg.Column(column_target,scrollable=True,size=(800,500),key='column_target_image')
        ],
        [
            sg.Button("Extract articles",key='button_extract_articles')
        ],
        [
            sg.Button("Test ordering",key='button_test_ordering')
        ],
        [
            sg.Button("Test ordering tree",key='button_test_ordering_tree')
        ],
        [
            sg.Button("Test improve bounds precision",key='button_test_improve_bounds'),
            sg.Text(progress,key='progress_text',visible=False),
        ],
        [
            sg.Button("Test alternative analyse text",key='button_test_alt_analyse'),
        ],
        [
            sg.Button("Test black and white",key='button_test_black_and_white'),
        ],
        [
            sg.Combo(values=[2,3,4,5],default_value=2,size=(10,2),key='draw_bounding_boxes_level',enable_events=True),
            sg.Button("Draw bounding boxes",key='draw_bounding_boxes'),
            sg.Button("Hide",key='button_hide_draw_bounding_boxes',visible=False),
            sg.Image(filename=None,visible=False,key='bounding_boxes_image'),
        ],
        [
            sg.Button("Close",key='button_close')
        ]
    ]

    main_layout = [
        [sg.Column(main_layout,scrollable=True,size=(1000,800),expand_x=True,expand_y=True,key='column_main_window')],
    ]
    main_tab = sg.Tab(layout=main_layout,title='Main')

    results_layout = [
        [
            sg.Button("Result",key='button_result'),
            sg.Image(filename=None,visible=False,key='result_img'),
            sg.Multiline(size=(50,10),visible=False,key='result_text',disabled=True),
            sg.Multiline(size=(50,10),visible=False,key='result_text2',disabled=True),
            sg.Image(filename=None,visible=False,key='result_columns')
        ]
        ]

    results_layout = [
        [sg.Column(results_layout,scrollable=True,size=(1000,800),expand_x=True,expand_y=True,key='column_results_window')],
    ]

    results_tab = sg.Tab(layout=results_layout,title='Results')


    fix_layout = [
        [
            sg.Text("Fix box bounds"),
            sg.Combo(values=[2,3,4,5],default_value=2,size=(10,2),key='fix_box_bounds_level',enable_events=True),
            sg.Button("Fix",key='fix_box_bounds'),
            sg.Image(filename=None,visible=False,key='fix_box_bounds_image_og'),
            sg.Image(filename=None,visible=False,key='fix_box_bounds_image_new')
        ],
        [
            sg.Button("Save result",key='button_save_fix_result',visible=False),
        ],
        [
            sg.Button("Result",key='button_result_fix'),
            sg.Image(filename=None,visible=False,key='result_img_fix'),
            sg.Text("Original text:",visible=False,key='result_label_fix'),
            sg.Multiline(size=(50,10),visible=False,key='result_text_fix',disabled=True),
            sg.Text("Fixed text:",visible=False,key='result_label2_fix'),
            sg.Multiline(size=(50,10),visible=False,key='result_text2_fix',disabled=True),
            sg.Image(filename=None,visible=False,key='result_columns_fix')
        ],
        [
            sg.Text("OG - Search for block:"),
            sg.Combo(key='search_block_og',values=[],size=(4,4),disabled=True),
            sg.Button("Search",key='button_search_block_og'),
            sg.Image(filename=None,visible=False,key='result_img_search_block_og'),
            sg.Multiline(size=(50,10),visible=False,key='result_text_search_block_og',disabled=True),
        ],
        [
            sg.Text("Fixed - Search for block:"),
            sg.Combo(key='search_block_fixed',values=[],size=(4,4),disabled=True),
            sg.Button("Search",key='button_search_block_fixed'),
            sg.Image(filename=None,visible=False,key='result_img_search_block_fixed'),
            sg.Multiline(size=(50,10),visible=False,key='result_text_search_block_fixed',disabled=True),
        ],
        [
            sg.Button("Overwrite original result",key='button_overwrite_original_result')
        ]
        
    ]

    fix_layout = [
        [sg.Column(fix_layout,scrollable=True,size=(1000,800),expand_x=True,expand_y=True,key='column_fix_window')],
    ]

    fix_tab = sg.Tab(layout=fix_layout,title='Fix')

    layout = [
        [
            sg.TabGroup([[main_tab,results_tab,fix_tab]],key='main_tab_group',enable_events=True,expand_x=True,expand_y=True)
        ]
    ]

    window = sg.Window(title="Simple tesseract",
                       layout=layout,
                       finalize=True,
                       size=(1000,800))
    
    target_image = conf['target_image_path']

    # update target image
    if target_image:
        image = Image.open(target_image)
        bio = io.BytesIO()
        image.save(bio, format="png")
        window['target_image_path'].update(data=bio.getvalue(),visible=True)
        window.refresh()
        window['column_target_image'].contents_changed()

    # update og image (fix tab)
    update_search_block_og(window,target_image)
    # update fixed image (fix tab)
    update_search_block_fixed(window,target_image)


    scroll_collumn_dict = {
        'Main': 'column_main_window',
        'Results': 'column_results_window',
        'Fix': 'column_fix_window'
    }

    while True:
        event, values = window.read()
        print(event)

    ########################################
    # Main tab
        # new target file chosen
        if event == 'target_input':
            target_image = values['target_input']
            if target_image and target_image.strip() != '' and target_image.endswith(('jpg','png')):
                # update target image
                image = Image.open(target_image)
                image.thumbnail((800, 800))
                bio = io.BytesIO()
                image.save(bio, format="png")
                window['target_image_path'].update(data=bio.getvalue(),visible=True)
                # update og image (fix tab)
                update_search_block_og(window,target_image)
                window.refresh()

        # use tesseract to search for text in image
        if event == 'button_tesseract':
            target_image = values['target_input']
            print('Target:',target_image)
            if  target_image and target_image.strip() != '' and target_image.endswith(('jpg','png')):
                conf['target_image_path'] = target_image
                save_configs()
                run_tesseract(target_image)
                # update og image (fix tab)
                update_search_block_og(window,target_image)


        # draw bounding boxes
        elif event == 'draw_bounding_boxes':
            if os.path.exists(f'{result_path}/result.json') and target_image:
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                box_level = values['draw_bounding_boxes_level']
                image = draw_bounding_boxes(data_dict,target_image,[box_level])
                bio = io.BytesIO()
                pil_img = Image.fromarray(image)
                pil_img.save(bio,format='png')
                window['bounding_boxes_image'].update(data=bio.getvalue(),visible=True)
                window['button_hide_draw_bounding_boxes'].update(visible=True)
                window.refresh()
            else:
                sg.popup('No result data found. Please run text search first.')

        # hide bounding boxes
        elif event == 'button_hide_draw_bounding_boxes':
            window['bounding_boxes_image'].update(visible=False)
            window['button_hide_draw_bounding_boxes'].update(visible=False)
            window.refresh()

        # basic article extraction
        elif event == 'button_extract_articles':
            if os.path.exists(f'{result_path}/result_processed.json'):
                run_extract_articles()
            else:
                sg.popup('No result data found. Please run text search first.')

        # test ordering
        elif event == 'button_test_ordering':
            if os.path.exists(f'{result_path}/result.json'):
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                data_dict_ordered = order_text_boxes(data_dict)
                for i in range(len(data_dict_ordered)):
                    print(data_dict_ordered[i]['text'])
        
        # test ordering tree
        elif event == 'button_test_ordering_tree':
            if os.path.exists(f'{result_path}/result.json'):
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                data_dict_ordered = order_text_boxes(data_dict)

        elif event == 'button_test_improve_bounds':
            if os.path.exists(f'{result_path}/result.json'):
                window['progress_text'].update(visible=True)

                data_dict = json.load(open(f'{result_path}/result.json','r'))
                data_dict = improve_bounds_precision(data_dict,target_image if target_image else f'{result_path}/result.jpg','progress_text',window)

                new_result_file = open(f'{result_path}/result_improved.json','w')
                json.dump(data_dict,new_result_file,indent=4)
                new_result_file.close()

                new_result_file_csv = open(f'{result_path}/result_improved.csv','w')
                df = pd.DataFrame(data_dict)
                df.to_csv(new_result_file_csv)
                new_result_file_csv.close()

                window['progress_text'].update(visible=False)

        elif event == 'button_test_alt_analyse':
            if os.path.exists(f'{result_path}/result.json'):
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                data_dict = analyze_text(data_dict)
                new_result_file = open(f'{result_path}/result_processed_alt.json','w')
                json.dump(data_dict,new_result_file,indent=4)
                new_result_file.close()

        elif event == 'button_test_black_and_white':
            if target_image:
                image = black_and_white(target_image)
                image.save('test_bw.jpg')
            else:
                sg.popup('No target image selected')

    ########################################
    # Results tab
        # show results of image search
        elif event == 'button_result':
            if os.path.exists(f'{result_path}/result.jpg') and os.path.exists(f'{result_path}/result.txt') and os.path.exists(f'{result_path}/result.json') and os.path.exists(f'{result_path}/result_processed.json'):
                run_tesseract_results(window)
            else:
                sg.popup('No result data found. Please run text search first.')

    ########################################
    # Fix tab
        # fix box bounds
        elif event == 'fix_box_bounds':
            if target_image and os.path.exists(f'{result_path}/result.json'):
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                box_level = values['fix_box_bounds_level']
                data_dict = id_boxes(data_dict,box_level)
                image = draw_bounding_boxes(data_dict,target_image,[box_level],id=True)
                bio = io.BytesIO()
                pil_img = Image.fromarray(image)
                pil_img.save(bio,format='png')
                window['fix_box_bounds_image_og'].update(data=bio.getvalue(),visible=True)
                window.refresh()

                data_dict = bound_box_fix(data_dict,box_level,get_image_info(target_image))
                image = draw_bounding_boxes(data_dict,target_image,[box_level],id=True)
                bio = io.BytesIO()
                pil_img = Image.fromarray(image)
                pil_img.save(bio,format='png')
                window['fix_box_bounds_image_new'].update(data=bio.getvalue(),visible=True)
                window['button_save_fix_result'].update(visible=True)
                window.refresh()

                # update fixed image (fix tab)
                update_search_block_fixed(window,target_image)
            else:
                sg.popup('No target image selected, or no result data found. Please run text search first.')
        
        # save fix result
        elif event == 'button_save_fix_result':
            if data_dict:
                result_dict_file = open(f'{result_path}/fixed/result_fixed.json','w')
                json.dump(data_dict,result_dict_file,indent=4)
                result_dict_file.close()
                image = draw_bounding_boxes(data_dict,target_image,[box_level],id=True)
                cv2.imwrite(f'{result_path}/fixed/result_fixed.jpg',image)
                csv = pd.DataFrame(data_dict)
                csv.to_csv(f'{result_path}/fixed/result_fixed.csv')

                # update fixed image (fix tab)
                update_search_block_fixed(window,target_image)

        # show fix results
        elif event == 'button_result_fix':
            if os.path.exists(f'{result_path}/fixed/result_fixed.jpg') and os.path.exists(f'{result_path}/fixed/result_fixed.json') and os.path.exists(f'{result_path}/result.json'):
                image = Image.open(f'{result_path}/fixed/result_fixed.jpg')
                image.thumbnail((800, 800))
                bio = io.BytesIO()
                image.save(bio, format="png")
                window['result_img_fix'].update(data=bio.getvalue(),visible=True)
                
                #update original text
                original_data = json.load(open(f'{result_path}/result.json','r'))
                lines = get_line_boxes(original_data)
                lines = order_line_boxes(lines)
                original_text = ''
                for line in lines:
                    for box in line['boxes']:
                        original_text += box['text'] + ' '
                    original_text += '\n'


                #update result text
                result_data = json.load(open(f'{result_path}/fixed/result_fixed.json','r'))
                lines = get_line_boxes(result_data)
                lines = order_line_boxes(lines)
                result_text = ''
                for line in lines:
                    for box in line['boxes']:
                        result_text += box['text'] + ' '
                    result_text += '\n'
                
                open(f'{result_path}/fixed/original_text.txt','w').write(original_text)
                open(f'{result_path}/fixed/result_fixed.txt','w').write(result_text)

                window['result_label_fix'].update(visible=True)
                window['result_text_fix'].update(original_text,visible=True)
                window['result_label2_fix'].update(visible=True)
                window['result_text2_fix'].update(result_text,visible=True)
                window.refresh()
                window['column_fix_window'].contents_changed()

            else:
                sg.popup('No result data found. Please run fix first.')
        
        # search for block in original image
        elif event == 'button_search_block_og':
            if os.path.exists(f'{result_path}/result.json'):
                data_dict = json.load(open(f'{result_path}/result.json','r'))
                data_dict = id_boxes(data_dict,2)
                block_id = values['search_block_og']
                boxes = get_group_boxes(data_dict,block_id)
                text = boxes_to_text(boxes)
                print(text)
                window['result_text_search_block_og'].update(text,visible=True)
                window.refresh()
                window['column_fix_window'].contents_changed()
            else:
                sg.popup('No result data found. Please run text search first.')

        # search for block in fixed image
        elif event == 'button_search_block_fixed':
            if os.path.exists(f'{result_path}/fixed/result_fixed.json'):
                data_dict = json.load(open(f'{result_path}/fixed/result_fixed.json','r'))
                data_dict = id_boxes(data_dict,2)
                block_id = values['search_block_fixed']
                boxes = get_group_boxes(data_dict,block_id)
                text = boxes_to_text(boxes)
                print(text)
                window['result_text_search_block_fixed'].update(text,visible=True)
                window.refresh()
                window['column_fix_window'].contents_changed()
            else:
                sg.popup('No result data found. Please run fix first.')
        
        elif event == 'button_overwrite_original_result':
            if os.path.exists(f'{result_path}/fixed/result_fixed.json'):
                data_dict = json.load(open(f'{result_path}/fixed/result_fixed.json','r'))
                save_results(data_dict,target_image)
                run_tesseract_results(window)

            else:
                sg.popup('No result data found. Please run fix first.')
                
        # close program
        elif event == "button_close" or event == sg.WIN_CLOSED:
            break

        # update main column size
        column = scroll_collumn_dict[values['main_tab_group']]
        window[column].contents_changed()
    window.close()






if __name__ == '__main__':
    read_configs()
    main()

