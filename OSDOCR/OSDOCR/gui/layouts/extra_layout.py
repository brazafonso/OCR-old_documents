import PySimpleGUI as sg
from ..aux_utils.utils import place

def build_gui_config_pipeline()->sg.Window:
    '''Build window for config pipeline'''
    configs = [
        [
            place(sg.Text('Output Folder:')),
            place(sg.InputText(key='output_folder_path')),
            place(sg.FolderBrowse()),
        ],
        [
            place(sg.Text('Output Type:')),
            place(sg.Combo(['Markdown'],default_value='Markdown',key='select_list_1_1',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Force OCR:',default=True,key='checkbox_1_1',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Checkbox('Ignore Delimiters:',default=True,key='checkbox_1_2',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Checkbox('Fix Rotation:',default=True,key='checkbox_1_3',enable_events=True,size=(15,10))),
            place(sg.Combo(['Auto','Clockwise','Counterclockwise'],default_value='Auto',key='select_list_1_1',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Upscale Image:',default=True,key='checkbox_1_4',enable_events=True,size=(15,10))),
            place(sg.Combo(['waifu2x','waifu4x'],default_value='waifu2x',key='select_list_1_2',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Denoise Image:',default=True,key='checkbox_1_5',enable_events=True,size=(15,10))),
            place(sg.Combo(['waifu2x'],default_value='waifu2x',key='select_list_1_3',enable_events=True,size=(5,10))),
            place(sg.Combo(['-1','0','1','2','3'],default_value='1',key='select_list_1_4',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract Language:')),
            place(sg.Combo(['eng','por'],default_value='por',key='select_list_1_5',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract DPI:')),
            place(sg.Input(default_text='150',key='input_1_1',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract psm:')),
            place(sg.Combo([str(x) for x in range(14)],default_value='3',key='select_list_1_6',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Debug Mode:',default=False,key='checkbox_1_6',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Button('Cancel')),
            place(sg.Button('Save',key='save')),
        ]
    ]



    window = sg.Window('Pipeline Configs',configs,finalize=True,resizable=True,size=(1200,800))
    window.bind('<Configure>',"Event")
    return window