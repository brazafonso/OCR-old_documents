
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


def save_articles(articles:list[OCR_Tree],o_taget:str,results_path:str,args:argparse.Namespace):
    '''Save articles. Type of output is defined in args : markdown, html, txt'''
    output_types = args.output_type
    min_text_conf = args.text_confidence
    metadata = get_target_metadata(o_taget)

    if 'markdown' in output_types:

        with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article,min_text_conf)
                f.write(article.to_md())
                f.write('\n'+'==='*40 + '\n')

        metadata['output']['markdown'] = f'{results_path}/articles.md'

    if 'html' in output_types:
        # TODO
        pass

        metadata['output']['html'] = f'{results_path}/articles.html'

    if 'txt' in output_types:
        # TODO
        pass

        metadata['output']['txt'] = f'{results_path}/articles.txt'

    if 'txt_simple' in output_types:
        with open(f'{results_path}/articles.txt','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article,min_text_conf)
                f.write(article.to_txt())

        metadata['output']['txt_simple'] = f'{results_path}/articles.txt'

    save_target_metadata(o_taget,metadata)

def extract_articles(o_target:str,ocr_results:OCR_Tree,results_path:str,args:argparse.Namespace):
    '''Extract articles from image'''

    metadata = get_target_metadata(o_target)
    target_img_path = metadata['target_path']

    # get journal template
    ## leaves only body
    image_info = get_image_info(target_img_path)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results,area=columns_area,ignore_delimiters=args.ignore_delimiters)
    order_list = sort_topologic_order(t_graph,sort_weight=True)


    # isolate articles
    articles = graph_isolate_articles(t_graph,order_list=order_list,logs=args.debug)
    if args.debug:
        articles_img = draw_articles(articles,target_img_path)
        cv2.imwrite(f'{results_path}/articles.png',articles_img)

    # draw reading order
    if args.debug:
        # change ids to order
        order_map = {order_list[i]:i for i in range(len(order_list))}
        ocr_results.change_ids(order_map)

        image = draw_bounding_boxes(ocr_results,target_img_path,[2],id=True)
        cv2.imwrite(f'{results_path}/reading_order.png',image)


    # save articles
    save_articles(articles,o_target,results_path,args)


    


