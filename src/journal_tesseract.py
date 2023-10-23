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
from ocr_box_module.ocr_box import *
from ocr_box_module.ocr_box_analyser import *
from ocr_engines.engine_utils import tesseract_search_img


current_path = os.path.dirname(os.path.realpath(__file__))
result_path = f'{current_path}/results'

conf = {}



def read_configs():
    '''Read program configs from config.json'''
    global current_path,conf
    if os.path.exists(f'{current_path}/config/conf.json'):
        conf_file = open(f'{current_path}/config/conf.json','r')
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
    conf_file = open(f'{current_path}/config/conf.json','w')
    json.dump(conf,conf_file,indent=4)
    conf_file.close()


def update_search_block_og(window,target_image=None):
    '''GUI - Update search block for original image'''
    global result_path
    if target_image and os.path.exists(f'{result_path}/result.json'):
        ocr_results = OCR_Box(f'{result_path}/result.json')
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

def update_search_block_fixed(window,target_image=None):
    '''GUI - Update search block for fixed image'''
    global result_path
    if target_image and os.path.exists(f'{result_path}/fixed/result_fixed.json'):
        ocr_results = OCR_Box(f'{result_path}/fixed/result_fixed.json')
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



def save_results(ocr_results:OCR_Box,image_path:str):
    '''Saves results gathered from ocr_results to files'''
    global result_path
    img = draw_bounding_boxes(ocr_results,image_path)
    # create result files

    # create result image
    cv2.imwrite(f'{result_path}/result.jpg',img)

    
    # save result data
    result_dict_file = open(f'{result_path}/result.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    result_csv_file = open(f'{result_path}/result.csv','w')
    df = pd.DataFrame(ocr_results.to_dict())
    df.to_csv(result_csv_file)
    result_csv_file.close()
    
    # save result processed data
    data_processed = analyze_text(ocr_results)
    result_file = open(f'{result_path}/result_processed.json','w')
    json.dump(data_processed,result_file,indent=4)
    result_file.close()


def run_tesseract(image_path):
    '''GUI - Run text search on target image'''
    global result_path,conf

    results = tesseract_search_img(image_path)
    ocr_results = results['ocr_results']
    data_text = results['data_text']
    data_pdf = results['data_pdf']
    data_xml = results['data_xml']
    
    # save results

    # save results from ocr_results
    save_results(ocr_results,image_path)

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
            sg.Button("Draw journal delimiters",key='button_draw_journal_delimiters'),
            sg.Image(filename=None,visible=False,key='journal_delimiters_image'),
        ],
        [
            sg.Button("Draw journal template",key='button_journal_template'),
            sg.Image(filename=None,visible=False,key='journal_template_image'),
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
                ocr_results = OCR_Box(f'{result_path}/result.json')
                box_level = values['draw_bounding_boxes_level']
                image = draw_bounding_boxes(ocr_results,target_image,[box_level])
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


        elif event == 'button_test_improve_bounds':
            if os.path.exists(f'{result_path}/result.json'):
                window['progress_text'].update(visible=True)

                ocr_results = OCR_Box(f'{result_path}/result.json')
                ocr_results = improve_bounds_precision(ocr_results,target_image if target_image else f'{result_path}/result.jpg','progress_text',window)

                new_result_file = open(f'{result_path}/result_improved.json','w')
                json.dump(ocr_results,new_result_file,indent=4)
                new_result_file.close()

                new_result_file_csv = open(f'{result_path}/result_improved.csv','w')
                df = pd.DataFrame(ocr_results)
                df.to_csv(new_result_file_csv)
                new_result_file_csv.close()

                window['progress_text'].update(visible=False)

        elif event == 'button_test_alt_analyse':
            if os.path.exists(f'{result_path}/result.json'):
                ocr_results = OCR_Box(f'{result_path}/result.json')
                ocr_results = analyze_text(ocr_results)
                new_result_file = open(f'{result_path}/result_processed_alt.json','w')
                json.dump(ocr_results,new_result_file,indent=4)
                new_result_file.close()

        elif event == 'button_test_black_and_white':
            if target_image:
                image = black_and_white(target_image)
                image.save('test_bw.jpg')
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_draw_journal_delimiters':
            if os.path.exists(f'{result_path}/result.json') and target_image:
                ocr_results = OCR_Box(f'{result_path}/result.json')
                ocr_results.id_boxes([2])
                image_info = get_image_info(target_image)
                # get delimiters
                delimiters = ocr_results.get_delimiters()
                page = OCR_Box(ocr_results.get_boxes_level(0)[0]) 
                for delimiter in delimiters:
                    page.add_child(delimiter)
                img = draw_bounding_boxes(page,target_image)
                cv2.imwrite(f'{result_path}//journal_delimiters.jpg',img)
                img = Image.fromarray(img)
                bio = io.BytesIO()
                img.save(bio,format='png')
                window['journal_delimiters_image'].update(data=bio.getvalue(),visible=True)
                window.refresh()
                
            else:
                sg.popup('No target image selected')
        
        elif event == 'button_journal_template':
            if os.path.exists(f'{result_path}/fixed/result_fixed.json') and target_image:
                ocr_results = OCR_Box(f'{result_path}/fixed/result_fixed.json')
                image_info = get_image_info(target_image)
                journal = estimate_journal_template(ocr_results,image_info)
                img = draw_journal_template(journal,target_image)
                cv2.imwrite(f'{result_path}//journal_template.jpg',img)
                img = Image.fromarray(img)
                bio = io.BytesIO()
                img.save(bio,format='png')
                window['journal_template_image'].update(data=bio.getvalue(),visible=True)
                window.refresh()
                
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
                ocr_results = OCR_Box(f'{result_path}/result.json')
                box_level = values['fix_box_bounds_level']
                ocr_results.id_boxes([box_level])
                image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
                bio = io.BytesIO()
                pil_img = Image.fromarray(image)
                pil_img.save(bio,format='png')
                window['fix_box_bounds_image_og'].update(data=bio.getvalue(),visible=True)
                window.refresh()

                ocr_results = bound_box_fix(ocr_results,box_level,get_image_info(target_image))
                image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
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
            if ocr_results:
                result_dict_file = open(f'{result_path}/fixed/result_fixed.json','w')
                json.dump(ocr_results.to_json(),result_dict_file,indent=4)
                result_dict_file.close()
                image = draw_bounding_boxes(ocr_results,target_image,[box_level],id=True)
                cv2.imwrite(f'{result_path}/fixed/result_fixed.jpg',image)
                csv = pd.DataFrame(ocr_results.to_dict())
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
                
                

                window['result_label_fix'].update(visible=True)
                window['result_label2_fix'].update(visible=True)
                window.refresh()
                window['column_fix_window'].contents_changed()

            else:
                sg.popup('No result data found. Please run fix first.')
        
        # search for block in original image
        elif event == 'button_search_block_og':
            if os.path.exists(f'{result_path}/result.json'):
                ocr_results = OCR_Box(f'{result_path}/result.json')
                ocr_results.id_boxes([2])
                block_id = values['search_block_og']
                text = ocr_results.to_text()
                print(text)
                window['result_text_search_block_og'].update(text,visible=True)
                window.refresh()
                window['column_fix_window'].contents_changed()
            else:
                sg.popup('No result data found. Please run text search first.')

        # search for block in fixed image
        elif event == 'button_search_block_fixed':
            if os.path.exists(f'{result_path}/fixed/result_fixed.json'):
                ocr_results = OCR_Box(f'{result_path}/fixed/result_fixed.json')
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
            if os.path.exists(f'{result_path}/fixed/result_fixed.json'):
                ocr_results = json.load(open(f'{result_path}/fixed/result_fixed.json','r'))
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






if __name__ == '__main__':
    read_configs()
    main()

