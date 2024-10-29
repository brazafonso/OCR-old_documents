import json
import os
import re
import shutil
import sys
import hashlib
import jellyfish
import OSDOCR.aux_utils.consts as consts
from argparse import Namespace
from OSDOCR.aux_utils.misc import path_to_id
from OSDOCR.aux_utils.parse_args import CustomAction_skip_method
from OSDOCR.parse_args import process_args,preprocessing_methods,posprocessing_methods
from OSDOCR.pipeline import run_target
from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.ocr_tree_module.ocr_tree_analyser import extract_articles
from OSDOCR.preprocessing.image import identify_document_images
from OSDOCR.output_module.text import fix_hifenization
from sklearn.feature_extraction.text import TfidfVectorizer
from document_image_utils.image import divide_columns



file_path = os.path.dirname(os.path.realpath(__file__))


def prepare_pipeline_config(pipeline_config:str,target_image:str,default_args:str,results_folder:str,
                            reuse_results:bool=False,logs:bool=False,debug:bool=False)->Namespace:
    '''Prepare pipeline config for calibration'''

    # load pipeline args
    pipeline_args = Namespace(**vars(default_args))
    options = json.load(open(f'{pipeline_config}','r'))
    for key in options:
        pipeline_args.__setattr__(key,options[key])

    skip_methods = []
    if pipeline_args.__getattribute__('skip_method'):
        skip_methods = pipeline_args.__getattribute__('skip_method')
        action = CustomAction_skip_method('skip_method','skip_method')
        action(None,pipeline_args,skip_methods,None)
        # need to remove 'output' from skip_method
        if 'output' in pipeline_args.skip_method:
            pipeline_args.skip_method.remove('output')

    pipeline_args.__setattr__('logs',logs)
    pipeline_args.__setattr__('debug',debug)
    pipeline_args.__setattr__('target',target_image)
    output_type = pipeline_args.__getattribute__('output_type')
    if not output_type:
        output_type = ['txt_simple']
    else:
        output_type += ['txt_simple']
    
    pipeline_args.__setattr__('output_type',output_type)
    
    # results folder for config
    consts.result_path = results_folder

    # create results folder
    if not os.path.exists(consts.result_path):
        os.mkdir(consts.result_path)
    elif not reuse_results and os.path.exists(f'{consts.result_path}/results.json'):
        # clear results folder
        for file in os.listdir(consts.result_path):
            if not os.path.isdir(f'{consts.result_path}/{file}'):
                os.remove(f'{consts.result_path}/{file}')
            else:
                shutil.rmtree(f'{consts.result_path}/{file}')

    # copy config to results folder
    json.dump(options,open(f'{consts.result_path}/pipeline_config.json','w',encoding='utf-8'),indent=4)

    return pipeline_args


