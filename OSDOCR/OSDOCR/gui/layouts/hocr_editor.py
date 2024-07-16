import os
import PySimpleGUI as sg
from ..aux_utils.utils import place
from OSDOCR.aux_utils import consts


# consts
browse_img_input_value = '/home/braz/projetos/OCR-old_documents/study_cases/simple template/2-1.jpg'
browse_file_input_value = '/home/braz/projetos/OCR-old_documents/results/2-1______88a3d1a9c2e7707cb70e8f9afa569005/processed/clean_ocr.json'

def ocr_editor_layour()->sg.Window:
    '''Build window for ocr results editor'''
    
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
        ]
    ]

    # canvas (editor)
    canvas = [
        [
            place(sg.Button('Save as copy',key='save_ocr_results_copy')),
            place(sg.Button('Save',key='save_ocr_results')),
            place(sg.Button('Reset',key='reset_ocr_results')),
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
            place(sg.Text('Box Type: ')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Title',text_color='red')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Text',text_color='yellow')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Image',text_color='black')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Highlight',text_color='purple')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Caption',text_color='white')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Delimiter',text_color='blue')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('Other',text_color='green')),
        ],
        [
            place(sg.Text('* ')),
            place(sg.Text('DEFAULT COLOR',key='text_default_color')),
        ]
    ]

    block_info = [
        [
            place(sg.Text('Block ')),
            place(sg.Text('',key='text_block_id')),
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


    # body, composed of side bar and canvas
    body = [
        [
            sg.Column(left_side_bar,vertical_alignment='top',scrollable=True,vertical_scroll_only=True,expand_x=True,expand_y=True),
            sg.Column(canvas,vertical_alignment='top',scrollable=True,expand_x=True,expand_y=True,key='canvas_body'),
            sg.Column(right_side_bar,vertical_alignment='top',scrollable=True,vertical_scroll_only=True,expand_x=True,expand_y=True),
        ]
    ]

    # main layout
    editor = [
        [
            upper_row,
            body
        ]
    ]


    window = sg.Window('OCR Editor',editor,finalize=True,resizable=True,size=(1200,800),relative_location=(500,100))
    window.bind('<Configure>',"Event")
    return window