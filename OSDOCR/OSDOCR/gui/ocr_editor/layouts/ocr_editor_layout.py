import os
import PySimpleGUI as sg
from ...aux_utils.utils import place,collapse
from OSDOCR.aux_utils import consts

file_path = os.path.dirname(os.path.realpath(__file__))



# consts
gui_theme = 'SandyBeach'
SYMBOL_UP =    '▲'
SYMBOL_DOWN =  '▼'
browse_img_input_value = '/home/braz/projetos/OCR-old_documents/study_cases/simple template/2-1.jpg'
browse_file_input_value = '/home/braz/projetos/OCR-old_documents/results/2-1______88a3d1a9c2e7707cb70e8f9afa569005/processed/clean_ocr.json'

def ocr_editor_layout()->sg.Window:
    '''Build window for ocr results editor'''
    sg.theme(gui_theme)

    window_size = (1200,800)
    window_location = (500,0)
    
    # target image and ocr results selector
    upper_row = [
        [
                sg.Push(),
                place(sg.FileBrowse(file_types=(("IMG Files", "*.*"),),button_text="Image",
                                    key='browse_image',target='target_input',initial_folder=os.getcwd(),
                                    font=("Calibri", 15))),
                place(sg.Input(default_text=browse_img_input_value,key='target_input',
                               enable_events=True,font=("Calibri", 15),size=(25,1))),

                place(sg.FileBrowse(file_types=(("OCR Files", ["*.json","*.hocr"]),),
                                    button_text="OCR Results",key='browse_file',target='ocr_results_input',
                                    initial_folder=os.getcwd(),font=("Calibri", 15))),
                place(sg.Input(default_text=browse_file_input_value,key='ocr_results_input',
                               enable_events=True,font=("Calibri", 15),size=(25,1))),

                sg.Push(),
                place(sg.Image(source=f'{file_path}/../assets/settings.png',
                               key='configurations_button',enable_events=True,
                               tooltip='Settings',
                               )
                    )
        ],
        [
            sg.HorizontalSeparator()
        ]
    ]

    # side bar for methods (palceholder)
    left_side_bar = [
        [
            place(sg.Image(source=f'{file_path}/../assets/new_block.png',
                           key='method_new_block',enable_events=True,
                           tooltip='Create new block')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/join_blocks.png',
                           key='method_join',enable_events=True,
                           tooltip='Join Blocks')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/split_blocks.png',
                           key='method_split',enable_events=True,
                           tooltip='Split Blocks')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/split_whitespaces.png',
                           key='method_split_whitespaces',enable_events=True,
                           tooltip='Split Whitespaces')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/split_image.png',
                           key='method_split_image',enable_events=True,
                           tooltip='Split Image')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/fix_intersections.png',
                           key='method_fix_intersections',enable_events=True,
                           tooltip='Fix intersections')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/remove_empty_blocks.png',
                           key='method_remove_empty_blocks',enable_events=True,
                           tooltip='Remove empty blocks')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/adjust_bb.png',
                           key='method_adjust_bounding_boxes',enable_events=True,
                           tooltip='Adjust bounding boxes')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/calculate_reading_order.png',
                           key='method_calculate_reading_order',enable_events=True,
                           tooltip='Calculate reading order')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/categorize_blocks.png',
                           key='method_categorize_blocks',enable_events=True,
                           tooltip='Categorize blocks')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/unite_blocks.png',
                           key='method_unite_blocks',enable_events=True,
                           tooltip='Unite Blocks method')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/find_titles.png',
                           key='method_find_titles',enable_events=True,
                           tooltip='Find Titles')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/find_articles.png',
                           key='method_find_articles',enable_events=True,
                           tooltip='Find Articles')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/refresh_block_id.png',
                           key='method_refresh_block_id',enable_events=True,tooltip='Refresh block id')),
        ],
        [
            place(sg.Button('Test',key='method_test',font=("Calibri", 15))),
        ]
    ]


    # canvas (editor)
    canvas_top = [
            place(sg.Button('Save as copy',key='save_ocr_results_copy',font=("Calibri", 15))),
            place(sg.Image(source=f'{file_path}/../assets/save.png'
                           ,key='save_ocr_results',enable_events=True,
                           tooltip='Save')),

            place(sg.Image(source=f'{file_path}/../assets/reset.png',
                           key='reset_ocr_results',enable_events=True,
                           tooltip='Reset')),

            place(sg.Image(source=f'{file_path}/../assets/undo.png',
                           key='undo_ocr_results',enable_events=True,
                           tooltip='Undo')),

            place(sg.Image(source=f'{file_path}/../assets/redo.png',
                           key='redo_ocr_results',enable_events=True,
                           tooltip='Redo')),

            place(sg.Image(source=f'{file_path}/../assets/zoom_in.png',
                           key='zoom_in',enable_events=True,
                           tooltip='Zoom In')),

            place(sg.Image(source=f'{file_path}/../assets/zoom_out.png',
                           key='zoom_out',enable_events=True,
                           tooltip='Zoom Out')),

            place(sg.Button('Generate MD',key='generate_md',font=("Calibri", 15))),

            place(sg.Image(source=f'{file_path}/../assets/send_block_back.png',
                           key='send_block_back',enable_events=True,
                           tooltip='Send block back')),

            place(sg.Image(source=f'{file_path}/../assets/send_block_front.png',
                           key='send_block_front',enable_events=True,
                           tooltip='Send block front')),

            place(sg.Image(source=f'{file_path}/../assets/reset_block_height.png',
                           key='reset_blocks_height',enable_events=True,
                           tooltip='Reset blocks height')),
        ]
    
    canvas_body = [
            [
                place(
                sg.Frame('',layout=[
                        [
                            sg.Canvas(key='canvas',size=(600,800),expand_x=True,expand_y=True)
                        ]
                    ],
                    # relief=sg.RELIEF_SUNKEN,
                    # border_width=0.1,
                    # background_color='#046380',
                    )
                )
            ]
        ]
    

    block_type_legend = [
        [
            place(sg.Text('Toogle Block Type: ', font=('Calibri', 15))),
            place(sg.Checkbox(text='', key='checkbox_toggle_block_type', enable_events=True)),
        ],
        [
            place(sg.Text('Box Type: ', font=('Calibri', 15))),
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_title_text', font=('Calibri', 13))),
            place(sg.Text('Title', enable_events=True, key='box_type_title_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='red', background_color='red', enable_events=True, key='box_type_title_text')),
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_text_text', font=('Calibri', 13))),
            place(sg.Text('Text', enable_events=True, key='box_type_text_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='yellow', background_color='yellow', enable_events=True, key='box_type_text_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_image_text', font=('Calibri', 13))),
            place(sg.Text('Image', enable_events=True, key='box_type_image_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='black', background_color='black', enable_events=True, key='box_type_image_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_highlight_text', font=('Calibri', 13))),
            place(sg.Text('Highlight', enable_events=True, key='box_type_highlight_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='purple', background_color='purple', enable_events=True, key='box_type_highlight_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_caption_text', font=('Calibri', 13))),
            place(sg.Text('Caption', enable_events=True, key='box_type_caption_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='white', background_color='white', enable_events=True, key='box_type_caption_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_delimiter_text', font=('Calibri', 13))),
            place(sg.Text('Delimiter', enable_events=True, key='box_type_delimiter_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='blue', background_color='blue', enable_events=True, key='box_type_delimiter_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_other_text', font=('Calibri', 13))),
            place(sg.Text('Other', enable_events=True, key='box_type_other_text', font=('Calibri', 13))),
        sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='green', background_color='green', enable_events=True, key='box_type_other_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_all_text', font=('Calibri', 13))),
            place(sg.Text('ALL', enable_events=True, key='box_type_all_text', font=('Calibri', 13))),
            # No color square here, so no need for sg.Push()
        ],
        [
            place(sg.Text('* ', font=('Calibri', 13))),
            place(sg.Text('DEFAULT COLOR', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='black', background_color='black', key='text_default_color'))
        ],
    ]

    block_info = [
        [
            place(sg.Text('Block ', font=('Calibri', 13))),
            place(sg.Input('',key='input_block_id',size=(3,1), font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Coordinates:', font=('Calibri', 13))),
            place(sg.Text('',key='text_block_coords', font=('Calibri', 10))),
        ],
        [
            place(sg.Text('Height:', font=('Calibri', 13))),
            place(sg.Text('',key='text_block_height', font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Width:', font=('Calibri', 13))),
            place(sg.Text('',key='text_block_width', font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Z:', font=('Calibri', 13))),
            place(sg.Text('',key='text_block_level', font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Type: ', font=('Calibri', 13))),
            place(sg.Combo(['title','text','image','highlight','caption','delimiter','other',''],
                           default_value='',key='list_block_type',enable_events=True, font=('Calibri', 13),
                           readonly=True)),
            place(sg.Button('░░',key='button_type_apply_all', font=('Calibri', 13),tooltip='Apply to all blocks')),
        ],
        [
            place(sg.Text('Text: ', font=('Calibri', 13)))
        ],
        [
            place(sg.Multiline(default_text='',key='input_block_text',enable_events=True,
                               size=(32,10),auto_size_text=True,autoscroll=True, font=('Calibri', 11)))
        ],
        [
            place(sg.Button('OCR',key='button_ocr_block', font=('Calibri', 13))),
            place(sg.Image(source=f'{file_path}/../assets/copy.png'
                           ,key='button_copy_block_text',enable_events=True,
                           tooltip='Copy')),
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/save.png'
                           ,key='button_save_block',enable_events=True,
                           tooltip='Save')),
            place(sg.Image(source=f'{file_path}/../assets/delete_bin.png'
                           ,key='button_delete_block',enable_events=True,
                           tooltip='Delete')),
        ],
    ]


    article_info = [
        [
            place(sg.Text('Toogle Articles: ', font=('Calibri', 15))),
            place(sg.Checkbox(text='', key='checkbox_toggle_articles', enable_events=True)),
        ],
        [
            place(sg.Table(values=[],headings=['Articles: '],auto_size_columns=False,def_col_width=10,
                           key='table_articles',expand_x=True,expand_y=True,enable_events=True,
                           enable_click_events=True,visible=True,select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                           font=('Calibri', 13))),
            sg.Column(
              [
                  [
                      sg.Text('↑',font=("Calibri", 30),text_color='#046380',enable_events=True,key='button_move_article_up'),
                  ],
                  [
                      sg.Text('↓',font=("Calibri", 30),text_color='#046380',enable_events=True,key='button_move_article_down'),
                  ],
              ]  
            ),
            sg.Column(
                [
                    [
                        place(sg.Image(source=f'{file_path}/../assets/add.png'
                           ,key='button_add_article',enable_events=True,
                           tooltip='Add Article')),
                    ],
                    [
                        
                        place(sg.Image(source=f'{file_path}/../assets/save.png'
                           ,key='button_update_article',enable_events=True,
                           tooltip='Update Article')),
                    ],
                    [
                        place(sg.Image(source=f'{file_path}/../assets/delete_bin.png'
                           ,key='button_delete_article',enable_events=True,
                           tooltip='Delete Article')),
                    ],
                ]
            ),
        ],
    ]


    # side bar for info about ocr results
    right_side_bar = [
        [
                sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN collapse_block_type_legend-',
                     font=("Calibri", 20,"bold"),text_color='#046380'), 
                sg.T('Block Filter', enable_events=True, k='-OPEN collapse_block_type_legend-TEXT',
                     font=("Calibri", 20,"bold"),text_color='#046380'),
        ],
        [
            sg.HorizontalSeparator(),
        ],
        [
            collapse([[sg.Frame('',block_type_legend)]],key='collapse_block_type_legend')
        ],
        [
            sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN collapse_block_info-',
                 font=("Calibri", 20,"bold"),text_color='#046380'), 
            sg.T('Block Info', enable_events=True, k='-OPEN collapse_block_info-TEXT',
                 font=("Calibri", 20,"bold"),text_color='#046380')
        ],
        [
            sg.HorizontalSeparator(),
        ],
        [
            collapse([[sg.Frame('',block_info,key='frame_block_info')]],key='collapse_block_info')
        ],
        [
            sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN collapse_article_info-',
                 font=("Calibri", 20,"bold"),text_color='#046380'), 
            sg.T('Article Info', enable_events=True, k='-OPEN collapse_article_info-TEXT',
                 font=("Calibri", 20,"bold"),text_color='#046380')
        ],
        [
            sg.HorizontalSeparator(),
        ],
        [
            collapse([[sg.Frame('',article_info,key='frame_article_info')]],key='collapse_article_info')
        ]
    ]


    

    ratio_1 = 1/10
    ratio_2 = 6/10
    ratio_3 = 3/10

    column_1_size = (window_size[0]*ratio_1,None)
    column_2_size = (window_size[0]*ratio_2,None)
    column_3_size = (window_size[0]*ratio_3,None)


    context_menu = [
        '',
        [
            'Send to front::context_menu_send_to_front',
            'Send to back::context_menu_send_to_back',
        ]
    ]

    canvas = [
        canvas_top,
        [
            sg.Column(canvas_body,scrollable=True,
                      expand_x=True,expand_y=True,right_click_menu=context_menu,
                      size=column_2_size,key='body_canvas')
        ],
    ]


    # body, composed of side bar and canvas
    body = [
        [
            [
                sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN collapse_body_left_side_bar-',
                     font=("Calibri", 24,"bold"),text_color='#046380'), 
                sg.T('Tools', enable_events=True, k='-OPEN collapse_body_left_side_bar-TEXT',
                     font=("Calibri", 24,"bold"),text_color='#046380')
            ],
            collapse([[
                sg.Column(left_side_bar,vertical_alignment='top',scrollable=True,
                        vertical_scroll_only=True,expand_x=True,expand_y=True,
                        size=column_1_size,key='body_left_side_bar')]]
                ,key='collapse_body_left_side_bar'),

            sg.VerticalSeparator(),

            sg.Column(canvas,vertical_alignment='top',expand_x=True,expand_y=True),

            sg.VerticalSeparator(),

            sg.Column(right_side_bar,vertical_alignment='top',scrollable=True,
                      vertical_scroll_only=True,expand_x=True,expand_y=True,
                      size=column_3_size,key='body_right_side_bar'),
        ]
    ]

    # main layout
    editor_main = [
        [
            upper_row,
            body
        ]
    ]

    window = sg.Window('OCR Editor',editor_main,finalize=True,
                       resizable=True,size=window_size,
                       relative_location=window_location,
                       )
    window.bind('<Configure>',"Event")
    return window










def configurations_layout(position:tuple=(None,None))->sg.Window:
    '''Window for configurations'''

    sg.theme(gui_theme)

    # normal configurations
    ## text confidence (input)
    ## output type (select : newspaper, simple)
    ## use pipeline results (checkbox)
    ## output path (folder)
    ## cache size (input)
    ## default ppi (input)
    
    simple_options = [
        [
            place(sg.Text('Text Confidence: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Slider(range=(0,100),default_value=70,key='slider_text_confidence'
                            ,orientation='h',enable_events=True,size=(15,13)))
        ],
        [
            place(sg.Text('Output Type: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['newspaper','simple'],default_value='newspaper',key='list_output_type',enable_events=True))
        ],
        [
            place(sg.Text('Use Pipeline Results: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox('',key='checkbox_use_pipeline_results',enable_events=True))
        ],
        [
            place(sg.FolderBrowse('Output Path: ',target='input_output_path',enable_events=True,
                                  font=("Calibri", 12,"bold"))),
            place(sg.Input(default_text=os.getcwd(),key='input_output_path',enable_events=True))
        ],
        [
            place(sg.Text('Operations Cache Size: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Input(10,key='input_operations_cache_size',size=(5,1), enable_events=True))
        ],
        [
            place(sg.Text('Debug mode: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox('',key='checkbox_debug_mode',enable_events=True))
        ],
        [
            place(sg.Text('Default PPI (zoom): ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Input(300,key='input_default_ppi',size=(5,1), enable_events=True))
        ],
        [
            place(sg.Text('Vertex radius: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Input(5,key='input_vertex_radius',size=(5,1), enable_events=True))
        ],
        [
            place(sg.Text('Edge thickness: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Input(2,key='input_edge_thickness',size=(5,1), enable_events=True))
        ],
        [
            place(sg.Text('Id Text size: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Input(10,key='input_id_text_size',size=(5,1), enable_events=True))
        ],

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
            place(sg.Text('Fix Rotation: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['none','auto','clockwise','counter-clockwise'],default_value='none',
                           key='list_fix_rotation',enable_events=True,size=(10,13)))
        ],
        [
            place(sg.Text('Upscaling Image: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_upscaling_image',
                           enable_events=True))
        ],
        [
            place(sg.Text('Denoise Image: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_denoise_image',
                           enable_events=True))
        ],
        [
            place(sg.Text('Fix Illumination: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox(text='',key='checkbox_fix_illumination',
                              enable_events=True))
        ],
        [
            place(sg.Text('Binarize: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['none','fax','otsu'],default_value='none',key='list_binarize',
                           enable_events=True))
        ]
    ]

    pipeline_tesseract_options = [
        [
            place(sg.Text('DPI: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.InputText(key='tesseract_input_dpi',enable_events=True,size=(5,1)))
        ],
        [
            place(sg.Text('PSM: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.InputText(key='tesseract_input_psm',enable_events=True,size=(5,1)))
        ],
        [
            place(sg.Text('Language: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['eng','por'],default_value='eng',key='tesseract_list_lang',
                           enable_events=True,size=(5,1)))
        ]
    ]

    pipeline_options = [
        [
            sg.Text('Preprocessing Options',font=("Calibri", 14,"bold"),text_color='#046380')
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Column(pipeline_preprocessing_options)
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Text('Tesseract Options',font=("Calibri", 14,"bold"),text_color='#046380')
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Column(pipeline_tesseract_options)
        ],
    ]


    # methods configurations
    ## type of document (select : newspaper, other)
    ## ignore delimiters (checkbox)
    ## calculate reading order (checkbox)
    ## target segments (header, body, footer - checkbox)
    ## image split, keep intersecting boxes (checkbox)
    ## article gathering (select : selected, fill)

    methods_options = [
        [
            place(sg.Text('Type of Document: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['newspaper','other'],default_value='newspaper',
                           key='list_type_of_document',enable_events=True))
        ],
        [
            place(sg.Text('Ignore Delimiters: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox(text='',key='checkbox_ignore_delimiters',enable_events=True))
        ],
        [
            place(sg.Text('Calculate Reading Order: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox(text='',key='checkbox_calculate_reading_order',enable_events=True))
        ],
        [
            place(sg.Text(text='Target Segments: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox(text='Header',key='checkbox_target_header',enable_events=True)),
            place(sg.Checkbox(text='Body',key='checkbox_target_body',enable_events=True)),
            place(sg.Checkbox(text='Footer',key='checkbox_target_footer',enable_events=True))
        ],
        [
            place(sg.Text('Image Split [Keep Intersecting Boxes]: ',font=("Calibri", 12,"bold"),
                          text_color='#046380')),
            place(sg.Checkbox(text='',key='checkbox_image_split_keep_intersecting_boxes',enable_events=True))
        ],
        [
            place(sg.Text('Article Gathering: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Combo(['selected','fill'],default_value='selected',key='list_article_gathering',
                           enable_events=True))
        ]
    ]


    simple_optios_tab = sg.Tab('Editor',simple_options)
    methods_options_tab = sg.Tab('Methods',methods_options)
    pipeline_options_tab = sg.Tab('Pipeline',pipeline_options)

    # final layout
    layout = [
        [
            place(sg.TabGroup([[simple_optios_tab,methods_options_tab,pipeline_options_tab]],
                              font=("Calibri", 15,'bold'),title_color='#046380'))
        ],
        [
            place(sg.Image(source=f'{file_path}/../assets/save.png'
                           ,key='button_save',enable_events=True,
                           tooltip='Save')),
            place(sg.Image(source=f'{file_path}/../assets/reset.png',
                           key='button_reset',enable_events=True,
                           tooltip='Reset')),
            place(sg.Button('Cancel',key='button_cancel')),
        ]
    ]

    location = position if position is not None else (0,0)
    window = sg.Window('OCR Editor - Configuration', layout,
                       finalize=True,resizable=True,keep_on_top=True,
                       force_toplevel=True,location=location
                       )
    window.bind('<Configure>',"Event")
    return window


def popup_window(title:str='',message:str='',options:list=[],location:tuple=(None,None),modal:bool=True):
    '''Popup window'''
    sg.theme(gui_theme)
    layout = [
        [
            place(sg.Text(message))
        ],
        [
        ]
    ]
    for option in options:
        layout[1].append(place(sg.Button(option,key=option)))

    window = sg.Window(title,layout,finalize=True,resizable=True,location=location,keep_on_top=True,force_toplevel=True,modal=modal)
    window.bind('<Configure>',"Event")

    option = None
    while True:
        event, _ = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in options:
            option = event
            break

    window.close()
    return option
    