def compare_results(results_folder:str,option:str,
                    ground_truth_file:str=None,partial_ground_truth_file:str=None,expected_results_path:str=None,
                    option_args:Namespace=None,logs:bool=False)->dict:
    '''Compare results with ground truth.
    
    Will gather results about OCR output, text output and image output and compare with available ground truth.'''

    comparison = {
        'ground_truth':{},
        'partial_ground_truth':{},
        'image':{},
        'validation':{
            'ocr':{},
            'text':{},
            'image':{},
        }
    }

    
    if logs:
        print('Comparing results with ground truth for option:',option)

    # load metadata
    metadata = json.load(open(f'{results_folder}/metadata.json','r'))


    if logs:
        print('Checking OCR results...')

    # check ocr results
    ocr_results_path = metadata['ocr_results_path']
    ocr_results = OCR_Tree(ocr_results_path)
    ocr_totaltext_conf, ocr_number_text_blocks = ocr_results.conf_sum(level=5)
    ocr_average_text_conf = ocr_totaltext_conf / ocr_number_text_blocks
    ocr_text_blocks_2 = [t for t in ocr_results.get_boxes_level(level=2)]
    ocr_text_blocks_5 = [t for t in ocr_results.get_boxes_level(level=5)]


    comparison['validation']['ocr'] = {
        'average_text_conf': ocr_average_text_conf,
        'number_text_blocks' : len(ocr_text_blocks_2),
        'number_word_blocks': len(ocr_text_blocks_5),
    }

    if not ground_truth_file and not partial_ground_truth_file:
        return comparison
    

    # check text results
    text_results_path = metadata['output']['txt_simple']
    text_result = open(text_results_path,'r',encoding='utf-8').read()
    ## clean text
    ### leave only words; reduce to lower case; reduce whitespaces
    text_result = re.sub(r'[^\w\d\s]',' ',text_result)
    text_result = re.sub(r'[ \t\r\v\f]+',' ',text_result)
    text_result = text_result.lower()
    text_result = fix_hifenization(text_result)


    ## compare with complete ground truth
    if ground_truth_file:

        if logs:
            print('Checking text results with ground truth...')

        ### overall similarity using cosine similarity
        gt_text = open(ground_truth_file,'r',encoding='utf-8').read()
        #### clean text
        ##### leave only words; reduce to lower case; reduce whitespaces
        gt_text = re.sub(r'[^\w\d\s]',' ',gt_text)
        gt_text = re.sub(r'[ \t\r\v\f]+',' ',gt_text)
        gt_text = gt_text.lower()
        gt_text = fix_hifenization(gt_text)

        documents = [gt_text,text_result]
        tfidf = TfidfVectorizer().fit_transform(documents)
        pairwise_similarity = tfidf * tfidf.T
        similarity = pairwise_similarity.toarray()[0][1]

        comparison['validation']['text']['ground_truth_similarity'] = similarity

        comparison['ground_truth']['word_count'] = len([w for w in text_result.split() if w.strip()])

        ### unique words count
        gt_words = gt_text.replace('\n',' ').split()
        gt_words_count = {}
        for w in gt_words:
            if w in gt_words_count:
                gt_words_count[w] += 1
            else:
                gt_words_count[w] = 1
        text_words = text_result.replace('\n',' ').split()
        text_words_count = {}
        for w in text_words:
            if w in text_words_count:
                text_words_count[w] += 1
            else:
                text_words_count[w] = 1
        
        ### compare unique words
        accuracy_ratios = []
        unique_words_count = 0
        for w in gt_words_count:
            if w in text_words_count:
                accuracy_ratios.append(text_words_count[w] / gt_words_count[w])
                unique_words_count += 1
            else:
                accuracy_ratios.append(0)

        accuracy = sum(accuracy_ratios) / len(accuracy_ratios)
        comparison['validation']['text']['words_accuracy'] = accuracy
        comparison['validation']['text']['unique_words_ratio'] = unique_words_count / len(gt_words_count)

    ## compare with partial ground truth
    if partial_ground_truth_file:
        if logs:
            print('Checking text results with partial ground truth...')

        partial_ground_truth = open(partial_ground_truth_file,'r',encoding='utf-8').read()
        ### clean text
        ### leave only words; reduce to lower case; reduce whitespaces
        partial_ground_truth = re.sub(r'[^\w\d\s]',' ',partial_ground_truth)
        partial_ground_truth = re.sub(r'[ \t\r\v\f]+',' ',partial_ground_truth)
        partial_ground_truth = partial_ground_truth.lower()
        partial_ground_truth = fix_hifenization(partial_ground_truth)
        partial_ground_truth = partial_ground_truth.splitlines()
        partial_ground_truth = [p.strip() for p in partial_ground_truth if p.strip()]
        
        text_results_lines = [line.strip() for line in text_result.splitlines()]

        ### check if lines in partial ground truth are in text result (90% similarity)
        total_hits = 0
        found_lines = []
        for line in partial_ground_truth:
            found = False
            for l in text_results_lines:
                if jellyfish.jaro_winkler_similarity(line, l) >= 0.9:
                    total_hits += 1
                    found_lines.append((line,l))
                    found = True
                    break

            if found:
                continue


        comparison['validation']['text']['partial_ground_truth_hit_rate']  = total_hits/len(partial_ground_truth)
        comparison['validation']['text']['partial_ground_truth_hit_count'] = total_hits
        comparison['partial_ground_truth']['number_lines'] = len(partial_ground_truth)
        comparison['validation']['text']['partial_ground_truth_correct_order_ratio'] = 0
        comparison['validation']['text']['partial_ground_truth_matched_lines_correct_order_ratio'] = 0
        comparison['validation']['text']['partial_ground_truth_matched_lines_correct_order_count'] = 0
        ### check if lines found are in the correct order in text
        if found_lines:
            n_correct_order = 0

            #### get line indexes in text
            line_text_indexes = {}
            for i,line in enumerate(text_results_lines):
                for j,pgt_line in enumerate(found_lines):
                    if line == pgt_line[1]:
                        line_text_indexes[hashlib.md5(pgt_line[0].encode('utf-8')).hexdigest()] = i

            for pair in found_lines:
                pgt_line,line = pair
                line_index = line_text_indexes[hashlib.md5(pgt_line.encode('utf-8')).hexdigest()]
                true_line_index = found_lines.index(pair)

                ##### check if line is in correct order relative to other lines
                correct_order = True
                for other_pair in found_lines:
                    pgt_other_line,other_line = other_pair
                    other_line_index = line_text_indexes[hashlib.md5(pgt_other_line.encode('utf-8')).hexdigest()]
                    true_other_line_index = found_lines.index(other_pair)
                    if line == other_line:
                        continue
                    elif (true_line_index < true_other_line_index and line_index > other_line_index) or \
                        (true_line_index > true_other_line_index and line_index < other_line_index):
                        correct_order = False
                        break

                if correct_order:
                    n_correct_order += 1

            comparison['validation']['text']['partial_ground_truth_correct_order_ratio'] = total_hits/len(partial_ground_truth)
            comparison['validation']['text']['partial_ground_truth_matched_lines_correct_order_ratio'] = n_correct_order/len(found_lines)
            comparison['validation']['text']['partial_ground_truth_matched_lines_correct_order_count'] = n_correct_order


    ## compare with other metrics
    if expected_results_path:

        if logs:
            print('Checking text results with expected results...')

        expected_results = json.load(open(expected_results_path,'r',encoding='utf-8'))
        metadata = json.load(open(f'{results_folder}/metadata.json','r',encoding='utf-8'))
        target_path = metadata['target_path']

        # compare number of columns
        if 'number_columns' in expected_results:
            number_of_columns = len(divide_columns(target_path))
            comparison['validation']['image']['number_columns'] = number_of_columns
            comparison['image']['number_columns'] = expected_results['number_columns']

        if 'number_images' in expected_results:
            identify_images_Flag = 'remove_document_images' not in option_args.skip_method
            n_images = 0
            if identify_images_Flag:
                method = option_args.remove_document_images[0]
                old_document = option_args.target_old_document
                n_images = len(identify_document_images(target_path,method=method,old_document=old_document,conf=0.5,logs=option_args.debug))
            comparison['validation']['image']['number_images'] = n_images
            comparison['image']['number_images'] = expected_results['number_images']

        if 'number_articles' in expected_results:
            ocr_results = OCR_Tree(metadata['ocr_results_path'])
            _,articles = extract_articles(target_path,ocr_results,ignore_delimiters=option_args.ignore_delimiters)
            comparison['validation']['image']['number_articles'] = len(articles)
            comparison['image']['number_articles'] = expected_results['number_articles']

    return comparison
                    

