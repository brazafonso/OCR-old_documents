import json
import os
import shutil
import sys
import hashlib
import aux_utils.consts as consts
from argparse import Namespace
from aux_utils.misc import path_to_id
from parse_args import process_args
from pipeline import run_target
from ocr_tree_module.ocr_tree import OCR_Tree
from sklearn.feature_extraction.text import TfidfVectorizer

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
    pipeline_args.__setattr__('output_type',['txt_simple'])
    
    # results folder for option
    consts.result_path = f'{results_folder}/{option}'

    # create results folder
    if not os.path.exists(consts.result_path):
        os.mkdir(consts.result_path)
    else:
        # clear results folder
        for file in os.listdir(consts.result_path):
            if not os.path.isdir(f'{consts.result_path}/{file}'):
                os.remove(f'{consts.result_path}/{file}')
            else:
                shutil.rmtree(f'{consts.result_path}/{file}')

    # copy option to results folder
    json.dump(options,open(f'{consts.result_path}/pipeline_options.json','w',encoding='utf-8'),indent=4)

    return pipeline_args


def compare_results(results_folder:str,option:str,ground_truth_file:str=None,partial_ground_truth_file:str=None,logs:bool=False)->dict:
    '''Compare results with ground truth'''

    comparison = {'ground_truth':{},'partial_ground_truth':{},'ocr':{},'text':{}}

    
    if logs:
        print('Comparing results with ground truth for option:',option)

    # load metadata
    metadata = json.load(open(f'{results_folder}/metadata.json','r'))


    if logs:
        print('Checking OCR results...')

    # check ocr results
    ocr_results_path = metadata['ocr_results_path']
    ocr_results = OCR_Tree(ocr_results_path)
    ocr_totaltext_conf, ocr_number_text_blocks = ocr_results.average_conf(level=5)
    ocr_average_text_conf = ocr_totaltext_conf / ocr_number_text_blocks
    ocr_text_blocks = [t for t in ocr_results.get_boxes_level(level=5)]

    comparison['ocr'] = {
        'average_text_conf': ocr_average_text_conf,
        'number_text_blocks': len(ocr_text_blocks)
    }

    if not ground_truth_file and not partial_ground_truth_file:
        return comparison
    

    # check text results
    text_results_path = metadata['output']['txt_simple']
    text_result = open(text_results_path,'r',encoding='utf-8').read()

    comparison['text'] = {}

    ## compare with complete ground truth
    if ground_truth_file:

        if logs:
            print('Checking text results with ground truth...')

        ### overall similarity using cosine similarity
        documents = [open(ground_truth_file,'r',encoding='utf-8').read(),text_result]
        tfidf = TfidfVectorizer().fit_transform(documents)
        pairwise_similarity = tfidf * tfidf.T
        similarity = pairwise_similarity.toarray()[0][1]

        comparison['text']['ground_truth_similarity'] = similarity

        comparison['ground_truth']['word_count'] = len([w for w in text_result.split() if w.strip()])

    ## compare with partial ground truth
    if partial_ground_truth_file:
        if logs:
            print('Checking text results with partial ground truth...')

        partial_ground_truth = open(partial_ground_truth_file,'r',encoding='utf-8').readlines()
        partial_ground_truth = [p.strip() for p in partial_ground_truth if p.strip()]
        
        text_results_lines = [line.strip() for line in text_result.splitlines()]

        ### check if lines in partial ground truth are in text result
        total_hits = 0
        found_lines = []
        for line in partial_ground_truth:
            if line in text_results_lines:
                total_hits += 1
                found_lines.append(line)

        comparison['text']['partial_ground_truth_hit_rate'] = total_hits/len(partial_ground_truth)
        comparison['text']['partial_ground_truth_hit_count'] = total_hits
        comparison['partial_ground_truth']['number_lines'] = len(partial_ground_truth)

        ### check if lines found are in the correct order in text
        if found_lines:
            n_correct_order = 0

            #### get line indexes in text
            line_text_indexes = {}
            for i,line in enumerate(text_results_lines):
                if line in found_lines:
                    line_text_indexes[hashlib.md5(line.encode('utf-8')).hexdigest()] = i

            for line in found_lines:
                line_index = line_text_indexes[hashlib.md5(line.encode('utf-8')).hexdigest()]
                true_line_index = found_lines.index(line)

                ##### check if line is in correct order relative to other lines
                correct_order = True
                for other_line in found_lines:
                    other_line_index = line_text_indexes[hashlib.md5(other_line.encode('utf-8')).hexdigest()]
                    true_other_line_index = found_lines.index(other_line)
                    if line == other_line:
                        continue
                    elif (true_line_index < true_other_line_index and line_index > other_line_index) or (true_line_index > true_other_line_index and line_index < other_line_index):
                        correct_order = False
                        break

                if correct_order:
                    n_correct_order += 1

            comparison['text']['partial_ground_truth_matched_lines_correct_order_ratio'] = n_correct_order/len(found_lines)
            comparison['text']['partial_ground_truth_matched_lines_correct_order_count'] = n_correct_order


    return comparison
                    

                

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
    
    if not os.path.exists(f'{calibration_folder}/ground_truth.txt') and not os.path.exists(f'{calibration_folder}/partial_ground_truth.txt'):
        print(f'No ground truth files found in {calibration_folder}')
        return
    
    ground_truth_path = f'{calibration_folder}/ground_truth.txt' if os.path.exists(f'{calibration_folder}/ground_truth.txt') else None
    partial_ground_truth_path = f'{calibration_folder}/partial_ground_truth.txt' if os.path.exists(f'{calibration_folder}/partial_ground_truth.txt') else None
    
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

            # compare results
            option_results_folder = f'{results_folder}/{option}'
            target_dir = path_to_id(target_image)
            results = compare_results(f'{option_results_folder}/{target_dir}',option,ground_truth_path,partial_ground_truth_path,logs)

            # save results
            with open(f'{option_results_folder}/results.json','w',encoding='utf-8') as f:
                json.dump(results,f,indent=4)




    