def image_preprocess(o_target:str,results_path:str,args:argparse.Namespace):
    '''Preprocess image'''
    if args.logs:
        print('IMAGE PREPROCESS')
    processed_image_path = f'{results_path}/processed.png'

    metadata = get_target_metadata(o_target)
    metadata['target_path'] = processed_image_path
    

    # save image
    og_img = cv2.imread(o_target)
    cv2.imwrite(processed_image_path,og_img)


    # image distortion
    if 'fix_distortions' not in args.skip_method:
        # TODO
        pass

    # noise removal
    if 'noise_removal' not in args.skip_method:
        if args.logs:
            print('NOISE REMOVAL')

        if args.denoise_image:
            method = args.denoise_image[0]
            tmp_denoised_image_path = f'{consts.tmp_path}/OSDOcr_image_denoised_tmp.png'
            denoised = False

            if method == 'waifu2x':
                method_config = None
                if len(args.denoise_image) > 1:
                    method_config = int(args.denoise_image[1])

                if method_config:
                    run_waifu2x(processed_image_path,method='noise',noise_level=method_config,result_image_path=tmp_denoised_image_path,logs=args.debug) 
                else:
                    run_waifu2x(processed_image_path,method='noise',result_image_path=tmp_denoised_image_path,logs=args.debug)

                denoised_img = cv2.imread(tmp_denoised_image_path)
                cv2.imwrite(processed_image_path,denoised_img)
                denoised = True

            if denoised:
                # create step img
                step_img_path = f'{results_path}/noise_removal.png'
                cv2.imwrite(step_img_path,denoised_img)

                metadata['transformations'].append(('noise_removal',method,method_config))
            
    # image rotation
    if args.fix_rotation and 'auto_rotate' not in args.skip_method:
        if args.logs:
            print('FIX ROTATION')

        rotate_img = rotate_image(processed_image_path,direction=args.fix_rotation,
                                  auto_crop=True,debug=args.debug)
        cv2.imwrite(processed_image_path,rotate_img)

        # create step img
        step_img_path = f'{results_path}/fix_rotation.png'
        cv2.imwrite(step_img_path,rotate_img)

        metadata['transformations'].append(('fix_rotation',args.fix_rotation))



    # remove document margins
    if 'remove_document_margins' not in args.skip_method:
        if args.logs:
            print('REMOVE DOCUMENT MARGINS')

        # remove document margins
        cut_margins = cut_document_margins(processed_image_path,logs=args.debug)
        
        image = cv2.imread(processed_image_path)
        treated_image = image[cut_margins.top:cut_margins.bottom,cut_margins.left:cut_margins.right]
        cv2.imwrite(processed_image_path,treated_image)

        # create step img
        step_img_path = f'{results_path}/remove_document_margins.png'
        cv2.imwrite(step_img_path,treated_image)

        metadata['transformations'].append(('remove_document_margins'))


    # blur removal
    if 'blur_removal' not in args.skip_method:
        # TODO
        pass

    # image upscaling
    if 'image_upscaling' not in args.skip_method:
        if args.logs:
            print('IMAGE UPSCALING')

        if args.upscaling_image:
            method = args.upscaling_image[0]
            upscaled = False

            if method == 'waifu2x':
                tmp_upsacled_image_path = f'{consts.tmp_path}/OSDOcr_image_upscaled_tmp.png'
                method_config = None
                if len(args.upscaling_image) > 1:
                    method_config = args.upscaling_image[1]

                target_dpi = args.target_dpi
                page_dimensions = get_dimensions(args.target_dimensions if args.target_dimensions else 'A3')
                page_dimensions = (page_dimensions['width'],page_dimensions['height'])

                if method_config:
                    run_waifu2x(processed_image_path,result_image_path=tmp_upsacled_image_path,method=method_config,target_dpi=target_dpi,dimensions=page_dimensions,logs=args.debug) 
                else:
                    run_waifu2x(processed_image_path,result_image_path=tmp_upsacled_image_path,target_dpi=target_dpi,dimensions=page_dimensions,logs=args.debug)

                upscaled_img = cv2.imread(tmp_upsacled_image_path)
                cv2.imwrite(processed_image_path,upscaled_img)
                upscaled = True

                # update tesseract config dpi
                w,h = upscaled_img.shape[1],upscaled_img.shape[0]

                dpi = calculate_dpi(Box(0,w,0,h),Box(0,page_dimensions[0],0,page_dimensions[1]))
                args.tesseract_config['dpi'] = dpi

            if upscaled:
                # create step img
                step_img_path = f'{results_path}/image_upscaling.png'
                cv2.imwrite(step_img_path,upscaled_img)

                metadata['transformations'].append(('image_upscaling',method,method_config))

    # remove document images
    if 'remove_document_images' not in args.skip_method:
        if args.logs:
            print('REMOVE DOCUMENT IMAGES')

        old_document = args.target_old_document
        # remove document images
            # also save them so they can be restored later
        images_folder = f'{results_path}/document_images'
        treated_image = remove_document_images(processed_image_path,logs=args.debug,old_document=old_document,save_blocks=True,save_blocks_path=images_folder)
        cv2.imwrite(processed_image_path,treated_image)

        # create step img
        step_img_path = f'{results_path}/remove_document_images.png'
        cv2.imwrite(step_img_path,treated_image)

        metadata['transformations'].append(('remove_document_images',images_folder))


    # lightning correction
    if 'lightning_correction' not in args.skip_method:
        # TODO
        pass



    # update metadata
    save_target_metadata(o_target,metadata)

    return processed_image_path


def run_target_hocr(target:str,args:argparse.Namespace):
    '''Run pipeline for single OCR target. TODO'''
    return None