def get_preprocessing_options(pipeline_config_json:dict)->dict:
    '''Get preprocessing options'''
    preprocessing_options = {}

    if 'skip_method' in pipeline_config_json:
        skip_methods = [method for method in pipeline_config_json['skip_method'] if method in preprocessing_methods]
        if 'all' in pipeline_config_json['skip_method']:
            skip_methods+=['all']

        preprocessing_options['skip_method'] = skip_methods

    preprocessing_args = ['target_type','target_old_document','target_dpi','target_dimensions',
                          'fix_rotation','upscaling_image','denoise_image']

    for arg in preprocessing_args:
        if arg in pipeline_config_json:
            preprocessing_options[arg] = pipeline_config_json[arg]

    return preprocessing_options

def config_preprocessing_score(results:dict,logs:bool=False)->float:
    '''Calculate config preprocessing score'''

    if logs:
        print('Config preprocessing score...')

    preprocessing_score = 0
    
    # average text conf (max score is 5)
    text_conf = results['validation']['ocr']['average_text_conf']

    preprocessing_score += 5 * (text_conf/100)

    # number of columns (max score is 3)
    if 'image' in results and 'number_columns' in results['image']:
        expected_columns = results['image']['number_columns']
        identified_columns = results['validation']['image']['number_columns']

        preprocessing_score += 3 - (expected_columns-identified_columns if expected_columns-identified_columns >= 0 else 3)

    # number of images (max score is 2)
    if 'image' in results and 'number_images' in results['image']:
        expected_images = results['image']['number_images']
        identified_images = results['validation']['image']['number_images']

        preprocessing_score += 2 - (expected_images-identified_images if expected_images-identified_images >= 0 else 2)

    # GT tests
    if 'ground_truth' in results:
        # GT similarity (max score is 4)
        preprocessing_score += 4 * results['validation']['text']['ground_truth_similarity']

        # GT word count (max score is 2)
        expected_words = results['ground_truth']['word_count']
        identified_words = results['validation']['ocr']['number_text_blocks']
        preprocessing_score += 2 * min(expected_words,identified_words)/max(expected_words,identified_words)

        # GT word accuracy (max score is 4)
        preprocessing_score += 4 * results['validation']['text']['words_accuracy']

        # GT unique word count ratio (max score is 2)
        preprocessing_score += 2 * results['validation']['text']['unique_words_ratio']

    # Partial GT tests
    if 'partial_ground_truth' in results:
        # partial GT hit rate (max score is 3)
        preprocessing_score += 3 * results['validation']['text']['partial_ground_truth_hit_rate']


    return preprocessing_score


