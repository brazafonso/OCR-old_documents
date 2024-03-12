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
from document_image_utils.image import *
from aux_utils.misc import *
from ocr_box_module.information_extraction import journal_template_to_text
from ocr_box_module.ocr_box import *
from ocr_box_module.ocr_box_analyser import *
from ocr_box_module.ocr_box_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article


methods = ['run_tesseract','fix_blocks','draw_bb','draw_journal_template',
           'calculate_reading_order','extract_articles','search_block']


def update_search_block_og(window:sg.Window,target_image=None):
    '''GUI - Update search block for original image'''
    if target_image:
        # results path
        results_path = f'{consts.result_path}/{path_to_id(target_image)}'

        if os.path.exists(f'{results_path}/result.json'):
            ocr_results = OCR_Box(f'{results_path}/result.json')
            ocr_results.id_boxes([2])
            image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
            image = Image.fromarray(image)
            bio = io.BytesIO()
            image.save(bio, format="png")
            # get available block ids
            block_ids = [block.id for block in ocr_results.get_boxes_level(2)]
            window['search_block_og'].update(values=block_ids,value=block_ids[0],disabled=False)
            window['result_img_search_block_og'].update(data=bio.getvalue(),visible=True)
            window.refresh()
            window['column_fix_window'].contents_changed()

def update_search_block_fixed(window:sg.Window,target_image=None):
    '''GUI - Update search block for fixed image'''
    if target_image:
        # results path
        results_path = f'{consts.result_path}/{path_to_id(target_image)}'

        if os.path.exists(f'{results_path}/fixed/result_fixed.json'):
            ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
            ocr_results.id_boxes([2])
            image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
            image = Image.fromarray(image)
            bio = io.BytesIO()
            image.save(bio, format="png")
            # get available block ids
            block_ids = [block.id for block in ocr_results.get_boxes_level(2)]
            window['search_block_fixed'].update(values=block_ids,value=block_ids[0],disabled=False)
            window['result_img_search_block_fixed'].update(data=bio.getvalue(),visible=True)
            window.refresh()
            window['column_fix_window'].contents_changed()







def run_tesseract_results(window:sg.Window):
    '''GUI - Show results of text search on target image'''
    target_image = consts.config['target_image_path']

    if target_image:

        # results path
        results_path = f'{consts.result_path}/{path_to_id(target_image)}'

        # update result image
        image = Image.open(f'{results_path}/result.png')
        image.thumbnail((800, 800))
        bio = io.BytesIO()
        image.save(bio, format="png")
        window['result_img'].update(data=bio.getvalue(),visible=True)
        
        #update result text
        result_text = open(f'{results_path}/result.txt','r').read()
        window['result_text'].update(result_text,visible=True)

        processed_result = json.load(open(f'{results_path}/result_processed.json','r'))
        window['result_text2'].update(processed_result,visible=True)

        #update result columns
        columns_image = split_page_columns(target_image if target_image else f'{results_path}/result.png',processed_result['columns'])
        columns_image = concatentate_columns(columns_image)
        if columns_image:
            columns_image.thumbnail((800, 800))
            bio2 = io.BytesIO()
            columns_image.save(bio2,format='png')
            window['result_columns'].update(data=bio2.getvalue(),visible=True)
        window.refresh()

    


def update_image_element(window:sg.Window,image_element:str,new_image,size:tuple=(500,700)):
    '''Update image element'''
    if new_image and type(new_image) in [str,'MatLike']:
        image = None
        if type(new_image) == str:
            image = cv2.imread(new_image)
        else:
            image = new_image
        image = cv2.resize(image,size)
        bio = cv2.imencode('.png',image)[1].tobytes()
        window[image_element].update(data=bio,visible=True)
        window.refresh()



