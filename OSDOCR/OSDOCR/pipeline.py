
import argparse
from aux_utils.parse_args import *
from aux_utils.misc import *
from aux_utils import consts
from ocr_tree_module.ocr_tree import *
from ocr_tree_module.ocr_tree_analyser import *
from ocr_tree_module.ocr_tree_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article
from preprocessing.image import *


def save_articles(articles:list,results_path:str,args:argparse.Namespace):
    '''Save articles. Type of output is defined in args : markdown, html, txt'''
    output_types = args.output_type

    if 'markdown' in output_types:
        with open(f'{results_path}/articles.txt','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article)
                f.write(article.pretty_print())
                f.write('\n')

        with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article)
                f.write(article.to_md())
                f.write('\n'+'==='*40 + '\n')

    if 'html' in output_types:
        # TODO
        pass

    if 'txt' in output_types:
        # TODO
        pass

def extract_articles(target:str,ocr_results:OCR_Tree,results_path:str,args:argparse.Namespace):
    '''Extract articles from image'''

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


    # isolate articles
    articles = graph_isolate_articles(t_graph,order_list=order_list)
    if args.debug:
        articles_img = draw_articles(articles,target)
        cv2.imwrite(f'{results_path}/articles.png',articles_img)

    # draw reading order
    if args.debug:
        # change ids to order
        order_map = {order_list[i]:i for i in range(len(order_list))}
        ocr_results.change_ids(order_map)

        image = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/reading_order.png',image)


    # save articles
    save_articles(articles,results_path,args)


    


def image_preprocess(target:str,args:argparse.Namespace):
    '''Preprocess image'''
    if args.debug:
        print('IMAGE PREPROCESS')
    processed_image_path = os.path.dirname(target) +f'/{os.path.basename(target)}' + '_processed.png'

    # save image
    og_img = cv2.imread(target)
    cv2.imwrite(processed_image_path,og_img)


    # image distortion
    if 'fix_distortions' not in args.skip_method:
        # TODO
        pass

    # noise removal
    if 'noise_removal' not in args.skip_method:
        if args.debug:
            print('NOISE REMOVAL')

        if args.denoise_image:
            method = args.denoise_image[0]
            tmp_denoised_image_path = f'{consts.tmp_path}/OSDOcr_image_denoised_tmp.png'

            if method == 'waifu2x':
                method_config = None
                if len(args.denoise_image) > 1:
                    method_config = int(args.denoise_image[1])

                if method_config:
                    run_waifu2x(processed_image_path,method='noise',noise_level=method_config,result_image_path=tmp_denoised_image_path,log=args.debug) 
                else:
                    run_waifu2x(processed_image_path,method='noise',result_image_path=tmp_denoised_image_path,log=args.debug)

                denoised_img = cv2.imread(tmp_denoised_image_path)
                cv2.imwrite(processed_image_path,denoised_img)
            


    # blur removal
    if 'blur_removal' not in args.skip_method:
        # TODO
        pass

    # image upscaling
    if 'image_upscaling' not in args.skip_method:
        if args.debug:
            print('IMAGE UPSCALING')

        if args.upscaling_image:
            method = args.upscaling_image[0]
            if method == 'waifu2x':
                tmp_upsacled_image_path = f'{consts.tmp_path}/OSDOcr_image_upscaled_tmp.png'
                method_config = None
                if len(args.upscaling_image) > 1:
                    method_config = args.upscaling_image[1]

                if method_config:
                    run_waifu2x(processed_image_path,result_image_path=tmp_upsacled_image_path,method=method_config,log=args.debug) 
                else:
                    run_waifu2x(processed_image_path,result_image_path=tmp_upsacled_image_path,log=args.debug)

                upscaled_img = cv2.imread(tmp_upsacled_image_path)
                cv2.imwrite(processed_image_path,upscaled_img)


    # lightning correction
    if 'lightning_correction' not in args.skip_method:
        # TODO
        pass


    # image rotation
    ## not used by default
    if args.fix_rotation and 'auto_rotate' not in args.skip_method:
        rotate_img = rotate_image(processed_image_path,direction=args.fix_rotation,debug=args.debug)
        cv2.imwrite(processed_image_path,rotate_img)

    return processed_image_path