def config_posprocessing_score(results:dict,logs:bool=False)->float:
    '''Calculate config posprocessing score'''

    if logs:
        print('Config posprocessing score...')

    posprocessing_score = 0

    # number of articles (max score is 5)
    if 'image' in results and 'number_articles' in results['image']:
        expected_articles = results['image']['number_articles']
        identified_articles = results['validation']['image']['number_articles']

        posprocessing_score += 5 - (expected_articles-identified_articles if expected_articles-identified_articles >= 0 else 5)

    # Partial GT tests
    if 'partial_ground_truth' in results:
        # correct order ration (max score is 4)
        posprocessing_score += 4 * results['validation']['text']['partial_ground_truth_matched_lines_correct_order_ratio']


    return posprocessing_score



def get_posprocessing_options(pipeline_config_json:dict)->dict:
    '''Get posprocessing options'''
    posprocessing_options = {}

    if 'skip_method' in pipeline_config_json:
        skip_methods = [method for method in pipeline_config_json['skip_method'] if method in posprocessing_methods]
        if 'all' in pipeline_config_json['skip_method']:
            skip_methods+=['all']

        posprocessing_options['skip_method'] = skip_methods

    posprocessing_args = ['text_confidence','ignore_delimiters','tesseract_config']

    for arg in posprocessing_args:
        if arg in pipeline_config_json:
            posprocessing_options[arg] = pipeline_config_json[arg]

    return posprocessing_options




