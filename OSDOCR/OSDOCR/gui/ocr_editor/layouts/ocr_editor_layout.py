import os
import PySimpleGUI as sg
from ...aux_utils.utils import place,collapse
from OSDOCR.aux_utils import consts

file_path = os.path.dirname(os.path.realpath(__file__))



# consts
gui_theme = 'SandyBeach'
SYMBOL_UP =    '▲'
SYMBOL_DOWN =  '▼'
browse_img_input_value = ''
browse_file_input_value = ''
checked = b'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'
unchecked = b'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'
    
    
def ocr_editor_layout()->sg.Window:
    '''Build window for ocr results editor'''
    sg.theme(gui_theme)

    window_size = (1200,800)
    window_location = (500,0)
    
    # target image and ocr results selector
    upper_row = [
        [
                sg.Push(),
                place(sg.FileBrowse(file_types=(("IMG Files", ["*.png","*.jpg","*.jpeg","*.bmp","*.tiff"]),),
                                    button_text="Image",
                                    key='browse_image',target='target_input',initial_folder=os.getcwd(),
                                    font=("Calibri", 15),enable_events=True)),
                place(sg.Input(default_text=browse_img_input_value,key='target_input',
                               enable_events=True,font=("Calibri", 15),size=(25,1))),

                place(sg.FileBrowse(file_types=(("OCR Files", ["*.json","*.hocr"]),),
                                    button_text="OCR Results",key='browse_file',target='ocr_results_input',
                                    initial_folder=os.getcwd(),font=("Calibri", 15),enable_events=True)),
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
            place(sg.Button('Test',key='method_test',font=("Calibri", 15),visible=False)),
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

            place(sg.Image(source=f'{file_path}/../assets/send_block_back.png',
                           key='send_block_back',enable_events=True,
                           tooltip='Send block back')),

            place(sg.Image(source=f'{file_path}/../assets/send_block_front.png',
                           key='send_block_front',enable_events=True,
                           tooltip='Send block front')),

            place(sg.Image(source=f'{file_path}/../assets/reset_block_height.png',
                           key='reset_blocks_height',enable_events=True,
                           tooltip='Reset blocks height')),

            place(sg.Button('Output',key='generate_output',font=("Calibri", 15))),
        ]
    
    canvas_body = [
            [
                place(
                sg.Frame('',layout=[
                        [
                            sg.Canvas(key='canvas',size=(1,1),expand_x=True,expand_y=True)
                        ],
                    ],key='canvas_frame',
                    element_justification='center',
                    pad=(0,0),
                    border_width=0,
                    expand_x=True,
                    expand_y=True
                    )
                )
            ]
        ]



    block_type_filter = [
        [
            place(sg.Text('Toogle Block Type: ', font=('Calibri', 15))),
            place(sg.Checkbox(text='', key='checkbox_toggle_block_type', enable_events=True)),
        ],
        [
            place(sg.Text('Box Type: ', font=('Calibri', 15))),
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_title_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Title', enable_events=True, key='box_type_title_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='red', background_color='red', enable_events=True, key='box_type_title_text')),
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_text_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Text', enable_events=True, key='box_type_text_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='yellow', background_color='yellow', enable_events=True, key='box_type_text_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_image_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Image', enable_events=True, key='box_type_image_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='black', background_color='black', enable_events=True, key='box_type_image_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_highlight_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Highlight', enable_events=True, key='box_type_highlight_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='purple', background_color='purple', enable_events=True, key='box_type_highlight_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_caption_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Caption', enable_events=True, key='box_type_caption_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='white', background_color='white', enable_events=True, key='box_type_caption_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_delimiter_text_main', font=('Calibri', 13),metadata=True)),
            place(sg.Text('Delimiter', enable_events=True, key='box_type_delimiter_text', font=('Calibri', 13))),
            sg.Push(),  # Pushes the color square to the right
            place(sg.Text('', size=(2, 1), text_color='blue', background_color='blue', enable_events=True, key='box_type_delimiter_text'))
        ],
        [
            place(sg.Text('* ', enable_events=True, key='box_type_other_text_main', font=('Calibri', 13),metadata=True)),
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

    frame_block_type_filter = [
        place(sg.Frame('Block Type Filter', block_type_filter))
    ]

    block_misc_filter = [
        [
            place(sg.Text('ID: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Input('',key='block_misc_filter_id',size=(6,1), font=('Calibri', 13))),
        ],
        [

            place(sg.Text('TEXT: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Text('REGEX: ', font=('Calibri', 11))),
            place(sg.Checkbox(text='', key='checkbox_block_misc_filter_regex', enable_events=True)),
        ],
        [
            place(sg.Multiline(default_text='',key='block_misc_filter_text',enable_events=True,
                               size=(20,2),auto_size_text=True,autoscroll=True, font=('Calibri', 11)))
        ],
        [
            place(sg.Text('LEFT: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Input('',key='block_misc_filter_left',size=(6,1), font=('Calibri', 13))),
        ],
        [
            place(sg.Text('TOP: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Input('',key='block_misc_filter_top',size=(6,1), font=('Calibri', 13))),
        ],
        [
            place(sg.Text('RIGHT: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Input('',key='block_misc_filter_right',size=(6,1), font=('Calibri', 13))),
        ],
        [
            place(sg.Text('BOTTOM: ', font=('Calibri', 13))),
            sg.Push(),
            place(sg.Input('',key='block_misc_filter_bottom',size=(6,1), font=('Calibri', 13))),
        ],
        [
            sg.Push(),
            place(sg.Button('APPLY',key='button_block_misc_filter_apply', font=('Calibri', 10))),
            sg.Push(),
            place(sg.Button('CLEAR',key='button_block_misc_filter_clear', font=('Calibri', 10))),
            sg.Push(),
            place(sg.Button('RESET',key='button_block_misc_filter_reset', font=('Calibri', 10))),
        ]
    ]

    frame_block_misc_filter = [
        place(sg.Frame('Block Misc Filter', block_misc_filter))
    ]

    block_filters = [
        frame_block_type_filter,
        frame_block_misc_filter
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
            place(sg.Text('Mean height:', font=('Calibri', 13))),
            place(sg.Text('',key='text_mean_height', font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Mean Char width:', font=('Calibri', 13))),
            place(sg.Text('',key='text_mean_char_width', font=('Calibri', 13))),
        ],
        [
            place(sg.Text('Avg. Conf:', font=('Calibri', 13))),
            place(sg.Text('',key='text_avg_conf', font=('Calibri', 13))),
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
            place(sg.Table(values=[],headings=['Articles'],auto_size_columns=False,def_col_width=7,
                           key='table_articles',expand_x=True,expand_y=True,enable_events=True,
                           enable_click_events=True,visible=True,select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                           font=('Calibri', 15, 'bold'),header_font=('Calibri', 16, 'bold'),
                           justification='center',num_rows=5)),
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
        [
            place(sg.Text('')),
            sg.Push(),
            place(sg.Text('Article Color', font=('Calibri', 16,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Text('')),
        ],
        [
            place(sg.Text('', size=(50, 1),  key='article_color'))
        ],
        [
            place(sg.Text('R:', font=('Calibri', 13),text_color='red')),
            place(sg.Input('', key='article_color_r', size=(3, 1), font=('Calibri', 13))),
            place(sg.Text('G:', font=('Calibri', 13),text_color='green')),
            place(sg.Input('', key='article_color_g', size=(3, 1), font=('Calibri', 13))),
            place(sg.Text('B:', font=('Calibri', 13),text_color='blue')),
            place(sg.Input('', key='article_color_b', size=(3, 1), font=('Calibri', 13))),
            place(sg.Text('✔', key='article_color_apply', font=('Calibri', 15),enable_events=True)),
        ]
    ]


    # side bar for info about ocr results
    right_side_bar = [
        [
                sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN collapse_block_filter-',
                     font=("Calibri", 20,"bold"),text_color='#046380'), 
                sg.T('Block Filter', enable_events=True, k='-OPEN collapse_block_filter-TEXT',
                     font=("Calibri", 20,"bold"),text_color='#046380'),
        ],
        [
            sg.HorizontalSeparator(),
        ],
        [
            collapse([[sg.Frame('',block_filters)]],key='collapse_block_filter')
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


    

    ratio_1 = 1/12
    ratio_2 = 7/12
    ratio_3 = 4/12

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
            place(sg.Text('BLOCK LEVEL:', font=('Calibri', 15,"bold"))),
            place(sg.Combo(['page','block','par','line','word'],
                           default_value='block',key='list_block_level',enable_events=True, font=('Calibri', 13),
                           readonly=True,auto_size_text=True)),
            place(sg.Text('⟲',key='button_block_level_refresh', font=('Calibri', 25,"bold"),text_color='#046380',
                         enable_events=True)),
            place(sg.Text('Toggle ID:', font=('Calibri', 15,"bold"))),
            place(sg.Checkbox('',key='checkbox_toggle_block_id',enable_events=True, font=('Calibri', 13),
                              default=True)),
            sg.Push(),
            place(sg.Button('SELECT ALL',key='button_select_all', font=('Calibri', 10,"bold"),enable_events=True)),
        ],
        [
            sg.Column(canvas_body,scrollable=True,
                      expand_x=True,expand_y=True,right_click_menu=context_menu,
                      size=column_2_size,key='body_canvas',
                      pad=(0,0)),
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
                       grab_anywhere_using_control=False
                       )
    window.bind('<Configure>',"Event")
    window['body_canvas'].expand(True,True,True)
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
            place(sg.Text('Text Confidence: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Slider(range=(0,100),default_value=70,key='slider_text_confidence'
                            ,orientation='h',enable_events=True,size=(40,20)))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Output Format: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['markdown','txt'],default_value='markdown',key='list_output_format',
                           enable_events=True,font=("Calibri", 18,"bold"),readonly=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Output Type: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['newspaper','simple'],default_value='newspaper',key='list_output_type',
                           enable_events=True,font=("Calibri", 18,"bold"),readonly=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.FolderBrowse('Output Path: ',target='input_output_path',enable_events=True,
                                  font=("Calibri", 18,"bold"))),
            sg.Push(),
            place(sg.Input(default_text=os.getcwd(),key='input_output_path',enable_events=True,
                           size=(20,1),font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Fix hifenization [output]: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_fix_hifenization',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Calculate Reading Order [Output]: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_calculate_reading_order',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Use Pipeline Results: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(unchecked,key='-CHECKBOX-checkbox_use_pipeline_results',metadata=False,enable_events=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Operations Cache Size: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input(10,key='input_operations_cache_size',size=(5,3), enable_events=True,
                           font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Debug mode: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(unchecked,key='-CHECKBOX-checkbox_debug_mode',enable_events=True,metadata=False))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Default PPI (zoom): ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input(300,key='input_default_ppi',size=(5,3), enable_events=True,font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Vertex radius: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input(5,key='input_vertex_radius',size=(5,3), enable_events=True,font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Edge thickness: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input(2,key='input_edge_thickness',size=(5,3), enable_events=True,font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Edge color: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input('',key='input_edge_color',size=(5,3), enable_events=True,font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Id Text size: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Input(10,key='input_id_text_size',size=(5,3), enable_events=True,font=("Calibri", 18,"bold")))
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
            place(sg.Text('Image Preprocessing: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox('',key='checkbox_image_preprocessing'))
        ],
        [
            sg.Push(),
            place(sg.Text('Fix Rotation: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['none','auto','clockwise','counter-clockwise'],default_value='none',
                           key='list_fix_rotation',enable_events=True,size=(10,13),readonly=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Upscaling Image: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_upscaling_image',
                           enable_events=True,readonly=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Denoise Image: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['none','waifu2x'],default_value='none',key='list_denoise_image',
                           enable_events=True,readonly=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Fix Illumination: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox(text='',key='checkbox_fix_illumination',
                              enable_events=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Binarize: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['none','fax','otsu'],default_value='none',key='list_binarize',
                           enable_events=True,readonly=True))
        ]
    ]

    pipeline_tesseract_options = [
        [
            sg.Push(),
            place(sg.Text('DPI: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.InputText(key='tesseract_input_dpi',enable_events=True,size=(5,1)))
        ],
        [
            sg.Push(),
            place(sg.Text('PSM: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.InputText(key='tesseract_input_psm',enable_events=True,size=(5,1)))
        ],
        [
            sg.Push(),
            place(sg.Text('Language: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['eng','por'],default_value='eng',key='tesseract_list_lang',
                           enable_events=True,size=(5,1)))
        ]
    ]

    pipeline_posprocessing_options = [
        [
            place(sg.Text('Posprocessing: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox('',key='checkbox_posprocessing',default=True,enable_events=True,
                              size=(10,1)))
        ],
        [
            sg.Push(),
            place(sg.Text('Clean OCR: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox('',key='checkbox_clean_ocr',default=True,enable_events=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Bound Box Image Fix: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox('',key='checkbox_bound_box_fix_image',default=True,enable_events=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Split Whitespaces: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox('',key='checkbox_split_whitespaces',default=True,enable_events=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Diff ratio [split whitespaces]: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.InputText(key='input_split_whitespaces_diff_ratio',enable_events=True,size=(2,1)))
        ],
        [
            sg.Push(),
            place(sg.Text('Unite Blocks: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox('',key='checkbox_unite_blocks',enable_events=True))
        ],
        [
            sg.Push(),
            place(sg.Text('Find Titles: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Checkbox('',key='checkbox_find_titles',enable_events=True))
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
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Text('Posprocessing Options',font=("Calibri", 14,"bold"),text_color='#046380')
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Column(pipeline_posprocessing_options)
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Text('Output Options',font=("Calibri", 14,"bold"),text_color='#046380')
        ],
        [
            place(sg.Text('Single Block: ',font=("Calibri", 12,"bold"),text_color='#046380')),
            place(sg.Checkbox('',key='checkbox_pipeline_output_single_block',enable_events=True))
        ]
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
            place(sg.Text('Type of Document: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['newspaper','other'],default_value='newspaper',readonly=True,
                           key='list_type_of_document',enable_events=True,font=("Calibri", 18,"bold")))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Ignore Delimiters: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_ignore_delimiters',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Override type [categorize blocks]: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_override_type',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Title priority [Calculate Reading Order]: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_title_priority_calculate_reading_order',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text(text='Target Segments: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Text(text='Header',key='text_target_header',font=("Calibri", 15),text_color='#046380')),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_target_header',enable_events=True,metadata=True)),
            place(sg.Text(text='Body',key='text_target_body',font=("Calibri", 15),text_color='#046380')),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_target_body',enable_events=True,metadata=True)),
            place(sg.Text(text='Footer',key='text_target_footer',font=("Calibri", 15),text_color='#046380')),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_target_footer',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Image Split [Keep Intersecting Boxes]: ',font=("Calibri", 18,"bold"),
                          text_color='#046380')),
            sg.Push(),
            place(sg.Image(checked,key='-CHECKBOX-checkbox_image_split_keep_intersecting_boxes',enable_events=True,metadata=True))
        ],
        [
            sg.VPush()
        ],
        [
            place(sg.Text('Article Gathering: ',font=("Calibri", 18,"bold"),text_color='#046380')),
            sg.Push(),
            place(sg.Combo(['selected','fill'],default_value='selected',key='list_article_gathering',
                           enable_events=True,font=("Calibri", 18,"bold"),readonly=True))
        ]
    ]


    simple_optios_tab = sg.Tab('Editor',simple_options,expand_y=True)
    methods_options_tab = sg.Tab('Tools',methods_options,expand_y=True)
    pipeline_options_tab = sg.Tab('Pipeline',pipeline_options,expand_y=True)

    # final layout
    layout = [
        [
            place(sg.TabGroup([[simple_optios_tab,methods_options_tab,pipeline_options_tab]],
                              font=("Calibri", 15,'bold'),title_color='#046380',expand_y=True))
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
                       force_toplevel=True,location=location,
                       )
    window.bind('<Configure>',"Event")

    window['checkbox_image_preprocessing'].widget.configure(takefocus=0) # bugged for some reason
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

    window = sg.Window(title,layout,finalize=True,resizable=True,location=location,
                       keep_on_top=True,force_toplevel=True,modal=modal)
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
    