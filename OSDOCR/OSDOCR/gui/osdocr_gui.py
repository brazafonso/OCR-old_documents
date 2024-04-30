'''Old Structured Document OCR - GUI'''

import os
import pandas as pd
import PySimpleGUI as sg
from aux_utils import consts
from aux_utils.page_tree import *
from document_image_utils.image import *
from aux_utils.misc import *
from .layouts.main_layout import *
from .layouts.extra_layout import *
from .methods.methods import *



methods_1 = ['run_tesseract','fix_blocks','draw_bb','draw_journal_template',
           'calculate_reading_order','extract_articles','search_block','unite_blocks']


def apply_method(window:sg.Window,values:dict,image_path:str,method:str):
    '''Apply method to image and update image element'''
    ## TAB 1
    if method == 'run_tesseract':
        tesseract_method(window,image_path,values)
    elif method == 'extract_articles':
        extract_articles_method(window,image_path,values)
    elif method == 'fix_blocks':
        fix_blocks_method(window,image_path)
    elif method == 'journal_template':
        journal_template_method(window,image_path)
    elif method == 'reading_order':
        reading_order_method(window,image_path,values)
    elif method == 'auto_rotate':
        auto_rotate_method(window,image_path)
    elif method == 'unite_blocks':
        unite_blocks_method(window,image_path)
    elif method == 'divide_columns':
        divide_columns_method(window,image_path,values)
    elif method == 'divide_journal':
        divide_journal_method(window,image_path)
        

    ## TAB 2
    elif method == 'ocr_pipeline':
        ocr_pipeline_method(window)
    elif method == 'calculate_dpi':
        calculate_dpi_method(window,image_path,values['select_list_2_1'])
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

def update_method_layout(window:sg.Window,method:str,o_image:str=None):
    '''Updates elements in layout based on method'''


    window['target_image_path'].update(visible=False)
    window['target_image_path_2'].update(visible=False)
    window['apply'].update(visible=False)
    # disable extra options
    window['checkbox_1_1'].update(visible=False)
    window['select_list_text_1_1'].update(visible=False)
    window['select_list_1_1'].update(visible=False)
    window['config_pipeline'].update(visible=False)
    window['select_list_2_1'].update(visible=False)
    window['result_text_1'].update(visible=False)
    window['result_text_2'].update(visible=False)
    window['result_text_3'].update(visible=False)

    ## TAB 1
    if method == 'run_tesseract' and o_image:
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        # update target image
        update_image_element(window,'target_image_path',o_image)

        # update apply button
        window['apply'].update(visible=True)
        # update options
        window['checkbox_1_1'].update(visible=True,text='Auto Rotate:')
        window['select_list_text_1_1'].update(value='Skew Direction:',visible=True)
        window['select_list_1_1'].update(value='Auto',values=['Auto','Clockwise','Counterclockwise'],visible=True)

        # check if result image exists
        if o_image and os.path.exists(result_image):
            # update result image
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'fix_blocks':
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        fixed_image = f'{consts.result_path}/{path_to_id(o_image)}/fixed/result_fixed.png'

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)

        # update apply button
        window['apply'].update(visible=True)

        if os.path.exists(fixed_image):
            # update result image
            update_image_element(window,'result_img',fixed_image)
        else:
            window['result_img'].update(visible=False)

        
    elif method == 'journal_template' and o_image:
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/result_journal_template.png'
        # update target image
        update_image_element(window,'target_image_path',o_image)

        # update apply button
        window['apply'].update(visible=True)

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window, 'result_img', result_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'reading_order':
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/result_id.png'
        reading_order_image = f'{consts.result_path}/{path_to_id(o_image)}/result_reading_order.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        # enable checkbox
        window['checkbox_1_1'].update(text='Ignore Delimeters:',visible=True)


        if os.path.exists(reading_order_image):
            # update result image
            update_image_element(window,'result_img',reading_order_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'extract_articles':
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        articles_image = f'{consts.result_path}/{path_to_id(o_image)}/articles.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        # enable checkbox
        window['checkbox_1_1'].update(text='Ignore Delimeters:',visible=True)

        if os.path.exists(articles_image):
            # update result image
            update_image_element(window,'result_img',articles_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'auto_rotate':
        target_image = consts.config['target_image_path']
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/rotated.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'unite_blocks':
        target_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/fixed/united.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'divide_columns':
        target_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/test/columns.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        window['select_list_text_1_1'].update(value='Analyses Type:',visible=True)
        window['select_list_1_1'].update(value='Blocks',values=['Blocks','Pixels'],visible=True)
        # update apply button
        window['apply'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'divide_journal':
        target_image = f'{consts.result_path}/{path_to_id(o_image)}/result.png'
        result_image = f'{consts.result_path}/{path_to_id(o_image)}/test/journal_areas.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    ## TAB 2
    elif method == 'ocr_pipeline':

        target_image = consts.config['target_image_path']

        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path_2',target_image)
        else:
            window['target_image_path_2'].update(visible=False)
        
        window['apply'].update(visible=False)
        window['config_pipeline'].update(visible=True)
        window['apply'].update(visible=True)

    elif method == 'calculate_dpi':
        target_image = consts.config['target_image_path']
        result_text = ''
        resolutions_list = [res  for res in consts.config['resolutions'].keys()]

        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path_2',target_image)
        else:
            window['target_image_path_2'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['select_list_2_1'].update(values=resolutions_list,value=resolutions_list[0],visible=True)
        window['result_text_1'].update(visible=True)
        window['result_text_2'].update(result_text,visible=True)
        window['result_text_3'].update(visible=False)

    window.refresh()



def change_tab(window:sg.Window,tab:str,target:str):
    '''Change tab'''
    if tab == 'First':
        highlight_buttons(window,'sidebar_method_run_tesseract','red')
        update_method_layout(window,'run_tesseract',target)
        method = 'run_tesseract'
    elif tab == 'Second':
        highlight_buttons(window,'sidebar_method_ocr_pipeline','red')
        update_method_layout(window,'ocr_pipeline',target)
        method = 'calculate_dpi'

    return method


def config_pipeline(window:sg.Window,image_path:str):
    '''Apply config pipeline method to image and update image element'''
    
    config_window = build_gui_config_pipeline()

    while True:
        event, values = config_window.read()
        if event in [sg.WIN_CLOSED, 'Cancel']:
            config_window.close()
            break
        elif event in ['save']:
            pipeline_config_method(values)
            config_window.close()
            break




def run_gui():
    conf = consts.config
    current_path = consts.current_path
    result_path = consts.result_path

    # create results folder
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    window = build_gui_main()
    
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
        last_window_size = window.size
        event, values = window.read()
        print(event)

        # check window size
        ## adaptelement sizes accordingly
        if event == 'Event':
            if last_window_size != window.size:
                update_sizes(window)
                update_method_layout(window,method,target_image)


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
        elif 'config_pipeline' in event:
            config_pipeline(window,target_image)

    ########################################
    # Methods sidebar
        elif  'sidebar_method_' in event:
            highlight_buttons(window,event,'red')
            method = "_".join(event.split('_')[2:])
            update_method_layout(window,method,target_image)

    ########################################
    # Tab
        elif 'tab_group' in event:
            method = change_tab(window,values['tab_group'],target_image)
        
        

    window.close()