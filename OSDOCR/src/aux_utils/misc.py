import json
import os
from aux_utils import consts



def path_to_id(path: str):
    """Convert a path to an id, geting the last 3 parts of the path and joining them with underscores"""
    # verify os system, change path separator
    if os.name == 'nt':
        path = path.replace('\\\\','\\')
        path = path.replace('\\','/')
    return '_'.join(path.split('/')[-3:])


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