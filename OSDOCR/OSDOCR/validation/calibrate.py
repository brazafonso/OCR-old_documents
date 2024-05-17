import json
import os
import shutil
import sys
import aux_utils.consts as consts
from argparse import Namespace
from parse_args import process_args
from pipeline import run_target

file_path = os.path.dirname(os.path.realpath(__file__))


def prepare_pipeline_option(pipeline_option:str,target_image:str,default_args:str,results_folder:str,
                            option:str,logs:bool=False,debug:bool=False)->Namespace:
    '''Prepare pipeline option for calibration'''

    # load pipeline args
    pipeline_args = Namespace(**vars(default_args))
    options = json.load(open(f'{pipeline_option}','r'))
    for key in options:
        pipeline_args.__setattr__(key,options[key])

    pipeline_args.__setattr__('logs',logs)
    pipeline_args.__setattr__('debug',debug)
    pipeline_args.__setattr__('target',target_image)
    
    # results folder for option
    consts.result_path = f'{results_folder}/{option}'

    # create results folder
    if not os.path.exists(consts.result_path):
        os.mkdir(consts.result_path)
    else:
        # clear results folder
        for file in os.listdir(consts.result_path):
            shutil.rmtree(f'{consts.result_path}/{file}')

    return pipeline_args


def run_calibrate(calibration_folder:str,logs:bool=False,debug:bool=False):
    '''Find the best calibration for OSDOCR using prepared ground truth data.
        Possible files:
        - target_image.<extension>
        - ground_truth.txt
        - parcial_ground_truth.txt
    '''

    if logs:
        print('Running calibration...')
        print('Calibration folder:',calibration_folder)

    # check if calibration folder is valid
    if not os.path.exists(calibration_folder):
        print(f'Calibration folder not found: {calibration_folder}')
        return
    
    target_image = None
    files = os.listdir(calibration_folder)
    for file in files:
        if 'target_image' in file:
            target_image = f'{calibration_folder}/{file}'
            break

    if not target_image:
        print(f'No target image found in {calibration_folder}')
        return
    
    if not os.path.exists(f'{calibration_folder}/ground_truth.txt') and not os.path.exists(f'{calibration_folder}/parcial_ground_truth.txt'):
        print(f'No ground truth files found in {calibration_folder}')
        return
    
    pipeline_options_path = f'{file_path}/pipeline_options'

    # modify results folder
    results_folder = f'{calibration_folder}/results'

    # create results folder
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)

    # default args for pipeline
    sys.argv = [sys.argv[0]]
    default_args:Namespace = process_args()

    # for each pipeline option
        # run pipeline and compare results with ground truth
        # save comparison results
    for option in os.listdir(pipeline_options_path):
        if option.endswith('.json'):

            pipeline_args = prepare_pipeline_option(f'{pipeline_options_path}/{option}',target_image,
                                                    default_args,results_folder,option,logs,debug)
        
            # run pipeline
            print(f'''
                ================================
                ||      Running pipeline      ||
                ================================
                || Option: {option[:19]}{' '*(19-len(option[:19]))}||
                ================================''')
            
            run_target(target_image,pipeline_args)
    