def run_target_image(o_target:str,results_path:str,args:argparse.Namespace):
    '''Run pipeline for single image.
    - Image preprocessing
    - OCR
    - Convert to ocr_tree

    Return ocr_tree and image path (in case of preprocessing)
    '''
    target = o_target

    # preprocess image
    if 'image_preprocess' not in args.skip_method:
        target = image_preprocess(o_target,results_path,args)
            
    if args.logs:
        print(f'OCR: {target}')

    # binarize
    binarize_tmp = binarize(target)
    cv2.imwrite(f'{results_path}/binarize.png',binarize_tmp)
    binarized_path = f'{results_path}/binarize.png'

    run_tesseract(binarized_path,results_path=results_path,opts=args.tesseract_config,logs=args.debug)

    # update metadata
    metadata = get_target_metadata(o_target)
    metadata['ocr'] = True
    metadata['ocr_results_original_path'] = f'{results_path}/ocr_results.json'
    metadata['ocr_results_path'] = f'{results_path}/ocr_results.json'
    save_target_metadata(o_target,metadata)


    # create image blocks in OCR results
    if metadata_has_transformation(metadata,'remove_document_images'):
        _,blocks_path = metadata_get_transformation(metadata,'remove_document_images')

        if os.path.exists(blocks_path):
            blocks_positions_file_path = f'{blocks_path}/blocks.json'
            blocks = json.load(open(blocks_positions_file_path,'r'))

            ocr_results = OCR_Tree(f'{results_path}/ocr_results.json')
            page = ocr_results.get_boxes_level(1)[0]
            for block in blocks:
                ocr_block = OCR_Tree({'level':2,'box':block,'type':'image'})
                ocr_block.image_id = block['id']
                page.add_child(ocr_block)

            # save ocr results
            result_dict_file = open(f'{results_path}/ocr_results.json','w')
            json.dump(ocr_results.to_json(),result_dict_file,indent=4)
            result_dict_file.close()


    # get results
    return [OCR_Tree(f'{results_path}/ocr_results.json'),target]