def choose_best_pipeline_options(results_folder:str,logs:bool=False,debug:bool=False)->dict:
    '''Choose best pipeline options. Compares all pipeline configs results and for each result choose the best corresponding pipeline options.
        
        Args:
            - results_folder: path to results folder
            - logs: whether to print logs
            - debug: whether to print debug logs'''
    
    if logs:
        print('Choosing best pipeline options...')


    best_pipeline_options = {}
    best_preprocessing_score = 0
    best_posprocessing_score = 0
    for pipeline_config in os.listdir(results_folder):
        if not os.path.isdir(f'{results_folder}/{pipeline_config}'):
            continue
        
        config_result_dir = f'{results_folder}/{pipeline_config}'
        results_json = json.load(open(f'{config_result_dir}/results.json','r',encoding='utf-8'))
        pipeline_config_json = json.load(open(f'{config_result_dir}/pipeline_config.json','r',encoding='utf-8'))

        preprocessing_options = get_preprocessing_options(pipeline_config_json)
        posprocessing_options = get_posprocessing_options(pipeline_config_json)

        # default
        if not best_pipeline_options:
            best_pipeline_options['config'] = pipeline_config_json
            best_pipeline_options['results'] = results_json
            best_preprocessing_score = results_json['score']['preprocessing']
            best_posprocessing_score = results_json['score']['posprocessing']
            continue

        # compare

        ## overall preprocessing
        preprocessing_score = results_json['score']['preprocessing']

        ### save config with best preprocessing score
        if preprocessing_score > best_preprocessing_score:
            # update best preprocessing options
            for key in preprocessing_options:
                if key != 'skip_method':
                    best_pipeline_options['config'][key] = preprocessing_options[key]
                else:
                    current_skip_methods = best_pipeline_options['config'][key]
                    # remove current preprocessing methods
                    current_skip_methods = [method for method in current_skip_methods if method not in preprocessing_methods]
                    # add new best preprocessing methods
                    best_pipeline_options['config'][key] = current_skip_methods + preprocessing_options[key]

            # update best preprocessing score
            best_preprocessing_score = preprocessing_score

        ## overall posprocessing
        posprocessing_score = results_json['score']['posprocessing']

        ### save config with best posprocessing score
        if posprocessing_score > best_posprocessing_score:
            # update best posprocessing options
            for key in posprocessing_options:
                if key != 'skip_method':
                    best_pipeline_options['config'][key] = posprocessing_options[key]
                else:
                    current_skip_methods = best_pipeline_options['config'][key]
                    # remove current posprocessing methods
                    current_skip_methods = [method for method in current_skip_methods if method not in posprocessing_methods]
                    # add new best posprocessing methods

            # update best posprocessing score
            best_posprocessing_score = posprocessing_score


        ## option identify document images (target_old_document)
        ### compare image identification
        if best_pipeline_options['results']['score']['image_identification'] < results_json['score']['image_identification']:
            if 'target_old_document' in pipeline_config_json:
                best_pipeline_options['config']['target_old_document'] = pipeline_config_json['target_old_document']

    return best_pipeline_options['config']


def score_config(pipeline_results:dict,logs:bool=False,debug:bool=False)->dict:
    '''Score single pipeline config. 
    
    Scores results of preprocessing, posprocessing and some other metrics.
    
    Returns results in form of a dict.'''

    results = {}

    ## preprocessing
    results['preprocessing'] = config_preprocessing_score(pipeline_results,logs=logs)

    ## posprocessing
    results['posprocessing'] = config_posprocessing_score(pipeline_results,logs=logs)

    ## document image identification
    expected_images = pipeline_results['image']['number_images']
    identified_images = pipeline_results['validation']['image']['number_images']
    results['image_identification'] = min(expected_images,identified_images) / max(expected_images,identified_images) if expected_images > 0 else 0

    if debug:
        print(results)

    return results



