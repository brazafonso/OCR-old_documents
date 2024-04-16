import PySimpleGUI as sg


def build_gui_config_pipeline()->sg.Window:
    '''Build window for config pipeline'''
    configs = [
        [
            sg.Text('Output Folder:'),
            sg.InputText(key='output_folder_path'),
            sg.FolderBrowse(),
        ],
        [
            sg.Text('Output Type:'),
            sg.Combo(['Markdown'],default_value='Markdown',key='select_list_1_1',enable_events=True,size=(5,10)),
        ],
        [
            sg.Checkbox('Force OCR:',default=True,key='checkbox_1_1',enable_events=True,size=(15,10)),
        ],
        [
            sg.Checkbox('Ignore Delimiters:',default=True,key='checkbox_1_2',enable_events=True,size=(15,10)),
        ],
        [
            sg.Checkbox('Fix Rotation:',default=True,key='checkbox_1_3',enable_events=True,size=(15,10)),
            sg.Combo(['Auto','Clockwise','Counterclockwise'],default_value='Auto',key='select_list_1_1',enable_events=True,size=(5,10)),
        ],
        [
            sg.Checkbox('Upscale Image:',default=True,key='checkbox_1_4',enable_events=True,size=(15,10)),
            sg.Combo(['waifu2x','waifu4x'],default_value='waifu2x',key='select_list_1_2',enable_events=True,size=(5,10)),
        ],
        [
            sg.Checkbox('Denoise Image:',default=True,key='checkbox_1_5',enable_events=True,size=(15,10)),
            sg.Combo(['waifu2x'],default_value='waifu2x',key='select_list_1_3',enable_events=True,size=(5,10)),
            sg.Combo(['-1','0','1','2','3'],default_value='1',key='select_list_1_4',enable_events=True,size=(5,10)),
        ],
        [
            sg.Text('Tesseract Language:'),
            sg.Combo(['eng','por'],default_value='por',key='select_list_1_5',enable_events=True,size=(5,10)),
        ],
        [
            sg.Text('Tesseract DPI:'),
            sg.Input(default_text='150',key='input_1_1',enable_events=True,size=(5,10)),
        ],
        [
            sg.Text('Tesseract psm:'),
            sg.Combo([str(x) for x in range(14)],default_value='3',key='select_list_1_6',enable_events=True,size=(5,10)),
        ],
        [
            sg.Checkbox('Debug Mode:',default=False,key='checkbox_1_6',enable_events=True,size=(15,10)),
        ],
        [
            sg.Button('Cancel'),
            sg.Button('Save',key='save'),
        ]
    ]



    window = sg.Window('Pipeline Configs',configs,finalize=True,resizable=True,size=(1200,800))
    window.bind('<Configure>',"Event")
    return window