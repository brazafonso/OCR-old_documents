'''Test columns calculations

Each test has a single target image.
For each target image, check number of columns is the same as the real one.'''
from argparse import Namespace
import os
from OSDOcr import run_target_image
from aux_utils.misc import path_to_id
from ocr_tree_module.ocr_tree import OCR_Tree
from ocr_tree_module.ocr_tree_analyser import get_columns

file_path = os.path.dirname(os.path.realpath(__file__))
study_cases_folder = f'{file_path}/../../../study_cases'
results_folder = f'{file_path}/../../../results'


def get_ocr_results(target,args= None):
    # get ocr_results
    results_path = f'{results_folder}/{path_to_id(target)}'
    if not args:
        args = Namespace()
        args.skip_method = [
                'image_preprocess'
            ]
        args.debug = False

    ocr_results = None
    if not os.path.exists(f'{results_path}/result.json'):
        ocr_results = run_target_image(target,results_folder,args)
    else:
        ocr_results = OCR_Tree(f'{results_path}/result.json')


    return ocr_results



def test_columns_number_1():
    target = f'{study_cases_folder}/ideal/AAA-13.png'

    ocr_results = get_ocr_results(target)

    columns = get_columns(ocr_results)

    assert len(columns) == 4

def test_columns_number_2():
    target = f'{study_cases_folder}/ideal/AAA-19.png'

    ocr_results = get_ocr_results(target)

    columns = get_columns(ocr_results)

    assert len(columns) == 4



def test_columns_number_3():
    target = f'{study_cases_folder}/complicated reading order/1-09.jpg'

    ocr_results = get_ocr_results(target)

    columns = get_columns(ocr_results)

    assert len(columns) == 4


def test_columns_number_4():
    target = f'{study_cases_folder}/simple template/2-1.jpg'

    ocr_results = get_ocr_results(target)

    columns = get_columns(ocr_results)

    assert len(columns) == 3
