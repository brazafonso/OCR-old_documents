'''Old Structured Document OCR - GUI'''

import io
import shutil
import cv2
import os
import json
import argparse
import pandas as pd
import PySimpleGUI as sg
from pytesseract import Output
from PIL import Image
from aux_utils import consts
from aux_utils.page_tree import *
from aux_utils.image import *
from aux_utils.misc import *
from ocr_tree_module.information_extraction import journal_template_to_text
from ocr_tree_module.ocr_tree import *
from ocr_tree_module.ocr_tree_analyser import *
from ocr_tree_module.ocr_tree_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article


methods_1 = ['run_tesseract','fix_blocks','draw_bb','draw_journal_template',
           'calculate_reading_order','extract_articles','search_block']



    


def update_image_element(window:sg.Window,image_element:str,new_image,size:tuple=(500,700)):
    '''Update image element'''
    if type(new_image) in [str,'MatLike']:
        image = None
        if type(new_image) == str:
            image = cv2.imread(new_image)
        else:
            image = new_image
        image = cv2.resize(image,size)
        bio = cv2.imencode('.png',image)[1].tobytes()
        window[image_element].update(data=bio,visible=True)
        window.refresh()



def fix_ocr(target_image:str,results_path:str):
    '''Fix OCR'''
    # check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    ocr_results = OCR_Tree(f'{results_path}/result.json')
    ocr_results.id_boxes([2])
    ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
    # save results
    result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
    cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/fixed/result_fixed.csv')


def tesseract_method(window:sg.Window,image_path:str,values:dict):
    '''Apply tesseract method to image and update image element'''
    # results path
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'

    # clean results folder files
    if os.path.exists(results_path):
        files = os.listdir(results_path)
        for file in files:
            # if is dir, delete dir
            if os.path.isdir(f'{results_path}/{file}'):
                shutil.rmtree(f'{results_path}/{file}')
            else:
                os.remove(f'{results_path}/{file}')


    # rotate image if not disabled
    ## create tmp rotated image
    if values['checkbox_1_1']:
        direction = values['select_list_1_1'].lower()
        img = rotate_image(image_path,direction=direction)
        cv2.imwrite(f'{image_path}_tmp.png',img)
        # run tesseract
        run_tesseract(f'{image_path}_tmp.png',results_path=results_path)
        os.remove(f'{image_path}_tmp.png')

    else:
        # run tesseract
        run_tesseract(image_path)
        
    # update result image
    update_image_element(window,'result_img',f'{results_path}/result.png')

    # create fixed result folder
    if not os.path.exists(f'{results_path}/fixed'):
        os.makedirs(f'{results_path}/fixed')





def extract_articles_method(window:sg.Window,image_path:str):
    '''Apply extract articles method to image and update image element'''

    # results path
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    results_ocr_path =  f'{results_path}/result.json'
    results_ocr_fixed_path =  f'{results_path}/fixed/result_fixed.json'

    if os.path.exists(results_ocr_fixed_path) or os.path.exists(results_ocr_path):
        # create fixed result file
        if not os.path.exists(results_ocr_fixed_path):
            fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    ocr_results = categorize_boxes(ocr_results)

    image_info = get_image_info(image_path)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])
    print('header',journal_template['header'])
    print('footer',journal_template['footer'])
    print(columns_area)
    
    t_graph = topologic_order_context(ocr_results,columns_area)
    order_list = sort_topologic_order(t_graph,sort_weight=True)
    print('Order List: ',order_list)
    articles = graph_isolate_articles(t_graph)
    for article in articles:
        print('Article:',[b.id for b in article])
        
    with open(f'{results_path}/articles.txt','w',encoding='utf-8') as f:
        for article in articles:
            article = Article(article)
            f.write(article.pretty_print())
            f.write('\n')

    with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
        for article in articles:
            article = Article(article)
            f.write(article.to_md())
            f.write('\n'+'==='*40 + '\n')

    # draw reading order
    image = draw_articles(articles,image_path)
    cv2.imwrite(f'{results_path}/articles.png',image)
    update_image_element(window,'result_img',f'{results_path}/articles.png')


def fix_blocks_method(window:sg.Window,image_path:str):
    '''Apply fix blocks method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    fix_ocr(image_path,results_path)
    update_image_element(window,'result_img',f'{results_path}/fixed/result_fixed.png')


def journal_template_method(window:sg.Window,image_path:str):
    '''Apply journal template method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if fixed result file exists
    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
        fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    image_info = get_image_info(image_path)
    journal = estimate_journal_template(ocr_results,image_info)
    img = draw_journal_template(journal,image_path)
    cv2.imwrite(f'{results_path}/result_journal_template.png',img)
    update_image_element(window,'result_img',f'{results_path}/result_journal_template.png')

