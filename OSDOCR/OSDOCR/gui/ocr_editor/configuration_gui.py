import collections
from .layouts.ocr_editor_layout import configurations_layout
from copy import deepcopy
import PySimpleGUI as sg
import json
import os
import OSDOCR.aux_utils.consts as consts

config_folder_path = f'{consts.ocr_editor_path}/config'
config_file_path = f'{config_folder_path}/conf.json'

# default configuration
default_config = {
    'base': {
        'text_confidence' : 0,
        'output_type' : ['newspaper'],
        'output_path' : os.getcwd(),
        'cache_size' : 10,
        'ppi' : 300,
        'interaction_range' : 10,
        'vertex_radius' : 5,
        'edge_thickness' : 2,
        'id_text_size' : 10,
    },
    'ocr_pipeline' : {
        'fix_rotation' : 'none',
        'upscaling_image' : 'none',
        'denoise_image' : 'none',
        'fix_illumination' : False,
        'binarize' : 'none',
        'tesseract_config' : {
            'l' : 'por',
            'dpi' : 300,
            'psm' : 3
        },
    },
    'methods' : {
        'article_gathering' : 'selected',
        'doc_type' : 'newspaper',
        'ignore_delimiters' : False,
        'calculate_reading_order' : False,
        'target_segments' : ['header', 'body'],
        'use_pipeline_results' : True,
        'image_split_keep_all' : False
    }
}

def read_ocr_editor_configs_file()->dict:
    '''Read config file if exists, else return default config'''
    global default_config, config_folder_path, config_file_path
    
    config = deepcopy(default_config)

    # create config folder if not exists
    if not os.path.exists(config_folder_path):
        os.makedirs(config_folder_path)

    # read file values
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            config = deepcopy(default_config)

    return config

def read_config_window(values:dict)->dict:
    '''Read config window values'''
    config = read_ocr_editor_configs_file()

    # base values
    config['base']['text_confidence'] = values['slider_text_confidence']
    config['base']['output_type'] = values['list_output_type']
    config['base']['use_pipeline_results'] = values['checkbox_use_pipeline_results']
    config['base']['output_path'] = values['input_output_path']
    try:
        config['base']['cache_size'] = int(values['input_operations_cache_size'])
    except:
        pass
    try:
        config['base']['ppi'] = int(values['input_default_ppi'])
    except:
        pass
    try:
        config['base']['vertex_radius'] = int(values['input_vertex_radius'])
    except:
        pass
    try:
        config['base']['edge_thickness'] = int(values['input_edge_thickness'])
    except:
        pass
    try:
        config['base']['id_text_size'] = int(values['input_id_text_size'])
    except:
        pass

    # ocr pipeline values
    config['ocr_pipeline']['fix_rotation'] = values['list_fix_rotation']
    config['ocr_pipeline']['upscaling_image'] = values['list_upscaling_image']
    config['ocr_pipeline']['denoise_image'] = values['list_denoise_image']
    config['ocr_pipeline']['fix_illumination'] = values['checkbox_fix_illumination']
    config['ocr_pipeline']['binarize'] = values['list_binarize']
    try:
        config['ocr_pipeline']['tesseract_config']['dpi'] = int(values['tesseract_input_dpi'])
    except:
        pass
    try:
        config['ocr_pipeline']['tesseract_config']['psm'] = values['tesseract_input_psm']
    except:
        pass
    config['ocr_pipeline']['tesseract_config']['l'] = values['tesseract_list_lang']

    # methods values
    config['methods']['article_gathering'] = values['list_article_gathering']
    config['methods']['doc_type'] = values['list_type_of_document']
    config['methods']['ignore_delimiters'] = values['checkbox_ignore_delimiters']
    config['methods']['calculate_reading_order'] = values['checkbox_calculate_reading_order']
    config['methods']['target_segments'] = []
    if values['checkbox_target_header']:
        config['methods']['target_segments'].append('header')
    if values['checkbox_target_body']:
        config['methods']['target_segments'].append('body')
    if values['checkbox_target_footer']:
        config['methods']['target_segments'].append('footer')
    config['methods']['image_split_keep_all'] = values['checkbox_image_split_keep_intersecting_boxes']

    return config


def update_dict(d: dict, new_values: dict):
    for k, v in new_values.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def refresh_config_window(window:sg.Window, config:dict):
    '''Refresh config window values'''
    global default_config
    refresh_conf = deepcopy(default_config)
    refresh_conf = update_dict(refresh_conf, config)

    # base values
    window['slider_text_confidence'].update(refresh_conf['base']['text_confidence'])
    window['list_output_type'].update(refresh_conf['base']['output_type'])
    window['checkbox_use_pipeline_results'].update(refresh_conf['base']['use_pipeline_results'])
    window['input_output_path'].update(refresh_conf['base']['output_path'])
    window['input_operations_cache_size'].update(refresh_conf['base']['cache_size'])
    window['input_default_ppi'].update(refresh_conf['base']['ppi'])
    window['input_vertex_radius'].update(refresh_conf['base']['vertex_radius'])
    window['input_edge_thickness'].update(refresh_conf['base']['edge_thickness'])
    window['input_id_text_size'].update(refresh_conf['base']['id_text_size'])

    # ocr pipeline values
    window['list_fix_rotation'].update(refresh_conf['ocr_pipeline']['fix_rotation'])
    window['list_upscaling_image'].update(refresh_conf['ocr_pipeline']['upscaling_image'])
    window['list_denoise_image'].update(refresh_conf['ocr_pipeline']['denoise_image'])
    window['checkbox_fix_illumination'].update(refresh_conf['ocr_pipeline']['fix_illumination'])
    window['list_binarize'].update(refresh_conf['ocr_pipeline']['binarize'])
    window['tesseract_input_dpi'].update(refresh_conf['ocr_pipeline']['tesseract_config']['dpi'])
    window['tesseract_input_psm'].update(refresh_conf['ocr_pipeline']['tesseract_config']['psm'])
    window['tesseract_list_lang'].update(refresh_conf['ocr_pipeline']['tesseract_config']['l'])

    # method values
    window['list_type_of_document'].update(refresh_conf['methods']['doc_type'])
    window['checkbox_ignore_delimiters'].update(refresh_conf['methods']['ignore_delimiters'])
    window['checkbox_calculate_reading_order'].update(refresh_conf['methods']['calculate_reading_order'])
    window['checkbox_target_header'].update('header' in refresh_conf['methods']['target_segments'])
    window['checkbox_target_body'].update('body' in refresh_conf['methods']['target_segments'])
    window['checkbox_target_footer'].update('footer' in refresh_conf['methods']['target_segments'])
    window['list_article_gathering'].update(refresh_conf['methods']['article_gathering'])
    window['checkbox_image_split_keep_intersecting_boxes'].update(refresh_conf['methods']['image_split_keep_all'])



def save_config_file(config:dict):
    '''Save config file'''
    global config_folder_path, config_file_path
    with open(config_file_path, 'w') as f:
        json.dump(config, f, indent=4)



def run_config_gui(position:tuple=None):
    '''Run ocr editor'''
    global default_config
    config_window = configurations_layout(position=position)
    config = read_ocr_editor_configs_file()
    refresh_config_window(config_window, config)

    while True:
        event, values = config_window.read()
        if event in [sg.WIN_CLOSED, 'button_cancel']:
            break
        elif event == 'button_save':
            config = read_config_window(values)
            save_config_file(config)
            break
        elif event == 'button_reset':
            config = deepcopy(default_config)
            refresh_config_window(config_window, config)

    config_window.close()
    config = read_ocr_editor_configs_file()
    return config