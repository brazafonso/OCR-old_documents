import argparse
import shutil
from OSDOCR.pipeline import run_target as ocr_pipeline
from OSDOCR.gui.aux_utils.utils import *
from OSDOCR.ocr_tree_module.information_extraction import journal_template_to_text
from OSDOCR.ocr_tree_module.ocr_tree import *
from OSDOCR.ocr_tree_module.ocr_tree_analyser import *
from OSDOCR.ocr_tree_module.ocr_tree_fix import *
from OSDOCR.ocr_engines.engine_utils import *
from OSDOCR.output_module.journal.article import Article
from OSDOCR.aux_utils.misc import *
from OSDOCR.preprocessing.image import fix_illumination, remove_document_images,run_waifu2x



#### TAB 1


def fix_ocr(target:str,results_path:str):
    '''Fix OCR'''
    # check if results folder exists
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    ocr_results = OCR_Tree(ocr_results_path)
    ocr_results.id_boxes([2])
    ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
    # save results
    result_dict_file = open(f'{processed_folder_path}/clean_ocr.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
    cv2.imwrite(f'{processed_folder_path}/clean_ocr.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{processed_folder_path}/clean_ocr.csv')

    metadata['ocr_results_path'] = f'{processed_folder_path}/clean_ocr.json'
    metadata['transformations'].append('clean_ocr')
    save_target_metadata(target,metadata)




def tesseract_method(window:sg.Window,target:str,values:dict):
    '''Apply tesseract method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    # clean results folder files
    if os.path.exists(results_path):
        files = os.listdir(results_path)
        for file in files:
            if not os.path.isdir(f'{results_path}/{file}'):
                os.remove(f'{results_path}/{file}')

    logs = values['checkbox_1_1']
    # rotate image if not disabled
    ## create tmp rotated image
    if values['checkbox_1_2']:
        direction = values['select_list_1_1'].lower()
        img = rotate_image(target_image,direction=direction,debug=logs)
        target_image =f'{processed_folder_path}/fix_rotation.png'
        cv2.imwrite(target_image,img)

    # run tesseract
    run_tesseract(target_image,results_path=processed_folder_path,logs=logs)

    metadata['target_path'] = target_image
    metadata['ocr'] = True
    metadata['ocr_results_path'] = f'{processed_folder_path}/ocr_results.json'
    save_target_metadata(target,metadata)

        
    # update result image
    update_image_element(window,'result_img',f'{processed_folder_path}/ocr_results.png')





def extract_articles_method(window:sg.Window,target:str,values:dict):
    '''Apply extract articles method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    if os.path.exists(ocr_results_path):
        # create fixed result file
        if metadata_has_transformation(metadata,'clean_ocr'):
            fix_ocr(target,results_path)

            metadata = get_target_metadata(target)
            ocr_results_path = metadata['ocr_results_path']

    ocr_results = OCR_Tree(ocr_results_path)
    ocr_results = categorize_boxes(ocr_results)

    image_info = get_image_info(target_image)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])
    print('header',journal_template['header'])
    print('footer',journal_template['footer'])
    print(columns_area)
    
    # calculate reading order
    ignore_delimiters = True if values['checkbox_1_2'] else False
    t_graph = topologic_order_context(ocr_results,columns_area,ignore_delimiters=ignore_delimiters)
    order_list = sort_topologic_order(t_graph,sort_weight=True)

    print('Order List: ',order_list)
    articles = graph_isolate_articles(t_graph)
    for article in articles:
        print('Article:',[b.id for b in article])
        
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

    # draw reading order
    image = draw_articles(articles,target_image)
    cv2.imwrite(f'{results_path}/articles.png',image)
    update_image_element(window,'result_img',f'{results_path}/articles.png')


