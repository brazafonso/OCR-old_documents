import json
import os
import hashlib
from aux_utils import consts



def path_to_id(path: str):
    """Convert a path to an id, joins file name and path hash"""
    # verify os system, change path separator
    if os.name == 'nt':
        path = path.replace('\\\\','\\')
        path = path.replace('\\','/')

    file_name = path.split('/')[-1].split('.')[0]
    path_hash = hashlib.md5('/'.join(path.split('/')[:-1]).encode('utf-8')).hexdigest()

    return f'{file_name}_{path_hash}'


def read_configs():
    '''Read program configs from config.json'''
    conf = {}
    if os.path.exists(consts.config_file_path):
        conf_file = open(consts.config_file_path,'r')
        conf = json.load(conf_file)
        conf_file.close()
        if not os.path.exists(conf['target_image_path']):
            conf['target_image_path'] = ''
    else:
        conf = {
            'target_image_path':'',
            'resolutions':[],
        }
    consts.config = conf

def save_configs():
    '''Save program configs to config.json'''
    conf_file = open(consts.config_file_path,'w')
    json.dump(consts.config,conf_file,indent=4)
    conf_file.close()


def clean_tmp_folder():
    '''Clean tmp folder. Removes all files in tmp folder with 'OSDOcr' in the name''' 
    if os.path.exists(consts.tmp_path):
        files = os.listdir(consts.tmp_path)
        for file in files:
            if 'OSDOcr' in file:
                os.remove(f'{consts.tmp_path}/{file}')

def create_target_results_folder(target_path:str):
    '''Create results folder for target image'''
    results_folder = f'{consts.result_path}/{path_to_id(target_path)}'
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)

    # create processed folder
    processed_folder_path = f'{results_folder}/processed'
    if not os.path.exists(processed_folder_path):
        os.mkdir(processed_folder_path)

    create_target_metadata(target_path)


def create_target_metadata(target_path:str):
    '''Create target metadata'''
    metadata = {
        'target_original_path':target_path,
        'target_path':target_path,
        'ocr': False,
        'ocr_results_original_path': '',
        'orc_results_path': '',
        'transformations': []
    }
    save_target_metadata(target_path,metadata)

def create_metadata(results_path:str):
    '''Create target metadata'''
    metadata = {
        'ocr': False,
        'ocr_results_original_path': '',
        'orc_results_path': '',
        'transformations': []
    }
    save_metadata(results_path,metadata)

def get_target_metadata(target_path:str):
    '''Get target metadata'''
    results_folder = f'{consts.result_path}/{path_to_id(target_path)}'
    metadata = {}
    if os.path.exists(f'{results_folder}/metadata.json'):
        metadata_file = open(f'{results_folder}/metadata.json','r')
        metadata = json.load(metadata_file)
        metadata_file.close()
    return metadata

def get_metadata(results_path:str):
    '''Get target metadata'''
    metadata = {}
    if os.path.exists(f'{results_path}/metadata.json'):
        metadata_file = open(f'{results_path}/metadata.json','r')
        metadata = json.load(metadata_file)
        metadata_file.close()
    return metadata

def save_target_metadata(target_path:str,metadata:dict):
    '''Save target metadata'''
    results_folder = f'{consts.result_path}/{path_to_id(target_path)}'
    metadata_file = open(f'{results_folder}/metadata.json','w')
    json.dump(metadata,metadata_file,indent=4)
    metadata_file.close()

def save_metadata(results_path:str,metadata:dict):
    '''Save target metadata'''
    metadata_file = open(f'{results_path}/metadata.json','w')
    json.dump(metadata,metadata_file,indent=4)
    metadata_file.close()


def reset_target_metadata(target_path:str):
    '''Reset target metadata'''
    metadata_path = f'{consts.result_path}/{path_to_id(target_path)}/metadata.json'
    os.remove(metadata_path)
    create_target_metadata(target_path)

def reset_metadata(results_path:str):
    '''Reset target metadata'''
    metadata_path = f'{results_path}/metadata.json'
    os.remove(metadata_path)
    create_metadata(results_path)


def metadata_has_transformation(metadata:dict,transformation:str):
    '''Check if metadata has transformation'''
    transformations = metadata['transformations']
    for t in transformations:
        if type(t) in (list,tuple):
            if t[0] == transformation:
                return True
        elif t == transformation:
            return True
    return False