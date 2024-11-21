import collections
import re
from .layouts.ocr_editor_layout import configurations_layout,checked,unchecked
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
        'output_format' : 'markdown',
        'output_path' : os.getcwd(),
        'fix_hifenization' : True,
        'calculate_reading_order' : False,
        'use_pipeline_results' : True,
        'cache_size' : 10,
        'ppi' : 300,
        'interaction_range' : 10,
        'vertex_radius' : 5,
        'edge_thickness' : 2,
        'default_edge_color' : None,
        'id_text_size' : 10,
        'debug' : False,
    },
    'ocr_pipeline' : {
        'image_preprocess' : True,
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
        'posprocess' : True,
        'clean_ocr' : True,
        'bound_box_fix_image' : True,
        'split_whitespace' : 3,
        'unite_blocks' : True,
        'find_titles' : True,
        'output_single_block' : False
    },
    'methods' : {
        'article_gathering' : 'selected',
        'doc_type' : 'newspaper',
        'ignore_delimiters' : False,
        'override_type_categorize_blocks' : True,
        'title_priority_calculate_reading_order' : False,
        'target_segments' : ['header', 'body'],
        'image_split_keep_all' : False
    },
    'user' : {
        'image_input_path' : '',
        'ocr_results__input_path' : '',
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
    else:
        with open(config_file_path, 'w') as f:
            json.dump(config, f, indent=4)

    # update config to have all keys in default config
    config = fill_dict(config, default_config)

    return config

def read_config_window(window:sg.Window,values:dict)->dict:
    '''Read config window values'''
    config = read_ocr_editor_configs_file()

    # base values
    config['base']['text_confidence'] = values['slider_text_confidence']
    config['base']['output_format'] = values['list_output_format']
    config['base']['output_type'] = values['list_output_type']
    config['base']['output_path'] = values['input_output_path']
    config['base']['fix_hifenization'] = window['-CHECKBOX-checkbox_fix_hifenization'].metadata
    config['base']['calculate_reading_order'] = window['-CHECKBOX-checkbox_calculate_reading_order'].metadata
    config['base']['use_pipeline_results'] = window['-CHECKBOX-checkbox_use_pipeline_results'].metadata
    config['base']['debug'] = window['-CHECKBOX-checkbox_debug_mode'].metadata
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
    config['base']['default_edge_color'] = values['input_edge_color']
    try:
        config['base']['id_text_size'] = int(values['input_id_text_size'])
    except:
        pass

    # ocr pipeline values
    config['ocr_pipeline']['image_preprocess'] = values['checkbox_image_preprocessing']
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
    config['ocr_pipeline']['posprocess'] = values['checkbox_posprocessing']
    config['ocr_pipeline']['clean_ocr'] = values['checkbox_clean_ocr']
    config['ocr_pipeline']['bound_box_fix_image'] = values['checkbox_bound_box_fix_image']
    if values['checkbox_split_whitespaces']:
        try:
            config['ocr_pipeline']['split_whitespace'] = int(values['input_split_whitespaces_diff_ratio'])
        except:
            pass
    else:
        config['ocr_pipeline']['split_whitespace'] = 'none'
    config['ocr_pipeline']['unite_blocks'] = values['checkbox_unite_blocks']
    config['ocr_pipeline']['find_titles'] = values['checkbox_find_titles']
    config['ocr_pipeline']['output_single_block'] = values['checkbox_pipeline_output_single_block']

    # methods values
    config['methods']['article_gathering'] = values['list_article_gathering']
    config['methods']['doc_type'] = values['list_type_of_document']
    config['methods']['ignore_delimiters'] = window['-CHECKBOX-checkbox_ignore_delimiters'].metadata
    config['methods']['override_type_categorize_blocks'] = window['-CHECKBOX-checkbox_override_type'].metadata
    config['methods']['title_priority_calculate_reading_order'] = window['-CHECKBOX-checkbox_title_priority_calculate_reading_order'].metadata
    config['methods']['target_segments'] = []
    if window['-CHECKBOX-checkbox_target_header'].metadata:
        config['methods']['target_segments'].append('header')
    if window['-CHECKBOX-checkbox_target_body'].metadata:
        config['methods']['target_segments'].append('body')
    if window['-CHECKBOX-checkbox_target_footer'].metadata:
        config['methods']['target_segments'].append('footer')
    config['methods']['image_split_keep_all'] = window['-CHECKBOX-checkbox_image_split_keep_intersecting_boxes'].metadata

    return config


def update_dict(d: dict, new_values: dict):
    for k, v in new_values.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def fill_dict(d: dict, new_values: dict):
    for k, v in new_values.items():
        if k not in d:
            d[k] = v
        elif isinstance(v, collections.abc.Mapping):
            d[k] = fill_dict(d.get(k, {}), v)
    return d


def refresh_config_window(window:sg.Window, config:dict):
    '''Refresh config window values'''
    global default_config
    refresh_conf = deepcopy(default_config)
    refresh_conf = update_dict(refresh_conf, config)

    # base values
    window['slider_text_confidence'].update(refresh_conf['base']['text_confidence'])
    window['list_output_format'].update(refresh_conf['base']['output_format'])
    window['list_output_type'].update(refresh_conf['base']['output_type'])
    window['input_output_path'].update(refresh_conf['base']['output_path'])
    window['-CHECKBOX-checkbox_fix_hifenization'].update(checked if refresh_conf['base']['fix_hifenization'] else unchecked)
    window['-CHECKBOX-checkbox_fix_hifenization'].metadata = refresh_conf['base']['fix_hifenization']
    window['-CHECKBOX-checkbox_calculate_reading_order'].update(checked if refresh_conf['base']['calculate_reading_order'] else unchecked)
    window['-CHECKBOX-checkbox_calculate_reading_order'].metadata = refresh_conf['base']['calculate_reading_order']
    window['-CHECKBOX-checkbox_use_pipeline_results'].update(checked if refresh_conf['base']['use_pipeline_results'] else unchecked)
    window['-CHECKBOX-checkbox_use_pipeline_results'].metadata = refresh_conf['base']['use_pipeline_results']
    window['-CHECKBOX-checkbox_debug_mode'].update(checked if refresh_conf['base']['debug'] else unchecked)
    window['-CHECKBOX-checkbox_debug_mode'].metadata = refresh_conf['base']['debug']
    window['input_operations_cache_size'].update(refresh_conf['base']['cache_size'])
    window['input_default_ppi'].update(refresh_conf['base']['ppi'])
    window['input_vertex_radius'].update(refresh_conf['base']['vertex_radius'])
    window['input_edge_thickness'].update(refresh_conf['base']['edge_thickness'])
    window['input_edge_color'].update(refresh_conf['base']['default_edge_color'] if refresh_conf['base']['default_edge_color'] else '')
    window['input_id_text_size'].update(refresh_conf['base']['id_text_size'])

    # ocr pipeline values
    window['checkbox_image_preprocessing'].update(refresh_conf['ocr_pipeline']['image_preprocess'])
    window['list_fix_rotation'].update(refresh_conf['ocr_pipeline']['fix_rotation'])
    window['list_upscaling_image'].update(refresh_conf['ocr_pipeline']['upscaling_image'])
    window['list_denoise_image'].update(refresh_conf['ocr_pipeline']['denoise_image'])
    window['checkbox_fix_illumination'].update(refresh_conf['ocr_pipeline']['fix_illumination'])
    window['list_binarize'].update(refresh_conf['ocr_pipeline']['binarize'])
    window['tesseract_input_dpi'].update(refresh_conf['ocr_pipeline']['tesseract_config']['dpi'])
    window['tesseract_input_psm'].update(refresh_conf['ocr_pipeline']['tesseract_config']['psm'])
    window['tesseract_list_lang'].update(refresh_conf['ocr_pipeline']['tesseract_config']['l'])
    window['checkbox_posprocessing'].update(refresh_conf['ocr_pipeline']['posprocess'])
    window['checkbox_clean_ocr'].update(refresh_conf['ocr_pipeline']['clean_ocr'])
    window['checkbox_bound_box_fix_image'].update(refresh_conf['ocr_pipeline']['bound_box_fix_image'])
    window['checkbox_split_whitespaces'].update(refresh_conf['ocr_pipeline']['split_whitespace'] != 'none')
    window['input_split_whitespaces_diff_ratio'].update(refresh_conf['ocr_pipeline']['split_whitespace'])
    window['checkbox_unite_blocks'].update(refresh_conf['ocr_pipeline']['unite_blocks'])
    window['checkbox_find_titles'].update(refresh_conf['ocr_pipeline']['find_titles'])
    window['checkbox_pipeline_output_single_block'].update(refresh_conf['ocr_pipeline']['output_single_block'])

    # method values
    window['list_type_of_document'].update(refresh_conf['methods']['doc_type'])
    window['-CHECKBOX-checkbox_ignore_delimiters'].update(checked if refresh_conf['methods']['ignore_delimiters'] else unchecked)
    window['-CHECKBOX-checkbox_ignore_delimiters'].metadata = refresh_conf['methods']['ignore_delimiters']
    window['-CHECKBOX-checkbox_override_type'].update(checked if refresh_conf['methods']['override_type_categorize_blocks'] else unchecked)
    window['-CHECKBOX-checkbox_override_type'].metadata = refresh_conf['methods']['override_type_categorize_blocks']
    window['-CHECKBOX-checkbox_title_priority_calculate_reading_order'].update(checked if refresh_conf['methods']['title_priority_calculate_reading_order'] else unchecked)
    window['-CHECKBOX-checkbox_title_priority_calculate_reading_order'].metadata = refresh_conf['methods']['title_priority_calculate_reading_order']
    window['-CHECKBOX-checkbox_target_header'].update(checked if 'header' in refresh_conf['methods']['target_segments'] else unchecked)
    window['-CHECKBOX-checkbox_target_header'].metadata = 'header' in refresh_conf['methods']['target_segments']
    window['-CHECKBOX-checkbox_target_body'].update(checked if 'body' in refresh_conf['methods']['target_segments'] else unchecked)
    window['-CHECKBOX-checkbox_target_body'].metadata = 'body' in refresh_conf['methods']['target_segments']
    window['-CHECKBOX-checkbox_target_footer'].update(checked if 'footer' in refresh_conf['methods']['target_segments'] else unchecked)
    window['-CHECKBOX-checkbox_target_footer'].metadata = 'footer' in refresh_conf['methods']['target_segments']
    window['list_article_gathering'].update(refresh_conf['methods']['article_gathering'])
    window['-CHECKBOX-checkbox_image_split_keep_intersecting_boxes'].update(checked if refresh_conf['methods']['image_split_keep_all'] else unchecked)
    window['-CHECKBOX-checkbox_image_split_keep_intersecting_boxes'].metadata = refresh_conf['methods']['image_split_keep_all']



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
        print(f'Config window event: {event}')
        if event in [sg.WIN_CLOSED, 'button_cancel']:
            break
        elif event == 'button_save':
            config = read_config_window(config_window,values)
            save_config_file(config)
            break
        elif event == 'button_reset':
            config = deepcopy(default_config)
            refresh_config_window(config_window, config)
        elif '-CHECKBOX-' in event:
            config_window[event].metadata = not config_window[event].metadata
            config_window[event].update(checked if config_window[event].metadata else unchecked)

    print('Closing config window')
    config_window.close()
    config = read_ocr_editor_configs_file()
    del config_window
    print('Config window closed')
    return config