def clean_ocr(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Clean ocr_tree'''
    ocr_results = bound_box_fix(ocr_results,2,None,find_images=False,logs=args.debug)

    result_dict_file = open(f'{results_path}/clean_ocr.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    metadata = get_target_metadata(o_target)
    target_img = metadata['target_path']

    image = draw_bounding_boxes(ocr_results,target_img,[2],id=True)
    cv2.imwrite(f'{results_path}/clean_ocr.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/ocr_results_processed.csv')

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/clean_ocr.json'
    metadata['transformations'].append('clean_ocr')
    save_target_metadata(o_target,metadata)

    return ocr_results


def unite_ocr_blocks(ocr_results:OCR_Tree,o_target:str,results_path:str,logs:bool=False):
    '''Unite ocr_tree'''
    

    ocr_results = unite_blocks(ocr_results)


    result_dict_file = open(f'{results_path}/result_united.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    metadata = get_target_metadata(o_target)
    target_img = metadata['target_path']

    image = draw_bounding_boxes(ocr_results,target_img,[2],id=True)
    cv2.imwrite(f'{results_path}/result_united.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/result_united.csv')

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/result_united.json'
    metadata['transformations'].append('unite_ocr_blocks')
    save_target_metadata(o_target,metadata)

    return ocr_results


def restore_document_images(o_target:str,results_path:str,logs:bool=False):
    '''Restore document images'''

    if logs:
        print('Restoring document images...')

    metadata = get_target_metadata(o_target)
    metadata['transformations'].append('restore_document_images')

    if metadata_has_transformation(metadata,'remove_document_images'):
        _,blocks_path = metadata_get_transformation(metadata,'remove_document_images')

        if os.path.exists(blocks_path):
            blocks_positions_file_path = f'{blocks_path}/blocks.json'
            blocks = json.load(open(blocks_positions_file_path,'r'))

            target_image = metadata['target_path']
            image = cv2.imread(target_image)

            for block in blocks:
                left = block['left']
                top = block['top']
                right = block['right']
                bottom = block['bottom']
                block_id = block['id']
                block_image_path = f'{blocks_path}/{block_id}.png'

                if os.path.exists(block_image_path):
                    block_image = cv2.imread(block_image_path)
                    image[top:bottom,left:right] = block_image

            # create step image
            cv2.imwrite(f'{results_path}/restore_document_images.png',image)

            metadata['target_path'] = f'{results_path}/restore_document_images.png'

    save_target_metadata(o_target,metadata)


def identify_images_ocr_results(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Identify images in ocr_results'''
    if args.logs:
        print('IDENTIFY DOCUMENT IMAGES')

    metadata = get_target_metadata(o_target)

    target_path = metadata['target_path']
    
    images = identify_document_images(target_path,old_document=args.target_old_document,logs=args.debug)
    
    #id ocr results
    ocr_results.id_boxes(level=[2])
    last_id = len(ocr_results.get_boxes_level(level=2))
    ocr_page = ocr_results.get_boxes_level(level=1)[0]
    images_ids = []

    for image in images:
        ocr_block = OCR_Tree({'level':2,'box':image,'type':'image','id':last_id})
        ocr_page.add_child(ocr_block)
        images_ids.append(last_id)
        last_id += 1

    # for each image, delete ocr blocks inside it
    for image_id in images_ids:
        ocr_results.remove_blocks_inside(image_id,args.debug)

    # save ocr results
    result_dict_file = open(f'{results_path}/identify_document_images.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target_path,[2],id=True)
    cv2.imwrite(f'{results_path}/identify_document_images.png',image)

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/identify_document_images.json'
    metadata['transformations'].append('identify_images_ocr_results')
    save_target_metadata(o_target,metadata)

    return ocr_results




def output_target_results(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Output target results'''
    if args.logs:
        print('OUTPUT TARGET RESULTS')

    metadata = get_target_metadata(o_target)
    metadata['output'] = {}
    save_target_metadata(o_target,metadata)


    if args.target_type == 'newspaper':
        # extract articles
        if 'extract_articles' not in args.skip_method:
            if args.logs:
                print('EXTRACT ARTICLES')
            extract_articles(o_target,ocr_results,results_path,args)



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
    create_target_results_folder(target)

    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_path = f'{results_path}/processed'
    original_target_path = target
    metadata = get_target_metadata(target)

    if args.logs:
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
        if force_ocr or not metadata['ocr']:
            ocr_results,_ = run_target_image(original_target_path,processed_path,args)
            
            # # identify images in target and modify ocr_results accordingly
            # if 'identify_document_images' not in args.skip_method:
            #     ocr_results = identify_images_ocr_results(ocr_results,original_target_path,processed_path,args)

            # get most recent metadata
            metadata = get_target_metadata(original_target_path)

        else:
            if os.path.exists(metadata['ocr_results_path']):
                ocr_results_path = metadata['ocr_results_path']
                ocr_results = OCR_Tree(ocr_results_path)
            else:
                print('File not found: ',ocr_results_path)
                print('Please run ocr first')
                sys.exit(1)

    target = metadata['target_path']


    # id boxes
    ocr_results.id_boxes([2])

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_0.png',id_img)

    # clean ocr_results
    if 'clean_ocr' not in args.skip_method:
        if args.logs:
            print('CLEAN OCR')
        ocr_results = clean_ocr(ocr_results,original_target_path,processed_path,args) 

    # categorize boxes
    ocr_results = categorize_boxes(ocr_results,args.debug)

    # unite same type blocks
    if 'unite_blocks' not in args.skip_method:
        if args.logs:
            print('UNITE BLOCKS')
        ocr_results = unite_ocr_blocks(ocr_results,original_target_path,processed_path,logs=args.debug)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_2.png',id_img)

    if args.debug:
        # analyse ocr_results
        results = analyze_text(ocr_results)
        print(results)


    # output
    output_target_results(ocr_results,original_target_path,results_path,args)


    restore_document_images(original_target_path,processed_path,args.debug)