def reading_order_method(window:sg.Window,image_path:str):
    '''Apply reading order method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if fixed result file exists
    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
        fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    ocr_results.id_boxes([2],delimiters=False)
    image_info = get_image_info(f'{results_path}/fixed/result_fixed.png')
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    ocr_results = categorize_boxes(ocr_results)

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results,columns_area)
    order_list = sort_topologic_order(t_graph,sort_weight=True)

    # change ids to order
    order_map = {order_list[i]:i for i in range(len(order_list))}
    ocr_results.change_ids(order_map)

    # draw reading order
    image = draw_bounding_boxes(ocr_results,image_path,[2],id=True)
    cv2.imwrite(f'{results_path}/result_reading_order.png',image)
    update_image_element(window,'result_img',f'{results_path}/result_reading_order.png')


def auto_rotate_method(window:sg.Window,image_path:str):
    '''Apply auto rotate method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'

    img = rotate_image(image_path,direction='auto')
    cv2.imwrite(f'{results_path}/rotated.png',img)
    update_image_element(window,'result_img',f'{results_path}/rotated.png')

def calculate_dpi_method(window:sg.Window,image_path:str,resolution:str):
    '''Apply calculate dpi method to image and update image element'''
    # get image info
    image_info = get_image_info(image_path)

    # get resolution info from configs
    resolution = consts.config['resolutions'][resolution]
    resolution = Box(0,resolution['width'],0,resolution['height'])

    # calculate dpi
    dpi = calculate_dpi(image_info,resolution)

    # update image element
    window['result_text_1'].update(dpi,visible=True)

def apply_method(window:sg.Window,values:dict,image_path:str,method:str):
    '''Apply method to image and update image element'''
    ## TAB 1
    if method == 'run_tesseract':
        tesseract_method(window,image_path,values)
    elif method == 'extract_articles':
        extract_articles_method(window,image_path)
    elif method == 'fix_blocks':
        fix_blocks_method(window,image_path)
    elif method == 'journal_template':
        journal_template_method(window,image_path)
    elif method == 'reading_order':
        reading_order_method(window,image_path)
    elif method == 'auto_rotate':
        auto_rotate_method(window,image_path)

    ## TAB 2
    elif method == 'calculate_dpi':
        calculate_dpi_method(window,image_path,values['select_list_2_!'])
    else:
        print(f'method {method} not implemented')


def highlight_buttons(window:sg.Window,button:str,color:str,default_color:str='#283b5b'):
    # reset all buttons
    for element in window.AllKeysDict.keys():
        if 'sidebar_method' in element:
            button_element = window[element]
            button_element.update(button_color=('white',default_color))

    # highlight button
    button_element = window[button]
    button_element.update(button_color=('white',color))

    window.refresh()