def apply_method(window:sg.Window,image_path:str,method:str):
    '''Apply method to image and update image element'''
    new_image = cv2.imread(image_path)

    if method == 'run_tesseract':
        # run tesseract
        run_tesseract_results(window)
        # update result image
        ## image with lvl. 2 BB drawn
        new_image = draw_bounding_boxes(OCR_Box(f'{consts.result_path}/target/result.json'),image_path,[2,3],id=True)
        update_image_element(window,'result_img',new_image)

    else:
        print('method not implemented')


def highlight_buttons(window:sg.Window,button:str,color:str,default_color:str='#283b5b'):
    # reset all buttons
    for element in window.AllKeysDict.keys():
        if 'sidebar_' in element:
            button_element = window[element]
            button_element.update(button_color=('white',default_color))

    # highlight button
    button_element = window[button]
    button_element.update(button_color=('white',color))

    window.refresh()


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
            sg.Button('Tesseract',key='sidebar_run_tesseract'),
        ],
        [
            sg.Button('Extract Articles',key='sidebar_extract_articles'),
        ]
    ]

    first_layout_1 = [
        [
            sg.Column(method_sidebar,expand_x=True,expand_y=True),
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
            sg.Button('Apply',key='apply'),
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

    method_sidebar_2 = [
        [
            sg.Button('Method3',key='sidebar_method3'),
        ]
    ]


    second_layout_1 = [
        [
            sg.Column(method_sidebar_2,expand_x=True,expand_y=True),
        ]
    ]

    second_layout_2 = [
        [
            sg.Image(filename=None,visible=True,key='target_image_path',size=(500,700)),
            sg.Button('Apply',key='apply'),
            sg.Image(filename=None,visible=True,key='result_img',size=(500,700)),
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

    column_target = [
        [
            sg.Image(filename=None,visible=False,key='target_image_path')
        ]
    ]

    # main window layout
    main_layout = [
        [
            sg.FileBrowse(file_types=(("IMG Files", "*.*"),),initial_folder=f'{current_path}/../docs/jornais/',button_text="Choose Image",key='browse_file',target='target_input'),
            sg.Input(default_text='' if not conf['target_image_path'] else conf['target_image_path'],key='target_input',enable_events=True),
            sg.Button("Search Text",key='button_tesseract')
        ],
        [
            sg.Text('Target: '),
            sg.Column(column_target,scrollable=True,size=(800,500),key='column_target_image')
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
            sg.Button("Draw journal delimiters",key='button_draw_journal_delimiters'),
            sg.Image(filename=None,visible=False,key='journal_delimiters_image'),
        ],
        [
            sg.Button("Draw journal template",key='button_journal_template'),
            sg.Image(filename=None,visible=False,key='journal_template_image'),
        ],
        [
            sg.Button("Seperate template text",key='button_journal_template_text')
        ],
        [
            sg.Button("Calculate reading order",key='button_calculate_reading_order'),
            sg.Image(filename=None,visible=False,key='initial_reading_order_image'),
            sg.Image(filename=None,visible=False,key='reading_order_image'),
        ],
        [
            sg.Button("Calculate reading order | context",key='button_calculate_reading_order_context'),
            sg.Image(filename=None,visible=False,key='initial_reading_order_image_context'),
            sg.Image(filename=None,visible=False,key='reading_order_image_context'),
        ],
        [
            sg.Button("Extract articles",key='button_extract_articles'),
            sg.Image(filename=None,visible=False,key='extract_articles_image'),
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

    window = sg.Window(title="OSDOcr",
                       layout=layout,
                       finalize=True,
                       size=(1000,800),
                       resizable=True)
    
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
            if target_image and target_image.strip() != '':
                # update target image
                image = Image.open(target_image)
                image.thumbnail((800, 800))
                bio = io.BytesIO()
                image.save(bio, format="png")
                window['target_image_path'].update(data=bio.getvalue(),visible=True)
                conf['target_image_path'] = target_image
                save_configs()
                # update og image (fix tab)
                update_search_block_og(window,target_image)
                window.refresh()

        # use tesseract to search for text in image
        if event == 'button_tesseract':
            target_image = values['target_input']
            print('Target:',target_image)
            if  target_image and target_image.strip() != '':
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'

                # clean results folder files
                if os.path.exists(results_path):
                    files = os.listdir(results_path)
                    for file in files:
                        # if is dir, delete dir
                        if os.path.isdir(f'{results_path}/{file}'):
                            shutil.rmtree(f'{results_path}/{file}')
                        else:
                            os.remove(f'{results_path}/{file}')

                conf['target_image_path'] = target_image
                save_configs()
                run_tesseract(target_image)
                # update og image (fix tab)
                update_search_block_og(window,target_image)

                # create fixed result folder
                if not os.path.exists(f'{results_path}/fixed'):
                    os.makedirs(f'{results_path}/fixed')
                


        # draw bounding boxes
        elif event == 'draw_bounding_boxes':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'

                if os.path.exists(f'{results_path}/result.json'):
                    if os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    else:
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                    ocr_results = categorize_boxes(ocr_results)
                    box_level = values['draw_bounding_boxes_level']
                    image = draw_bounding_boxes(ocr_results,target_image,[box_level])
                    bio = io.BytesIO()
                    pil_img = Image.fromarray(image)
                    pil_img.save(bio,format='png')
                    window['bounding_boxes_image'].update(data=bio.getvalue(),visible=True)
                    window['button_hide_draw_bounding_boxes'].update(visible=True)
                    window.refresh()

                    # save tmp png
                    cv2.imwrite(f'{results_path}/test.png',image)
            else:
                sg.popup('No result data found. Please run text search first.')

        # hide bounding boxes
        elif event == 'button_hide_draw_bounding_boxes':
            window['bounding_boxes_image'].update(visible=False)
            window['button_hide_draw_bounding_boxes'].update(visible=False)
            window.refresh()

        elif event == 'button_test_alt_analyse':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/result.json'):
                    ocr_results = OCR_Box(f'{results_path}/result.json')
                    ocr_results = analyze_text(ocr_results)
                    new_result_file = open(f'{results_path}/result_processed_alt.json','w')
                    json.dump(ocr_results,new_result_file,indent=4)
                    new_result_file.close()

        elif event == 'button_test_black_and_white':
            if target_image:
                image = black_and_white(target_image)
                image.save('test_bw.png')
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_draw_journal_delimiters':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/result.json'):
                    ocr_results = OCR_Box(f'{results_path}/result.json')
                    ocr_results.id_boxes([2])
                    image_info = get_image_info(target_image)
                    # get delimiters
                    delimiters = ocr_results.get_delimiters()
                    page = OCR_Box(ocr_results.get_boxes_level(0)[0]) 
                    for delimiter in delimiters:
                        page.add_child(delimiter)
                    img = draw_bounding_boxes(page,target_image)
                    cv2.imwrite(f'{results_path}//journal_delimiters.png',img)
                    bio = cv2.imencode('.png',img)[1].tobytes()
                    window['journal_delimiters_image'].update(data=bio,visible=True)
                    window.refresh()
                
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_journal_template':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json') or os.path.exists(f'{results_path}/result.json'):
                    # create fixed result file
                    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                        ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
                        result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                        result_dict_file.close()
                        image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                        cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                        csv = pd.DataFrame(ocr_results.to_dict())
                        csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
                        
                    # draw journal template
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    image_info = get_image_info(target_image)
                    journal = estimate_journal_template(ocr_results,image_info)
                    img = draw_journal_template(journal,target_image)
                    cv2.imwrite(f'{results_path}//journal_template.png',img)
                    img = Image.fromarray(img)
                    bio = io.BytesIO()
                    img.save(bio,format='png')
                    window['journal_template_image'].update(data=bio.getvalue(),visible=True)
                    window.refresh()
                
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_journal_template_text':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json') or os.path.exists(f'{results_path}/result.json'):
                    # create fixed result file
                    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                        ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
                        result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                        result_dict_file.close()
                        image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                        cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                        csv = pd.DataFrame(ocr_results.to_dict())
                        csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
                    
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    image_info = get_image_info(target_image)
                    journal_template = estimate_journal_template(ocr_results,image_info)
                    text = journal_template_to_text(journal_template,ocr_results)
                    text_file = open(f'{results_path}/journal_template_text.txt','w')
                    text_file.write(text)
                    text_file.close()
                
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_calculate_reading_order':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json') or os.path.exists(f'{results_path}/result.json'):
                    # create fixed result file
                    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                        ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
                        result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                        result_dict_file.close()
                        image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                        cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                        csv = pd.DataFrame(ocr_results.to_dict())
                        csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
                    
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    ocr_results = categorize_boxes(ocr_results)

                    image_info = get_image_info(target_image)
                    journal_template = estimate_journal_template(ocr_results,image_info)
                    columns_area = image_info
                    columns_area.remove_box_area(journal_template['header'])
                    columns_area.remove_box_area(journal_template['footer'])
                    print('header',journal_template['header'])
                    print('footer',journal_template['footer'])
                    print(columns_area)
                    # draw initial reading order
                    ocr_results.clean_ids()
                    ocr_results.id_boxes([2],{2:1},False,columns_area)
                    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                    cv2.imwrite(f'{results_path}/initial_reading_order.png',image)
                    bio = cv2.imencode('.png',img)[1].tobytes()
                    window['initial_reading_order_image'].update(data=bio,visible=True)
                    window.refresh()
                    
                    reading_order = calculate_reading_order_naive(ocr_results,columns_area)

                    # draw reading order
                    image = draw_bounding_boxes(reading_order,target_image,[2],id=True)
                    cv2.imwrite(f'{results_path}/reading_order.png',image)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['reading_order_image'].update(data=bio,visible=True)
                    window.refresh()

        elif event == 'button_calculate_reading_order_context':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json') or os.path.exists(f'{results_path}/result.json'):
                    # create fixed result file
                    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                        ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
                        result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                        result_dict_file.close()
                        image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                        cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                        csv = pd.DataFrame(ocr_results.to_dict())
                        csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
                    
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    ocr_results = categorize_boxes(ocr_results)

                    image_info = get_image_info(target_image)
                    journal_template = estimate_journal_template(ocr_results,image_info)
                    columns_area = image_info
                    columns_area.remove_box_area(journal_template['header'])
                    columns_area.remove_box_area(journal_template['footer'])
                    print('header',journal_template['header'])
                    print('footer',journal_template['footer'])
                    print(columns_area)

                    # draw initial reading order
                    ocr_results.clean_ids()
                    ocr_results.id_boxes([2],{2:1},True,columns_area)
                    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                    cv2.imwrite(f'{results_path}/initial_reading_order_context.png',image)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['initial_reading_order_image_context'].update(data=bio,visible=True)
                    window.refresh()
                    
                    reading_order = calculate_reading_order_naive_context(ocr_results,columns_area)

                    # draw reading order
                    image = draw_bounding_boxes(reading_order,target_image,[2],id=True)
                    cv2.imwrite(f'{results_path}/reading_order_context.png',image)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['reading_order_image_context'].update(data=bio,visible=True)
                    window.refresh()

        elif event == 'button_extract_articles':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json') or os.path.exists(f'{results_path}/result.json'):
                    # create fixed result file
                    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                        ocr_results = OCR_Box(f'{results_path}/result.json')
                        ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
                        result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                        result_dict_file.close()
                        image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
                        cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                        csv = pd.DataFrame(ocr_results.to_dict())
                        csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
                    
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    ocr_results = categorize_boxes(ocr_results)

                    image_info = get_image_info(target_image)
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
                        
                    with open(f'{results_path}/articles.txt','w') as f:
                        for article in articles:
                            article = Article(article)
                            f.write(article.pretty_print())
                            f.write('\n')

                    with open(f'{results_path}/articles.md','w') as f:
                        for article in articles:
                            article = Article(article)
                            f.write(article.to_md())
                            f.write('\n'+'==='*40 + '\n')

                    # draw reading order
                    image = draw_articles(articles,target_image)
                    cv2.imwrite(f'{results_path}/articles.png',image)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['extract_articles_image'].update(data=bio,visible=True)
                    window.refresh()


    ########################################
    # Results tab
        # show results of image search
        elif event == 'button_result':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/result.png') and os.path.exists(f'{results_path}/result.txt') and os.path.exists(f'{results_path}/result.json') and os.path.exists(f'{results_path}/result_processed.json'):
                    run_tesseract_results(window)
            else:
                sg.popup('No result data found. Please run text search first.')

    ########################################
    # Fix tab
        # fix box bounds
        elif event == 'fix_box_bounds':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/result.json'):
                    ocr_results = OCR_Box(f'{results_path}/result.json')
                    box_level = values['fix_box_bounds_level']
                    ocr_results.id_boxes([box_level])
                    image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['fix_box_bounds_image_og'].update(data=bio,visible=True)
                    window.refresh()

                    ocr_results = bound_box_fix(ocr_results,box_level,get_image_info(target_image))
                    image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
                    bio = cv2.imencode('.png',image)[1].tobytes()
                    window['fix_box_bounds_image_new'].update(data=bio,visible=True)
                    window['button_save_fix_result'].update(visible=True)
                    window.refresh()

                    # update fixed image (fix tab)
                    update_search_block_fixed(window,target_image)
            else:
                sg.popup('No target image selected, or no result data found. Please run text search first.')
        
        # save fix result
        elif event == 'button_save_fix_result':
            if ocr_results and target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'

                result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
                json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                result_dict_file.close()
                image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
                cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
                csv = pd.DataFrame(ocr_results.to_dict())
                csv.to_csv(f'{results_path}/fixed/result_fixed.csv')

                # update fixed image (fix tab)
                update_search_block_fixed(window,target_image)

        # show fix results
        elif event == 'button_result_fix':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.png') and os.path.exists(f'{results_path}/fixed/result_fixed.json') and os.path.exists(f'{results_path}/result.json'):
                    image = Image.open(f'{results_path}/fixed/result_fixed.png')
                    image.thumbnail((800, 800))
                    bio = io.BytesIO()
                    image.save(bio, format="png")
                    window['result_img_fix'].update(data=bio.getvalue(),visible=True)
                    
                    

                    window['result_label_fix'].update(visible=True)
                    window['result_label2_fix'].update(visible=True)
                    window.refresh()
                    window['column_fix_window'].contents_changed()

            else:
                sg.popup('No result data found. Please run fix first.')
        
        # search for block in original image
        elif event == 'button_search_block_og':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/result.json'):
                    ocr_results = OCR_Box(f'{results_path}/result.json')
                    ocr_results.id_boxes([2])
                    block_id = values['search_block_og']
                    original_box = ocr_results.get_box_id(block_id,2)
                    text = ''
                    if original_box:
                        text = original_box.to_text()
                    print(text)
                    window['result_text_search_block_og'].update(text,visible=True)
                    window.refresh()
                    window['column_fix_window'].contents_changed()
            else:
                sg.popup('No result data found. Please run text search first.')

        # search for block in fixed image
        elif event == 'button_search_block_fixed':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                    ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
                    ocr_results.id_boxes([2])
                    block_id = values['search_block_fixed']
                    fixed_box = ocr_results.get_box_id(block_id,2)
                    text = ''
                    if fixed_box:
                        text = fixed_box.to_text()
                    print(text)
                    window['result_text_search_block_fixed'].update(text,visible=True)
                    window.refresh()
                    window['column_fix_window'].contents_changed()
            else:
                sg.popup('No result data found. Please run fix first.')
        
        elif event == 'button_overwrite_original_result':
            if target_image:
                # results path
                results_path = f'{result_path}/{path_to_id(target_image)}'
                if os.path.exists(f'{results_path}/fixed/result_fixed.json'):
                    ocr_results = json.load(open(f'{results_path}/fixed/result_fixed.json','r'))
                    save_results(ocr_results,target_image)
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