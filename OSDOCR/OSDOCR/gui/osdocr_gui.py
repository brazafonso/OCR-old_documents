'''Old Structured Document OCR - GUI'''

import os
import PySimpleGUI as sg
from OSDOCR.aux_utils import consts
from document_image_utils.image import *
from OSDOCR.aux_utils.misc import *
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
        auto_rotate_method(window,image_path,values)
    elif method == 'unite_blocks':
        unite_blocks_method(window,image_path,values)
    elif method == 'divide_columns':
        divide_columns_method(window,image_path,values)
    elif method == 'divide_journal':
        divide_journal_method(window,image_path,values)
    elif method == 'remove_document_images':
        remove_document_images_method(window,image_path,values)
    elif method == 'upscale_image':
        upscale_image_method(window,image_path,values)
    elif method == 'denoise_image':
        denoise_image_method(window,image_path,values)
    elif method == 'cut_margins':
        cut_margins_method(window,image_path,values)
    elif method == 'binarize':
        binarize_method(window,image_path,values)
        

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
    results_path = f'{consts.result_path}/{path_to_id(o_image)}'
    processed_folder_path = f'{results_path}/processed'
    latest_image = get_last_image_path(o_image)
    print(latest_image)


    window['target_image_path'].update(visible=False)
    window['target_image_path_2'].update(visible=False)
    window['apply'].update(visible=False)
    # disable extra options
    window['checkbox_1_1'].update(visible=False)
    window['checkbox_1_2'].update(visible=False)
    window['select_list_text_1_1'].update(visible=False)
    window['select_list_1_1'].update(visible=False)
    window['config_pipeline'].update(visible=False)
    window['select_list_2_1'].update(visible=False)
    window['result_text_1'].update(visible=False)
    window['result_text_2'].update(visible=False)
    window['result_text_3'].update(visible=False)

    ## TAB 1
    if method == 'run_tesseract' and latest_image:
        result_image = f'{processed_folder_path}/ocr_results.png'
        # update target image
        update_image_element(window,'target_image_path',latest_image)

        # update apply button
        window['apply'].update(visible=True)
        # update options
        window['checkbox_1_1'].update(visible=True)
        window['checkbox_1_2'].update(visible=True,text='Auto Rotate:')
        window['select_list_text_1_1'].update(value='Skew Direction:',visible=True)
        window['select_list_1_1'].update(value='Auto',values=['Auto','Clockwise','Counterclockwise'],visible=True)

        # check if result image exists
        if latest_image and os.path.exists(result_image):
            # update result image
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'fix_blocks':
        result_image = f'{processed_folder_path}/ocr_results.png'
        fixed_image = f'{processed_folder_path}/clean_ocr.png'

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)

        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        if os.path.exists(fixed_image):
            # update result image
            update_image_element(window,'result_img',fixed_image)
        else:
            window['result_img'].update(visible=False)

        
    elif method == 'journal_template' and latest_image:
        result_image = f'{processed_folder_path}/result_journal_template.png'
        # update target image
        update_image_element(window,'target_image_path',latest_image)

        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window, 'result_img', result_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'reading_order':
        result_image = f'{processed_folder_path}/ocr_results_id.png'
        reading_order_image = f'{processed_folder_path}/result_reading_order.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        # enable checkbox
        window['checkbox_1_1'].update(visible=True)
        window['checkbox_1_2'].update(text='Ignore Delimeters:',visible=True)


        if os.path.exists(reading_order_image):
            # update result image
            update_image_element(window,'result_img',reading_order_image)
        else:
            window['result_img'].update(visible=False)


    elif method == 'extract_articles':
        result_image = f'{processed_folder_path}/ocr_results.png'
        articles_image = f'{results_path}/articles.png'
        # check if result image exists
        if os.path.exists(result_image):
            # update target image
            update_image_element(window,'target_image_path',result_image)
        else:
            window['result_img'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        # enable checkbox
        window['checkbox_1_1'].update(visible=True)
        window['checkbox_1_2'].update(text='Ignore Delimeters:',visible=True)

        if os.path.exists(articles_image):
            # update result image
            update_image_element(window,'result_img',articles_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'auto_rotate':
        result_image = f'{processed_folder_path}/fix_rotation.png'
        if latest_image:
            update_image_element(window,'target_image_path',latest_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'unite_blocks':
        target_image = f'{processed_folder_path}/ocr_results.png'
        result_image = f'{processed_folder_path}/result_united.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'divide_columns':
        target_image = latest_image
        result_image = f'{processed_folder_path}/divide_columns.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        window['select_list_text_1_1'].update(value='Analyses Type:',visible=True)
        window['select_list_1_1'].update(value='Pixels',values=['Blocks','Pixels'],visible=True)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'divide_journal':
        target_image = latest_image
        result_image = f'{processed_folder_path}/journal_areas.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)
        
    elif method == 'remove_document_images':
        target_image = latest_image
        result_image = f'{processed_folder_path}/removed_images.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        window['select_list_text_1_1'].update(value='Document type:',visible=True)
        window['select_list_1_1'].update(value='Leptonica',values=['Leptonica','Old','New'],visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'upscale_image':
        target_image = latest_image
        result_image = f'{processed_folder_path}/image_upscaling.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        window['select_list_text_1_1'].update(value='Upscaling Method:',visible=True)
        window['select_list_1_1'].update(value='autoscale',values=['autoscale','scale2x','scale4x'],visible=True)

        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'denoise_image':
        target_image = latest_image
        result_image = f'{processed_folder_path}/noise_removal.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        window['select_list_text_1_1'].update(value='Noise Level:',visible=True)
        window['select_list_1_1'].update(value=1,values=[0,1,2,3],visible=True)

        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'cut_margins':
        target_image = latest_image
        result_image = f'{processed_folder_path}/cut_margins.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    elif method == 'binarize':
        target_image = latest_image
        result_image = f'{processed_folder_path}/binarized.png'
        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path',target_image)
        else:
            window['target_image_path'].update(visible=False)
        # update apply button
        window['apply'].update(visible=True)
        window['checkbox_1_1'].update(visible=True)

        window['select_list_text_1_1'].update(value='Denoise strength:',visible=True)
        window['select_list_1_1'].update(value=10,values=[5,7,10,15,20],visible=True)
        if os.path.exists(result_image):
            update_image_element(window,'result_img',result_image)
        else:
            window['result_img'].update(visible=False)

    ## TAB 2
    elif method == 'ocr_pipeline':

        target_image = latest_image

        if o_image and os.path.exists(target_image):
            update_image_element(window,'target_image_path_2',target_image)
        else:
            window['target_image_path_2'].update(visible=False)
        
        window['apply'].update(visible=False)
        window['config_pipeline'].update(visible=True)
        window['apply'].update(visible=True)

    elif method == 'calculate_dpi':
        target_image = latest_image
        result_text = ''
        resolutions_list = [res  for res in consts.config['dimensions'].keys()]

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

def reset_target_image(target:str):
    '''Reset target image. Updates metadata info'''
    metadata = get_target_metadata(target)
    metadata['target_path'] = metadata['target_original_path']
    metadata['transformations'] = []
    metadata['ocr'] = False
    metadata['ocr_results_original_path'] = ''
    metadata['ocr_results_path'] = ''
    save_target_metadata(target,metadata)
    



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
        create_target_results_folder(target_image)
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
            create_target_results_folder(target_image)
            # update target image
            update_image_element(window,'target_image_path',target_image)
            update_method_layout(window,method,target_image)
            # save config
            conf['target_image_path'] = target_image
            save_configs()
        elif 'apply' in event:
            if target_image and method:
                try:
                    apply_method(window,values,target_image,method)
                except OCR_Tree_load_error:
                    sg.popup_error('Could not load OCR results. Please run OCR on the target.')
                except Exception as e:
                    sg.popup_error(e)
        elif 'config_pipeline' in event:
            config_pipeline(window,target_image)
        # reset target image to original
        elif event == 'reset_image':
            reset_target_image(target_image)
            update_method_layout(window,method,target_image)


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