def run_target_hocr(target:str,args:argparse.Namespace):
    '''Run pipeline for single OCR target. TODO'''
    return None


def run_target_image(target:str,results_path:str,args:argparse.Namespace):
    '''Run pipeline for single image.
    - Image preprocessing
    - OCR
    - Convert to ocr_tree

    Return ocr_tree and image path (in case of preprocessing)
    '''
    
    # preprocess image
    if 'image_preprocess' not in args.skip_method:
        target = image_preprocess(target,args)
            
    run_tesseract(target,results_path=results_path,opts=args.tesseract_config,logs=args.debug)

    # get results
    return [OCR_Tree(f'{results_path}/result.json'),target]


def clean_ocr(ocr_results:OCR_Tree,target:str,results_path:str,logs:bool=False):
    '''Clean ocr_tree'''
    ocr_results = bound_box_fix(ocr_results,2,None)

    # save results

    ## check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target,[2],id=True)
    cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/fixed/result_fixed.csv')

    return ocr_results


def unite_ocr_blocks(ocr_results:OCR_Tree,target:str,results_path:str,logs:bool=False):
    '''Unite ocr_tree'''
    ocr_results = unite_blocks(ocr_results)

    ## check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    result_dict_file = open(f'{results_path}/fixed/result_united.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target,[2],id=True)
    cv2.imwrite(f'{results_path}/fixed/result_united.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/fixed/result_united.csv')

    return ocr_results

def run_target(target:str,args:argparse.Namespace):
    '''Run pipeline for single target.
    
    - A : image
    1. Analyze target 
    2. Preprocess image
    3. OCR
    4. Convert to ocr_tree


    - B : hOCR
    1. Convert to ocr_tree

    - General
    1. Clean ocr_tree
    2. Analyse ocr_tree
    3. Extract articles
    4. Save articles

    '''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    if args.debug:
        print(f'Processing: {target}')
        print(f'Options: {args}')

    image_target = True
    # check if target is hOCR
    if target.endswith('.hocr'):
        image_target = False

    ocr_results = None

    if not image_target:
        ocr_results = run_target_hocr(target,args)
    else:
        force_ocr = args.force_ocr
        # check if target has been ocrd before or force
        if force_ocr or not os.path.exists(f'{consts.result_path}/{path_to_id(target)}/result.json'):
            ocr_results,target = run_target_image(target,results_path,args)
        else:
            if os.path.exists(f'{consts.result_path}/{path_to_id(target)}/result.json'):
                ocr_results = OCR_Tree(f'{consts.result_path}/{path_to_id(target)}/result.json')
            else:
                print('File not found: ',f'{consts.result_path}/{path_to_id(target)}/result.json')
                print('Please run ocr first')
                sys.exit(1)

    # id boxes
    ocr_results.id_boxes([2])

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/result_id_0.png',id_img)

    # clean ocr_results
    if 'clean_ocr' not in args.skip_method:
        if args.debug:
            print('CLEAN OCR')
        ocr_results = clean_ocr(ocr_results,target,results_path,logs=args.debug) 

    # categorize boxes
    ocr_results = categorize_boxes(ocr_results)

    # unite same type blocks
    if 'unite_blocks' not in args.skip_method:
        if args.debug:
            print('UNITE BLOCKS')
        ocr_results = unite_ocr_blocks(ocr_results,target,results_path,logs=args.debug)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/result_id_2.png',id_img)

    if args.debug:
        # analyse ocr_results
        results = analyze_text(ocr_results)
        print(results)

    # extract articles
    if 'extract_articles' not in args.skip_method:
        if args.debug:
            print('EXTRACT ARTICLES')
        extract_articles(target,ocr_results,results_path,args)