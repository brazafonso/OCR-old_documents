import PySimpleGUI as sg
from ..aux_utils.utils import place
from aux_utils import consts

def build_gui_config_pipeline()->sg.Window:
    '''Build window for config ocr pipeline'''
    # read configs
    pipeline_config = consts.config['ocr_pipeline'] if 'ocr_pipeline' in consts.config else {}

    # set default values if no config
    if not pipeline_config:
        pipeline_config = {
            'target': '',
            'output_folder': '',
            'output_type': ['Markdown'],
            'force_ocr': True,
            'ignore_delimiters': False,
            'fix_rotation': ['auto'],
            'upscaling_image': ['waifu2x'],
            'denoise_image': ['waifu2x'],
            'tesseract_config': {
                'l': 'por',
                'dpi': 100,
                'psm': 3
            },
            'debug': False
        }

    output_type_default = pipeline_config['output_type']
    force_ocr = pipeline_config['force_ocr']
    ignore_delimiters = pipeline_config['ignore_delimiters']
    fix_rotation = True if pipeline_config['fix_rotation'] else False
    fix_rotation_default = pipeline_config['fix_rotation'][0] if fix_rotation else 'Auto'
    upscaling_image = True if pipeline_config['upscaling_image'] else False
    upscaling_image_default = pipeline_config['upscaling_image'][0] if upscaling_image else 'waifu2x'
    denoise_image = True if pipeline_config['denoise_image'] else False
    denoise_image_default = pipeline_config['denoise_image'][0] if denoise_image else 'waifu2x'
    denoise_image_level_default = pipeline_config['denoise_image'][1] if denoise_image else '1'
    tesseract_lang = pipeline_config['tesseract_config']['l']
    tesseract_dpi = pipeline_config['tesseract_config']['dpi']
    tesseract_psm = pipeline_config['tesseract_config']['psm']
    debug_opt = pipeline_config['debug']

    configs = [
        [
            place(sg.Text('Output Folder:')),
            place(sg.InputText(key='output_folder_path')),
            place(sg.FolderBrowse()),
        ],
        [
            place(sg.Text('Output Type:')),
            place(sg.Combo(['Markdown'],default_value=output_type_default,key='select_list_1_1',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Force OCR:',default=force_ocr,key='checkbox_1_1',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Checkbox('Ignore Delimiters:',default=ignore_delimiters,key='checkbox_1_2',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Checkbox('Fix Rotation:',default=fix_rotation,key='checkbox_1_3',enable_events=True,size=(15,10))),
            place(sg.Combo(['Auto','Clockwise','Counterclockwise'],default_value=fix_rotation_default,key='select_list_1_2',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Upscale Image:',default=upscaling_image,key='checkbox_1_4',enable_events=True,size=(15,10))),
            place(sg.Combo(['waifu2x','waifu4x'],default_value=upscaling_image_default,key='select_list_1_3',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Denoise Image:',default=True,key='checkbox_1_5',enable_events=True,size=(15,10))),
            place(sg.Combo(['waifu2x'],default_value=denoise_image_default,key='select_list_1_4',enable_events=True,size=(5,10))),
            place(sg.Combo(['-1','0','1','2','3'],default_value=denoise_image_level_default,key='select_list_1_5',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract Language:')),
            place(sg.Combo(['eng','por'],default_value=tesseract_lang,key='select_list_1_6',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract DPI:')),
            place(sg.Input(default_text=tesseract_dpi,key='input_1_1',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Text('Tesseract psm:')),
            place(sg.Combo([str(x) for x in range(14)],default_value=tesseract_psm,key='select_list_1_7',enable_events=True,size=(5,10))),
        ],
        [
            place(sg.Checkbox('Debug Mode:',default=debug_opt,key='checkbox_1_6',enable_events=True,size=(15,10))),
        ],
        [
            place(sg.Button('Cancel')),
            place(sg.Button('Save',key='save')),
        ]
    ]



    window = sg.Window('Pipeline Configs',configs,finalize=True,resizable=True,size=(1200,800))
    window.bind('<Configure>',"Event")
    return window