def fix_blocks_method(window:sg.Window,target:str):
    '''Apply fix blocks method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'

    fix_ocr(target,results_path)
    update_image_element(window,'result_img',f'{processed_folder_path}/clean_ocr.png')


def journal_template_method(window:sg.Window,target:str):
    '''Apply journal template method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    ocr_results = OCR_Tree(ocr_results_path)
    image_info = get_image_info(target_image)
    journal = estimate_journal_template(ocr_results,image_info)
    img = draw_journal_template(journal,target_image)
    cv2.imwrite(f'{processed_folder_path}/result_journal_template.png',img)

    update_image_element(window,'result_img',f'{processed_folder_path}/result_journal_template.png')

def reading_order_method(window:sg.Window,target:str,values:dict):
    '''Apply reading order method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    ocr_results = OCR_Tree(ocr_results_path)
    ocr_results.id_boxes([2],delimiters=False)
    image_info = get_image_info(target_image)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    ocr_results = categorize_boxes(ocr_results)

    # run topologic_order context
    ignore_delimiters = True if values['checkbox_1_1'] else False
    t_graph = topologic_order_context(ocr_results,columns_area,ignore_delimiters=ignore_delimiters)
    order_list = sort_topologic_order(t_graph,sort_weight=True)

    # change ids to order
    order_map = {order_list[i]:i for i in range(len(order_list))}
    ocr_results.change_ids(order_map)

    # draw reading order
    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
    cv2.imwrite(f'{processed_folder_path}/result_reading_order.png',image)
    update_image_element(window,'result_img',f'{processed_folder_path}/result_reading_order.png')


def auto_rotate_method(window:sg.Window,target:str,values:dict):
    '''Apply auto rotate method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']

    img = rotate_image(target_image,direction='auto',debug=logs,
                       auto_crop=True)

    cv2.imwrite(f'{processed_folder_path}/fix_rotation.png',img)
    metadata['target_path'] = f'{processed_folder_path}/fix_rotation.png'
    metadata['transformations'].append(('fix_rotation','auto'))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',img)


def unite_blocks_method(window:sg.Window,target:str,values:dict):
    '''Apply unite blocks method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']


    ocr_results = OCR_Tree(ocr_results_path)
    ocr_results.id_boxes([2])
    ocr_results = categorize_boxes(ocr_results)
    ocr_results = unite_blocks(ocr_results,debug=logs)
    # save results
    result_dict_file = open(f'{processed_folder_path}/result_united.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    metadata['ocr_results_path'] = f'{processed_folder_path}/result_united.json'
    metadata['transformations'].append('unite_ocr_blocks')
    save_target_metadata(target,metadata)

    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
    cv2.imwrite(f'{processed_folder_path}/result_united.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{processed_folder_path}/result_united.csv')

    update_image_element(window,'result_img',f'{processed_folder_path}/result_united.png')


def divide_columns_method(window:sg.Window,target:str,values:dict):
    '''Apply divide columns method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']


    logs = values['checkbox_1_1']
    analyses_type = values['select_list_1_1'].strip().lower()

    if analyses_type == 'blocks':
        ocr_results = OCR_Tree(ocr_results_path)
        column_boxes = get_columns(ocr_results,logs=logs)
    else:
        column_boxes = divide_columns(target_image,logs=logs)


    image_info = get_image_info(target_image)
    page_tree = OCR_Tree()

    for column in column_boxes:
        column.update(top=image_info.top,bottom=image_info.bottom)
        column_tree = OCR_Tree()
        column_tree.box = column
        page_tree.add_child(column_tree)



    result_image_path = f'{processed_folder_path}/divide_columns.png'
        
    image = draw_bounding_boxes(page_tree,target_image,[1])
    cv2.imwrite(result_image_path,image)

    update_image_element(window,'result_img',result_image_path)