def update_method_layout(window:sg.Window,method:str,target_image:str=None):
    '''Updates elements in layout based on method'''
    window['checkbox_1_1'].update(visible=False)
    window['select_list_text_1_1'].update(visible=False)
    window['select_list_1_1'].update(visible=False)

    ## TAB 1
    if method == 'run_tesseract' and target_image:
        window['checkbox_1_1'].update(visible=True)
        window['select_list_text_1_1'].update(visible=True)
        window['select_list_1_1'].update(visible=True)
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/result.png'
        # update target image
        update_image_element(window,'target_image_path',target_image)
        # check if result image exists
        if target_image and os.path.exists(result_image):
            # update result image
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'fix_blocks':
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/result.png'
        fixed_image = f'{consts.result_path}/{path_to_id(target_image)}/fixed/result_fixed.png'

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)

        if os.path.exists(fixed_image):
            # update result image
            update_image_element(window,'result_img',fixed_image)
        else:
            window['result_img'].update(visible=False)

        
    elif method == 'journal_template' and target_image:
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/result_journal_template.png'
        # update target image
        update_image_element(window,'target_image_path',target_image)

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window, 'result_img', result_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'reading_order':
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/result.png'
        reading_order_image = f'{consts.result_path}/{path_to_id(target_image)}/result_reading_order.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)

        if os.path.exists(reading_order_image):
            # update result image
            update_image_element(window,'result_img',reading_order_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'extract_articles':
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/result.png'
        articles_image = f'{consts.result_path}/{path_to_id(target_image)}/articles.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)

        if os.path.exists(articles_image):
            # update result image
            update_image_element(window,'result_img',articles_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'auto_rotate':
        target_image = consts.config['target_image_path']
        result_image = f'{consts.result_path}/{path_to_id(target_image)}/rotated.png'
        if target_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)

        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    ## TAB 2
    elif method == 'calculate_dpi':
        target_image = consts.config['target_image_path']
        result_text = ''
        resolutions_list = [res  for res in consts.config['resolutions'].keys()]

        if target_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path_2',target_image)
        else:
            window['target_image_path_2'].update(visible=False)

        window['select_list_2_1'].update(values=resolutions_list,value=resolutions_list[0])
        window['result_text_1'].update(result_text,visible=True)
        window['result_text_2'].update(visible=False)

    window.refresh()



def change_tab(window:sg.Window,tab:str):
    '''Change tab'''
    if tab == 'First':
        update_method_layout(window,'run_tesseract')
        method = 'run_tesseract'
    elif tab == 'Second':
        update_method_layout(window,'calculate_dpi')
        method = 'calculate_dpi'

    return method



def build_gui()->sg.Window:
    '''Build GUI'''
    # first_layout
    ## side bar for different methods
    ## upper bar for layout selection'
    ## main frame
    ### choose target image
    ### target image
    ### apply button
    ### results
    method_sidebar = [
        [
            sg.Button('Tesseract',key='sidebar_method_run_tesseract'),
        ],
        [
            sg.Button('Fix Blocks',key='sidebar_method_fix_blocks'),
        ],
        [
            sg.Button('Journal Template',key='sidebar_method_journal_template'),
        ],
        [
            sg.Button('Reading Order',key='sidebar_method_reading_order'),
        ],
        [
            sg.Button('Extract Articles',key='sidebar_method_extract_articles'),
        ],
        [
            sg.Button('Auto Rotate',key='sidebar_method_auto_rotate'),
        ]
    ]

    first_layout_1 = [
        [
            sg.Column(method_sidebar,expand_x=False,expand_y=True),
        ]
    ]

    first_layout_2_1 = [
        [
            sg.Button('Apply',key='apply'),
        ],
        [
            sg.Checkbox('Auto Rotate:',default=True,key='checkbox_1_1',enable_events=True,size=(10,10),visible=False),
        ],
        [
            sg.Text('Skew Direction:',key='select_list_text_1_1',visible=False),
            sg.Combo(['Auto','Clockwise','Counterclockwise'],default_value='Auto',key='select_list_1_1',enable_events=True,size=(5,10),visible=False),
        ]
    ]

    first_layout_2 = [
        [
                sg.FileBrowse(file_types=(("IMG Files", "*.*"),),button_text="Choose Image",key='browse_file',target='target_input'),
                sg.Input(default_text='',key='target_input',enable_events=True),
                sg.Button("Search Text",key='button_tesseract')
        ],
        [
            sg.Image(filename=None,visible=True,key='target_image_path',size=(500,700)),
            sg.Column(first_layout_2_1,expand_x=True,expand_y=False),
            sg.Image(filename=None,visible=True,key='result_img',size=(500,700)),
        ],
    ]

    first_layout = [
        [
            sg.Column(first_layout_1,expand_x=False,expand_y=True,
                    scrollable=True,vertical_scroll_only=True,
                    background_color='white'),
            sg.Column(first_layout_2,expand_x=True,expand_y=True),
        ]
    ]

    first_tab = sg.Tab(layout=first_layout,title='First')


    # second_layout - only for testing now
    ## side bar for different methods
    ## upper bar for layout selection'
    ## main frame
    ### target image
    ### select list
    ### apply button
    ### result text
    
    method_sidebar_2 = [
        [
            sg.Button('Calculate DPI',key='sidebar_method_calculate_dpi'),
        ]
    ]


    second_layout_1 = [
        [
            sg.Column(method_sidebar_2,expand_x=False,expand_y=True),
        ]
    ]

    second_layout_2 = [
        [
            sg.Image(filename=None,visible=True,key='target_image_path_2',size=(500,700)),
            sg.Button('Apply',key='apply'),
            sg.Combo([],key='select_list_2_1',enable_events=True,size=(5,10)),
            sg.Text('Result:'),
            sg.Text('',visible=False,key='result_text_1'),
            sg.Multiline(visible=False,key='result_text_2',size=(500,500)),
        ]
    ]

    second_layout = [
        [
            sg.Column(second_layout_1,expand_x=False,expand_y=True,
                    scrollable=True,vertical_scroll_only=True,
                    background_color='white'),
            sg.Column(second_layout_2,expand_x=True,expand_y=True),
        ]
    ]


    second_tab = sg.Tab(layout=second_layout,title='Second')


    layout = [
        [
            sg.TabGroup([
                [first_tab,second_tab]
            ],key='tab_group',expand_x=True,expand_y=True,enable_events=True)
        ]
    ]

    window = sg.Window('OCR',layout,finalize=True,resizable=True,size=(1200,800))
    return window







def run_gui():
    conf = consts.config
    current_path = consts.current_path
    result_path = consts.result_path

    # create results folder
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    window = build_gui()
    
    target_image = conf['target_image_path']
    # default method
    method = 'run_tesseract'
    highlight_buttons(window,'sidebar_method_run_tesseract','red')


    # update target image if exists
    if target_image:
        update_image_element(window,'target_image_path',target_image)
        update_method_layout(window,method,target_image)
        window['target_input'].update(target_image)

    while True:
        event, values = window.read()
        print(event)

        if event in (sg.WIN_CLOSED, 'Exit'):
            break
    ########################################
    # Main tab
        # new target file chosen
        elif event == 'target_input':
            target_image = str(values['target_input'])
            # update target image
            update_image_element(window,'target_image_path',target_image)
            update_method_layout(window,method,target_image)
            # save config
            conf['target_image_path'] = target_image
            save_configs()
        elif 'apply' in event:
            if target_image and method:
                apply_method(window,values,target_image,method)

    ########################################
    # Methods sidebar
        elif  'sidebar_method_' in event:
            highlight_buttons(window,event,'red')
            method = "_".join(event.split('_')[2:])
            update_method_layout(window,method,target_image)

    ########################################
    # Tab
        elif 'tab_group' in event:
            method = change_tab(window,values['tab_group'])
        
        

    window.close()