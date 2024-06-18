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


def get_reading_order(target:str,ocr_results:OCR_Tree,args=None):
    if not args:
        args = Namespace()
        args.ignore_delimiters = False

    # get journal template
    ## leaves only body
    _,body,_ = segment_document(target)
    columns_area = body
    

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

def similarity(acceptable_order:list,reading_order:list):
    similarity = 0
    pairings = []
    for i,id_1 in enumerate(acceptable_order[:-1]):
        for id_2 in acceptable_order[i+1:]:
            pairings.append([id_1,id_2])

    total_pairings = len(pairings)
    valid_pairings = 0

    for pairing in pairings:
        id_1 = pairing[0]
        id_2 = pairing[1]
        if reading_order.index(id_1) < reading_order.index(id_2):
            valid_pairings += 1

    similarity = valid_pairings/total_pairings


    return similarity

def compare_reading_orders(real_reading_orders,result_reading_order,threshold=1):
    valid = False
    biggest_similarity = 0
    for real_reading_order in real_reading_orders:
        cleaned_reading_order = clean_reading_order(result_reading_order,[real_reading_order])
        real_reading_order = clean_reading_order(real_reading_order,[result_reading_order])
        if threshold == 1:
            if real_reading_order == cleaned_reading_order:
                valid = True
                break
        else:
            if similarity(real_reading_order,cleaned_reading_order) >= threshold:
                valid = True
                break

        if similarity(real_reading_order,cleaned_reading_order) > biggest_similarity:
            biggest_similarity = similarity(real_reading_order,cleaned_reading_order)

        print('Real:',real_reading_order)
        print('Cleaned:',cleaned_reading_order)
        print('Similarity:',similarity(real_reading_order,cleaned_reading_order))

    print('Biggest similarity:',biggest_similarity)
    return valid


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
    
    
    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)


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

    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)




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

    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)

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

    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)




def test_reading_order_3_1():
    target = f'{study_cases_folder}/simple template/2-1.jpg'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])
    ocr_results = categorize_boxes(ocr_results)
    args = Namespace()
    args.ignore_delimiters = False
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [2,17,31,40,51,58],
    ]

    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)

def test_reading_order_3_2():
    target = f'{study_cases_folder}/simple template/2-1.jpg'

    ocr_results = get_ocr_results(target)
    ocr_results = bound_box_fix(ocr_results,2,None)
    ocr_results.id_boxes([2])
    ocr_results = categorize_boxes(ocr_results)

    args = Namespace()
    args.ignore_delimiters = False
    reading_order = get_reading_order(target,ocr_results,args)
    print('Calculated reading order:',reading_order)

    acceptable_orders = [
        [2,11,12,17,31,37,40,51,53],
    ]

    assert compare_reading_orders(acceptable_orders,reading_order,threshold=0.8)