def divide_journal_method(window:sg.Window,target:str,values:dict):
    '''Apply divide journal method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    ocr_results_path = metadata['ocr_results_path'] 
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']

    method = values['select_list_1_1'].strip().lower()

    if method == 'blocks':

        ocr_results = OCR_Tree(ocr_results_path)
        journal_areas = get_journal_areas(ocr_results,logs=logs)

        image_info = get_image_info(target_image)
        page_tree = OCR_Tree()

        if 'body' in journal_areas:
            body_box = journal_areas['body']
            body_box.update(right=image_info.right)
            body_tree = OCR_Tree()
            body_tree.box = body_box
            page_tree.add_child(body_tree)

            print('Body',body_box)


        if 'footer' in journal_areas:
            footer_box = journal_areas['footer']
            footer_box.update(right=image_info.right)
            footer_tree = OCR_Tree()
            footer_tree.box = footer_box
            page_tree.add_child(footer_tree)

            print('Footer',footer_box)


        if 'header' in journal_areas:
            header_box = journal_areas['header']
            header_box.update(right=image_info.right)
            header_tree = OCR_Tree()
            header_tree.box = header_box
            page_tree.add_child(header_tree)

            print('Header',header_box)

    else:
        header,body,footer = segment_document(target_image,logs=logs)
        page_tree = OCR_Tree()

        if header.valid():
            header_tree = OCR_Tree()
            header_tree.box = header
            page_tree.add_child(header_tree)

        if body.valid():
            body_tree = OCR_Tree()
            body_tree.box = body
            page_tree.add_child(body_tree)

        if footer.valid():
            footer_tree = OCR_Tree()
            footer_tree.box = footer
            page_tree.add_child(footer_tree)


    result_image_path = f'{processed_folder_path}/journal_areas.png'
        
    image = draw_bounding_boxes(page_tree,target_image,[1])
    cv2.imwrite(result_image_path,image)

    update_image_element(window,'result_img',result_image_path)


def remove_document_images_method(window:sg.Window,target:str,values:dict):
    '''Apply remove document images method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    model = values['select_list_1_1'].strip().lower() == 'old'
    
    treated_image = remove_document_images(target_image,logs=logs,old_document=model)

    cv2.imwrite(f'{processed_folder_path}/removed_images.png',treated_image)
    metadata['target_path'] = f'{processed_folder_path}/removed_images.png'
    metadata['transformations'].append(('remove_document_images'))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',treated_image)


def upscale_image_method(window:sg.Window,target:str,values:dict):
    '''Apply upscale image method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    method = values['select_list_1_1']
    
    upscaled_image_path = f'{processed_folder_path}/image_upscaling.png'
    run_waifu2x(target_image,result_image_path=upscaled_image_path,logs=logs,method=method)

    metadata['target_path'] = f'{processed_folder_path}/image_upscaling.png'
    metadata['transformations'].append(('image_upscaling','waifu2x',method))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',upscaled_image_path)


def denoise_image_method(window:sg.Window,target:str,values:dict):
    '''Apply denoise image method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    noise_level = values['select_list_1_1']
    
    denoise_image_path = f'{processed_folder_path}/noise_removal.png'

    run_waifu2x(target_image,result_image_path=denoise_image_path,logs=logs,noise_level=noise_level,method='noise')

    metadata['target_path'] = f'{processed_folder_path}/noise_removal.png'
    metadata['transformations'].append(('noise_removal','waifu2x',noise_level))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',denoise_image_path)


def light_correction_method(window:sg.Window,target:str,values:dict):
    '''Apply light correction method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    model_weight = values['select_list_1_1']
    split_image = values['checkbox_1_2']
    
    light_corrected_img = fix_illumination(target_image,model_weight=model_weight,split_image=split_image,logs=logs)

    if light_corrected_img is not None:
        cv2.imwrite(f'{processed_folder_path}/light_correction.png',light_corrected_img)
        metadata['target_path'] = f'{processed_folder_path}/light_correction.png'
        metadata['transformations'].append(('light_correction',model_weight))
        save_target_metadata(target,metadata)

        update_image_element(window,'result_img',light_corrected_img)


def cut_margins_method(window:sg.Window,target:str,values:dict):
    '''Apply cut margins method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    
    body = cut_document_margins(target_image,logs=logs)

    image = cv2.imread(target_image)
    cut_image = image[body.top:body.bottom,body.left:body.right]

    cv2.imwrite(f'{processed_folder_path}/remove_document_margins.png',cut_image)
    metadata['target_path'] = f'{processed_folder_path}/remove_document_margins.png'
    metadata['transformations'].append(('remove_document_margins'))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',cut_image)


