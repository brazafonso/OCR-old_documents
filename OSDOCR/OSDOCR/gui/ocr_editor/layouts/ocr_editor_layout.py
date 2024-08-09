import os
import PySimpleGUI as sg
from ...aux_utils.utils import place
from OSDOCR.aux_utils import consts


# consts
browse_img_input_value = '/home/braz/projetos/OCR-old_documents/study_cases/simple template/2-1.jpg'
browse_file_input_value = '/home/braz/projetos/OCR-old_documents/results/2-1______88a3d1a9c2e7707cb70e8f9afa569005/processed/clean_ocr.json'

def ocr_editor_layout()->sg.Window:
    '''Build window for ocr results editor'''

    window_size = (1200,800)
    window_location = (500,100)
    
    # target image and ocr results selector
    upper_row = [
        [
                place(sg.FileBrowse(file_types=(("IMG Files", "*.*"),),button_text="Choose Image",key='browse_image',target='target_input',initial_folder=os.getcwd())),
                place(sg.Input(default_text=browse_img_input_value,key='target_input',enable_events=True)),

                place(sg.FileBrowse(file_types=(("OCR Files", ["*.json","*.hocr"]),),button_text="Choose OCR Results",key='browse_file',target='ocr_results_input',initial_folder=os.getcwd())),
                place(sg.Input(default_text=browse_file_input_value,key='ocr_results_input',enable_events=True)),

                place(sg.Button('Config',key='configurations_button')),
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
        [
            place(sg.Button('Categorize blocks',key='method_categorize_blocks')),
        ],
        [
            place(sg.Button('Find Titles',key='method_find_titles')),
        ],
        [
            place(sg.Button('Find Articles',key='method_find_articles')),
        ],
        [
            place(sg.Button('Refresh block id',key='method_refresh_block_id')),
        ]
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
            place(sg.Button('Generate MD',key='generate_md')),
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


    article_info = [
        [
            place(sg.Checkbox(text='Toogle Articles: ',key='checkbox_toggle_articles',enable_events=True)),
        ],
        [
            place(sg.Table(values=[],headings=['Articles: '],auto_size_columns=False,def_col_width=10,key='table_articles',expand_x=True,expand_y=True,enable_events=True,enable_click_events=True,visible=True,select_mode=sg.TABLE_SELECT_MODE_BROWSE)),
            sg.Column(
              [
                  [
                      sg.Button('↑',key='button_move_article_up'),
                  ],
                  [
                      sg.Button('↓',key='button_move_article_down'),
                  ],
              ]  
            ),
            sg.Column(
                [
                    [
                        sg.Button('Add Article',key='button_add_article'),
                    ],
                    [
                        sg.Button('Update Article',key='button_update_article'),
                    ],
                    [
                        sg.Button('Delete Article',key='button_delete_article'),
                    ],
                ]
            ),
        ],
    ]


    # side bar for info about ocr results
    right_side_bar = [
        [
            sg.Frame('',block_type_legend)
        ],
        [
            sg.Frame('',block_info,key='frame_block_info')
        ],
        [
            sg.Frame('',article_info,key='frame_article_info')
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
    editor_main = [
        [
            upper_row,
            body
        ]
    ]

    window = sg.Window('OCR Editor',editor_main,finalize=True,resizable=True,size=window_size,relative_location=window_location)
    window.bind('<Configure>',"Event")
    return window



def configurations_layout()->sg.Window:
    '''Window for configurations'''

    # normal configurations
    ## text confidence (input)
    ## type of document (select : newspaper, other)
    ## ignore delimiters (checkbox)
    ## calculate reading order (checkbox)
    ## target segments (header, body, footer - checkbox)
    ## output type (select : newspaper, simple)
    ## use pipeline results (checkbox)
    ## output path (folder)
    
    simple_options = [
        [
            place(sg.Text('Text Confidence: ')),
            place(sg.Slider(range=(0,100),default_value=70,key='slider_text_confidence',orientation='h',enable_events=True))
        ],
        [
            place(sg.Text('Type of Document: ')),
            place(sg.Combo(['newspaper','other'],default_value='newspaper',key='list_type_of_document',enable_events=True))
        ],
        [
            place(sg.Checkbox(text='Ignore Delimiters: ',key='checkbox_ignore_delimiters',enable_events=True))
        ],
        [
            place(sg.Checkbox(text='Calculate Reading Order: ',key='checkbox_calculate_reading_order',enable_events=True))
        ],
        [
            place(sg.Text(text='Target Segments: ')),
            place(sg.Checkbox(text='Header',key='checkbox_target_header',enable_events=True)),
            place(sg.Checkbox(text='Body',key='checkbox_target_body',enable_events=True)),
            place(sg.Checkbox(text='Footer',key='checkbox_target_footer',enable_events=True))
        ],
        [
            place(sg.Text('Output Type: ')),
            place(sg.Combo(['newspaper','simple'],default_value='newspaper',key='list_output_type',enable_events=True))
        ],
        [
            place(sg.Checkbox(text='Use Pipeline Results: ',key='checkbox_use_pipeline_results',enable_events=True))
        ],
        [
            place(sg.FolderBrowse('Output Path: ',target='input_output_path',enable_events=True)),
            place(sg.Input(default_text=os.getcwd(),key='input_output_path',enable_events=True))
        ],
    ]

    simple_options_frame = [
        [
            place(sg.Frame('Basic Options',simple_options))
        ]
    ]

    # OCR pipeline configurations
    ## preprocessing
    ### fix rotation (select : auto,clockwise,counter-clockwise, none)
    ### upscaling_image (select : none, waifu2x)
    ### denoise_image (select : none, waifu2x)
    ### fix_illumination (checkbox)
    ### binarize (select : none, fax, otsu)
    ## tesseract options
    ### dpi (input)
    ### psm (input)
    ### l (select : eng, por)

    pipeline_preprocessing_options = [
        [
            place(sg.Text('Fix Rotation: ')),
            place(sg.Combo(['none','auto','clockwise','counter-clockwise'],default_value='none',key='list_fix_rotation',enable_events=True))
        ],
        [
            place(sg.Text('Upscaling Image: ')),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_upscaling_image',enable_events=True))
        ],
        [
            place(sg.Text('Denoise Image: ')),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_denoise_image',enable_events=True))
        ],
        [
            place(sg.Checkbox(text='Fix Illumination: ',key='checkbox_fix_illumination',enable_events=True))
        ],
        [
            place(sg.Text('Binarize: ')),
            place(sg.Combo(['none','fax','otsu'],default_value='none',key='list_binarize',enable_events=True))
        ]
    ]

    pipeline_tesseract_options = [
        [
            place(sg.Text('DPI: ')),
            place(sg.InputText(key='tesseract_input_dpi',enable_events=True))
        ],
        [
            place(sg.Text('PSM: ')),
            place(sg.InputText(key='tesseract_input_psm',enable_events=True))
        ],
        [
            place(sg.Text('Language: ')),
            place(sg.Combo(['eng','por'],default_value='eng',key='tesseract_list_lang',enable_events=True))
        ]
    ]

    pipeline_options = [
        [
            place(sg.Frame('Preprocessing',pipeline_preprocessing_options))
        ],
        [
            place(sg.Frame('Tesseract',pipeline_tesseract_options))
        ]
    ]

    pipeline_options_frame = [
        [
            place(sg.Frame('OCR Pipeline',pipeline_options))
        ]
    ]

    # article configurations
    ## article gathering (select : selected, fill)

    article_options = [
        [
            place(sg.Text('Article Gathering: ')),
            place(sg.Combo(['selected','fill'],default_value='selected',key='list_article_gathering',enable_events=True))
        ]
    ]

    article_options_frame = [
        [
            place(sg.Frame('Article Configuration',article_options))
        ]
    ]


    # final layout
    layout = [
        [
            simple_options_frame,
        ],
        [
            pipeline_options_frame,
        ],
        [
            article_options_frame,
        ],
        [
            place(sg.Button('Save',key='button_save')),
            place(sg.Button('Reset',key='button_reset')),
            place(sg.Button('Cancel',key='button_cancel')),
        ]
    ]

    window = sg.Window('OCR Editor - Configuration', layout,finalize=True,resizable=True,keep_on_top=True,force_toplevel=True)
    window.bind('<Configure>',"Event")
    return window
    