def run_test_config(config_path:str,calibration_folder:str,results_folder:str,
                    reuse_results:bool=False,logs:bool=False,debug:bool=False):
    '''Run test in a single pipeline config.'''

    # get target image
    target_image = None
    files = os.listdir(calibration_folder)
    for file in files:
        if 'target_image' in file:
            target_image = f'{calibration_folder}/{file}'
            break

    if not target_image:
        print(f'No target image found in {calibration_folder}')
        return
    
    # minimum required GT files
    if not os.path.exists(f'{calibration_folder}/ground_truth.txt') and not os.path.exists(f'{calibration_folder}/partial_ground_truth.txt'):
        print(f'No ground truth files found in {calibration_folder}')
        return
    
    # get existing GT files
    ground_truth_path = f'{calibration_folder}/ground_truth.txt' if os.path.exists(f'{calibration_folder}/ground_truth.txt') else None
    partial_ground_truth_path = f'{calibration_folder}/partial_ground_truth.txt' if os.path.exists(f'{calibration_folder}/partial_ground_truth.txt') else None
    expected_results_path = f'{calibration_folder}/expected_results.json' if os.path.exists(f'{calibration_folder}/expected_results.json') else None


    # create results folder
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)


    config_name = os.path.basename(config_path)

    # default args for pipeline
    sys.argv = [sys.argv[0]]
    default_args:Namespace = process_args()

    pipeline_args = prepare_pipeline_config(config_path,target_image,
                                                    default_args,results_folder,reuse_results,logs,debug)
        
    # run pipeline
    print(f'''
        ================================
        ||      Running pipeline      ||
        ================================
        || Config: {config_name[:19]}{' '*(19-len(config_name[:19]))}||
        ================================''')
    
    run_target(target_image,pipeline_args)

    # compare results
    target_dir = path_to_id(target_image)
    results = compare_results(f'{results_folder}/{target_dir}',config_name,
                                ground_truth_path,partial_ground_truth_path,expected_results_path,
                                pipeline_args,logs)
    
    score = score_config(results,logs,debug)

    results['score'] = score

    # save results
    with open(f'{results_folder}/results.json','w',encoding='utf-8') as f:
        json.dump(results,f,indent=4)
                

def run_calibrate(calibration_folder:str,pipeline_configs_path:str,results_folder:str=None,reuse_results:bool=False,logs:bool=False,debug:bool=False)->dict:
    '''Find the best calibration for OSDOCR using prepared ground truth data.
        Possible files:
        - target_image.<extension>
        - ground_truth.txt
        - parcial_ground_truth.txt
        - expected_results.json
    '''

    if logs:
        print('Running calibration...')
        print('Calibration folder:',calibration_folder)

    # check if calibration folder is valid
    if not os.path.exists(calibration_folder):
        print(f'Calibration folder not found: {calibration_folder}')
        return

    # modify results folder
    if not results_folder:
        results_folder = f'{calibration_folder}/results'
    

    # create results folder
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)



    # for each pipeline option
    ## run pipeline and compare results with ground truth
    ## save comparison results
    pipeline_configs = []
    if not os.path.exists(pipeline_configs_path):
        print(f'Pipeline configs not found: {pipeline_configs_path}')
        return
    elif not os.path.isdir(pipeline_configs_path):
        pipeline_configs = [os.path.basename(pipeline_configs_path)]
        pipeline_configs_path = os.path.split(pipeline_configs_path)[0]
    else:
        pipeline_configs = os.listdir(pipeline_configs_path)

    for config in sorted(pipeline_configs):
        if config.endswith('.json'):
            config_path = f'{pipeline_configs_path}/{config}'
            config_results_folder = f'{results_folder}/{config}'
            run_test_config(config_path,calibration_folder,config_results_folder,reuse_results,logs,debug)

            
    # compare all results and create best pipeline config
    best_config = choose_best_pipeline_options(results_folder,logs)

    # save best config
    with open(f'{calibration_folder}/best_config.json','w',encoding='utf-8') as f:
        json.dump(best_config,f,indent=4)

    return best_config

    




    