def binarize_method(window:sg.Window,target:str,values:dict):
    '''Apply binarize method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_folder_path = f'{results_path}/processed'
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    logs = values['checkbox_1_1']
    denoise_strength = values['select_list_1_1']
    
    treated_image = binarize(target_image,denoise_strength,logs=logs)

    cv2.imwrite(f'{processed_folder_path}/binarized.png',treated_image)
    metadata['target_path'] = f'{processed_folder_path}/binarized.png'
    metadata['transformations'].append(('binarize',denoise_strength))
    save_target_metadata(target,metadata)

    update_image_element(window,'result_img',treated_image)


#### TAB 2

def calculate_dpi_method(window:sg.Window,target:str,resolution:str):
    '''Apply calculate dpi method to image and update image element'''
    metadata = get_target_metadata(target)
    target_image = metadata['target_path']

    # get image info
    image_info = get_image_info(target_image)

    # get resolution info from configs
    resolution = consts.config['dimensions'][resolution]
    resolution = Box(0,resolution['width'],0,resolution['height'])

    # calculate dpi
    dpi = calculate_dpi(image_info,resolution)

    # update image element
    window['result_text_1'].update(dpi,visible=True)



def ocr_pipeline_method(window:sg.Window):
    '''Apply ocr pipeline method to image and update image element'''
    configs = {}
    
    if 'ocr_pipeline' in consts.config:
        configs.update(consts.config['ocr_pipeline'])

    if configs['target']:
        args = argparse.Namespace(**configs)
        ocr_pipeline(configs['target'],args)


def pipeline_config_method(values:dict):
    '''Read values from pipeline config window and update configs'''
    
    new_configs = {
        'skip_method' : []
    }

    new_configs['target'] = consts.config['target_image_path']

    new_configs['output_folder'] = values['output_folder_path']

    new_configs['output_type'] = [values['select_list_output_type'].lower()]

    new_configs['force_ocr'] = values['checkbox_force_ocr']

    new_configs['ignore_delimiters'] = values['checkbox_ignore_delimiters']

    new_configs['fix_rotation'] = [values['select_list_fix_rotation'].lower()]
    if not values['checkbox_fix_rotation']:
        new_configs['skip_method'].append('auto_rotate')

    new_configs['upscaling_image'] = [values['select_list_upscaling_image'].lower()]
    if not values['checkbox_upscaling_image']:
        new_configs['skip_method'].append('image_upscaling')

    new_configs['denoise_image'] = [values['select_list_denoise_image_method'].lower(),values['select_list_denoise_image_level']]
    if not values['checkbox_denoise_image']:
        new_configs['skip_method'].append('denoise_image')

    
    tesseract_lang = values['select_list_tesseract_language']
    tesseract_dpi = int(values['input_tesseract_dpi']) if values['input_tesseract_dpi'].isdigit() else 150
    tesseract_psm = int(values['select_list_tesseract_psm'])
    new_configs['tesseract_config'] = {
        'l' : tesseract_lang,
        'dpi' : tesseract_dpi,
        'psm' : tesseract_psm
    }


    new_configs['fix_blocks'] = values['checkbox_fix_blocks']
    if not values['checkbox_fix_blocks']:
        new_configs['skip_method'].append('clean_ocr')

    new_configs['unite_blocks'] = values['checkbox_unite_blocks']
    if not values['checkbox_unite_blocks']:
        new_configs['skip_method'].append('unite_blocks')

    new_configs['extract_articles'] = values['checkbox_extract_articles']
    if not values['checkbox_extract_articles']:
        new_configs['skip_method'].append('extract_articles')

    new_configs['debug'] = values['checkbox_debug']

    consts.config['ocr_pipeline'] = new_configs
    save_configs()
