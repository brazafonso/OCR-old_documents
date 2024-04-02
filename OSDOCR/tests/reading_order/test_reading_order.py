'''Test reading order

Each test has a single target image.
For each target image, diferent reading order complexities are tested.'''
import os
from argparse import Namespace
from OSDOcr import run_target_image
from aux_utils.misc import path_to_id
from ocr_tree_module.ocr_tree import OCR_Tree
from ocr_tree_module.ocr_tree_analyser import *
from ocr_tree_module.ocr_tree_fix import bound_box_fix

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

    ocr_results = categorize_boxes(ocr_results)

    return ocr_results


def get_reading_order(target,ocr_results,args=None):
    if not args:
        args = Namespace()
        args.ignore_delimiters = False

    # get journal template
    ## leaves only body
    image_info = get_image_info(target)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results,area=columns_area,ignore_delimiters=args.ignore_delimiters)
    order_list = sort_topologic_order(t_graph,sort_weight=True)

    return order_list

    
def clean_reading_order(reading_order,acceptable_orders):
    i = 0
    while i < len(reading_order):
        id = reading_order[i]
        in_order = False
        for order in acceptable_orders:
            if id in order:
                in_order = True
                break
        if not in_order:
            reading_order.remove(id)
        else:
            i += 1

    return reading_order


def test_reading_order_1_1():
    target = f'{study_cases_folder}/ideal/AAA-13.png'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])
    
    args = Namespace()
    args.ignore_delimiters = True
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [3,5,6,8,9,12]
    ]

    reading_order = clean_reading_order(reading_order,acceptable_orders)

    print('Cleaned reading order:',reading_order)
    assert reading_order in acceptable_orders


def test_reading_order_1_2():
    target = f'{study_cases_folder}/ideal/AAA-13.png'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])
    
    args = Namespace()
    args.ignore_delimiters = True
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [1,3,2,4,5,6,7,8,9,11,10,12,15,14,13],
        [1,3,2,4,5,6,7,8,9,11,10,12,14,15,13],
    ]

    reading_order = clean_reading_order(reading_order,acceptable_orders)

    print('Cleaned reading order:',reading_order)
    assert reading_order in acceptable_orders




def test_reading_order_2_1():
    target = f'{study_cases_folder}/ideal/AAA-19.png'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])

    args = Namespace()
    args.ignore_delimiters = True
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [5,11,13,19,23,34,35],
    ]

    # remove non existing ids from reading order
    reading_order = clean_reading_order(reading_order,acceptable_orders)
    

    print('Cleaned reading order:',reading_order)
    assert reading_order in acceptable_orders

def test_reading_order_2_2():
    target = f'{study_cases_folder}/ideal/AAA-19.png'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])

    args = Namespace()
    args.ignore_delimiters = True
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [0,5,7,9,11,13,15,12,16,3,19,21,23,32,33,34,35,37],
        [0,3,5,7,9,11,13,15,12,16,19,21,23,32,33,34,35,37],
    ]

    # remove non existing ids from reading order
    reading_order = clean_reading_order(reading_order,acceptable_orders)
    

    print('Cleaned reading order:',reading_order)
    assert reading_order in acceptable_orders

