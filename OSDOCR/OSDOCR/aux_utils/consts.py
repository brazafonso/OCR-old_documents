import os

current_path = os.getcwd()
osdocr_path = os.path.dirname(os.path.realpath(__file__)) + '/..'
result_path = f'{current_path}/results'
tmp_path = f'{current_path}/tmp'

config_file_path = f'{osdocr_path}/config/conf.json'

config = {}