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
    side_bar = [
        [
            place(sg.Button('Placeholder',key='method_placeholder')),
        ]
    ]

    # canvas (editor)
    canvas = [
        [
            place(sg.Button('Save',key='save_ocr_results')),
            place(sg.Button('Save as copy',key='save_ocr_results_copy')),
            place(sg.Button('Reset',key='reset_ocr_results')),
        ],
        [
            place(sg.Canvas(key='canvas',size=(1200,800),expand_x=True,expand_y=True))
        ]
    ]

    # body, composed of side bar and canvas
    body = [
        [
            sg.Column(side_bar,vertical_alignment='top',scrollable=True,expand_x=True,expand_y=True),
            sg.Column(canvas,vertical_alignment='top',scrollable=True,expand_x=True,expand_y=True,key='canvas_body'),
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