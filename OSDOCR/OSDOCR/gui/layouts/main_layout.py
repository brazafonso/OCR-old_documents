import PySimpleGUI as sg


def build_gui_main()->sg.Window:
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
            sg.Button('Tesseract',key='sidebar_method_run_tesseract'),
        ],
        [
            sg.Button('Fix Blocks',key='sidebar_method_fix_blocks'),
        ],
        [
            sg.Button('Journal Template',key='sidebar_method_journal_template'),
        ],
        [
            sg.Button('Reading Order',key='sidebar_method_reading_order'),
        ],
        [
            sg.Button('Extract Articles',key='sidebar_method_extract_articles'),
        ],
        [
            sg.Button('Auto Rotate',key='sidebar_method_auto_rotate'),
        ],
        [
            sg.Button('Unite blocks',key='sidebar_method_unite_blocks'),
        ],
        [
            sg.Button('Divide Columns',key='sidebar_method_divide_columns'),
        ]
    ]

    first_layout_1 = [
        [
            sg.Column(method_sidebar,expand_x=False,expand_y=True),
        ]
    ]

    first_layout_2_1 = [
        [
            sg.Button('Apply',key='apply'),
        ],
        [
            sg.Checkbox('Auto Rotate:',default=True,key='checkbox_1_1',enable_events=True,size=(15,10),visible=False),
        ],
        [
            sg.Text('Skew Direction:',key='select_list_text_1_1',visible=False),
            sg.Combo(['Auto','Clockwise','Counterclockwise'],default_value='Auto',key='select_list_1_1',enable_events=True,size=(5,10),visible=False),
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
            sg.Column(first_layout_2_1,expand_x=True,expand_y=False),
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
    ### target image
    ### select list
    ### apply button
    ### result text
    
    method_sidebar_2 = [
        [
            sg.Button('OCR Pipeline',key='sidebar_method_ocr_pipeline'),
        ],
        [
            sg.Button('Calculate DPI',key='sidebar_method_calculate_dpi'),
        ]
    ]


    second_layout_1 = [
        [
            sg.Column(method_sidebar_2,expand_x=False,expand_y=True),
        ]
    ]

    second_layout_2 = [
        [
            sg.Image(filename=None,visible=True,key='target_image_path_2',size=(500,700)),
            sg.Button('Config',key='config_pipeline',visible=False),
            sg.Button('Apply',key='apply'),
            sg.Combo([],key='select_list_2_1',enable_events=True,size=(5,10)),
            sg.Text('Result:'),
            sg.Text('',visible=False,key='result_text_1'),
            sg.Multiline(visible=False,key='result_text_2',size=(500,500)),
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
    window.bind('<Configure>',"Event")
    return window