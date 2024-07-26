import os
import PySimpleGUI as sg
from ..aux_utils.utils import place
from OSDOCR.aux_utils import consts


# consts
browse_img_input_value = '/home/braz/projetos/OCR-old_documents/study_cases/simple template/2-1.jpg'
browse_file_input_value = '/home/braz/projetos/OCR-old_documents/results/2-1______88a3d1a9c2e7707cb70e8f9afa569005/processed/clean_ocr.json'

def ocr_editor_layour()->sg.Window:
    '''Build window for ocr results editor'''

    window_size = (1200,800)
    window_location = (500,100)
    
    # target image and ocr results selector
    upper_row = [
        [
                place(sg.FileBrowse(file_types=(("IMG Files", "*.*"),),button_text="Choose Image",key='browse_image',target='target_input',initial_folder=os.getcwd())),
                place(sg.Input(default_text=browse_img_input_value,key='target_input',enable_events=True)),

                place(sg.FileBrowse(file_types=(("OCR Files", "*.json"),),button_text="Choose OCR Results",key='browse_file',target='ocr_results_input',initial_folder=os.getcwd())),
                place(sg.Input(default_text=browse_file_input_value,key='ocr_results_input',enable_events=True))
        ]
    ]

    # side bar for methods (palceholder)
    left_side_bar = [
        [
            place(sg.Button('New Block',key='method_new_block')),
        ],
        [
            place(sg.Button('Join Blocks',key='method_join')),
        ],
        [
            place(sg.Button('Split Blocks',key='method_split')),
        ],
        [
            place(sg.Button('Split Whitespaces',key='method_split_whitespaces')),
        ],
        [
            place(sg.Button('Fix intersections',key='method_fix_intersections')),
        ],
        [
            place(sg.Button('Adjust bounding boxes',key='method_adjust_bounding_boxes')),
        ],
        [
            place(sg.Button('Calculate reading order',key='method_calculate_reading_order')),
        ],
    ]


    # canvas (editor)
    canvas = [
        [
            place(sg.Button('Save as copy',key='save_ocr_results_copy')),
            place(sg.Button('Save',key='save_ocr_results')),
            place(sg.Button('Reset',key='reset_ocr_results')),
            place(sg.Button('<-',key='undo_ocr_results')),
            place(sg.Button('->',key='redo_ocr_results')),
            place(sg.Button('Zoom In',key='zoom_in')),
            place(sg.Button('Zoom Out',key='zoom_out')),
        ],
        [
            place(sg.Canvas(key='canvas',size=(600,800),expand_x=True,expand_y=True))
        ]
    ]

    block_type_legend = [
        [
            place(sg.Text('Toogle Block Type: ')),
            place(sg.Checkbox(text='',key='checkbox_toggle_block_type',enable_events=True)),
        ],
        [
            place(sg.Text('Filter Box Type: ')),
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_title_text')),
            place(sg.Text('Title',enable_events=True,key='box_type_title_text')),
            place(sg.Text('',size=(2,1),text_color='red',background_color='red',enable_events=True,key='box_type_title_text')),
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_text_text')),
            place(sg.Text('Text',enable_events=True,key='box_type_text_text')),
            place(sg.Text('',size=(2,1),text_color='yellow',background_color='yellow',enable_events=True,key='box_type_text_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_image_text')),
            place(sg.Text('Image',enable_events=True,key='box_type_image_text')),
            place(sg.Text('',size=(2,1),text_color='black',background_color='black',enable_events=True,key='box_type_image_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_highlight_text')),
            place(sg.Text('Highlight',enable_events=True,key='box_type_highlight_text')),
            place(sg.Text('',size=(2,1),text_color='purple',background_color='purple',enable_events=True,key='box_type_highlight_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_caption_text')),
            place(sg.Text('Caption',enable_events=True,key='box_type_caption_text')),
            place(sg.Text('',size=(2,1),text_color='white',background_color='white',enable_events=True,key='box_type_caption_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_delimiter_text')),
            place(sg.Text('Delimiter',enable_events=True,key='box_type_delimiter_text')),
            place(sg.Text('',size=(2,1),text_color='blue',background_color='blue',enable_events=True,key='box_type_delimiter_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_other_text')),
            place(sg.Text('Other',enable_events=True,key='box_type_other_text')),
            place(sg.Text('',size=(2,1),text_color='green',background_color='green',enable_events=True,key='box_type_other_text'))
        ],
        [
            place(sg.Text('* ',enable_events=True,key='box_type_all_text')),
            place(sg.Text('ALL',enable_events=True,key='box_type_all_text')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('DEFAULT COLOR')),
            place(sg.Text('',size=(2,1),text_color='black',background_color='black',key='text_default_color'))
        ],
    ]

    block_info = [
        [
            place(sg.Text('Block ')),
            place(sg.Input('',key='input_block_id',size=(3,1))),
            place(sg.Text('Coordinates: ')),
            place(sg.Text('',key='text_block_coords')),
        ],
        [
            place(sg.Text('Type: ')),
            place(sg.Combo(['title','text','image','highlight','caption','delimiter','other'],default_value='',key='list_block_type',enable_events=True)),
        ],
        [
            place(sg.Text('Text: '))
        ],
        [
            place(sg.Multiline(default_text='',key='input_block_text',enable_events=True,size=(50,10),auto_size_text=True,autoscroll=True))
        ],
        [
            place(sg.Button('OCR',key='button_ocr_block'))
        ],
        [
            place(sg.Button('Save',key='button_save_block')),place(sg.Button('Delete',key='button_delete_block'))
        ],
    ]

    # side bar for info about ocr results
    right_side_bar = [
        [
            sg.Frame('',block_type_legend)
        ],
        [
            sg.Frame('',block_info,key='frame_block_info')
        ]
    ]


    context_menu = [
        '',
        [
            'Send to front::context_menu_send_to_front',
            'Send to back::context_menu_send_to_back',
        ]
    ]

    # body, composed of side bar and canvas
    body = [
        [
            sg.Column(left_side_bar,vertical_alignment='top',scrollable=True,vertical_scroll_only=True,expand_x=True,expand_y=True,size=(window_size[0]/5,None),key='body_left_side_bar'),
            sg.Column(canvas,vertical_alignment='top',scrollable=True,expand_x=True,expand_y=True,right_click_menu=context_menu,size=(window_size[0]/5*3,None),key='body_canvas'),
            sg.Column(right_side_bar,vertical_alignment='top',scrollable=True,vertical_scroll_only=True,expand_x=True,expand_y=True,size=(window_size[0]/5,None),key='body_right_side_bar'),
        ]
    ]

    # main layout
    editor = [
        [
            upper_row,
            body
        ]
    ]


    window = sg.Window('OCR Editor',editor,finalize=True,resizable=True,size=window_size,relative_location=window_location)
    window.bind('<Configure>',"Event")
    return window