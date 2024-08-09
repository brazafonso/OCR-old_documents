import os
from OSDOCR.aux_utils.misc import create_base_folders,read_configs

current_path = os.getcwd()
user_path = os.path.expanduser('~')
osdocr_path = f'{user_path}/OSDOCR'
result_path = f'{current_path}/results'
tmp_path = f'{user_path}/OSDOCR/tmp'


config_folder_path = f'{osdocr_path}/config'
config_file_path = f'{osdocr_path}/config/conf.json'
consts_path = f'{osdocr_path}/consts'
ocr_editor_path = f'{osdocr_path}/ocr_editor'
ocr_editor_tmp_path = f'{osdocr_path}/ocr_editor/tmp'

config = {}
create_base_folders()
read_configs()