import argparse
import shutil
from pipeline import run_target as ocr_pipeline
from gui.aux_utils.utils import *
from ocr_tree_module.information_extraction import journal_template_to_text
from ocr_tree_module.ocr_tree import *
from ocr_tree_module.ocr_tree_analyser import *
from ocr_tree_module.ocr_tree_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article
from aux_utils.misc import *



#### TAB 1


def fix_ocr(target_image:str,results_path:str):
    '''Fix OCR'''
    # check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    ocr_results = OCR_Tree(f'{results_path}/result.json')
    ocr_results.id_boxes([2])
    ocr_results = bound_box_fix(ocr_results,2,get_image_info(target_image))
    # save results
    result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target_image,[2],id=True)
    cv2.imwrite(f'{results_path}/fixed/result_fixed.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/fixed/result_fixed.csv')




def tesseract_method(window:sg.Window,image_path:str,values:dict):
    '''Apply tesseract method to image and update image element'''
    # results path
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'

    # clean results folder files
    if os.path.exists(results_path):
        files = os.listdir(results_path)
        for file in files:
            # if is dir, delete dir
            if os.path.isdir(f'{results_path}/{file}'):
                shutil.rmtree(f'{results_path}/{file}')
            else:
                os.remove(f'{results_path}/{file}')


    # rotate image if not disabled
    ## create tmp rotated image
    if values['checkbox_1_1']:
        direction = values['select_list_1_1'].lower()
        img = rotate_image(image_path,direction=direction)
        cv2.imwrite(f'{image_path}_tmp.png',img)
        # run tesseract
        run_tesseract(f'{image_path}_tmp.png',results_path=results_path)
        os.remove(f'{image_path}_tmp.png')

    else:
        # run tesseract
        run_tesseract(image_path)
        
    # update result image
    update_image_element(window,'result_img',f'{results_path}/result.png')

    # create fixed result folder
    if not os.path.exists(f'{results_path}/fixed'):
        os.makedirs(f'{results_path}/fixed')





def extract_articles_method(window:sg.Window,image_path:str,values:dict):
    '''Apply extract articles method to image and update image element'''

    # results path
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    results_ocr_path =  f'{results_path}/result.json'
    results_ocr_fixed_path =  f'{results_path}/fixed/result_fixed.json'

    if os.path.exists(results_ocr_fixed_path) or os.path.exists(results_ocr_path):
        # create fixed result file
        if not os.path.exists(results_ocr_fixed_path):
            fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    ocr_results = categorize_boxes(ocr_results)

    image_info = get_image_info(image_path)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])
    print('header',journal_template['header'])
    print('footer',journal_template['footer'])
    print(columns_area)
    
    # calculate reading order
    ignore_delimiters = True if values['checkbox_1_1'] else False
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
    image = draw_articles(articles,image_path)
    cv2.imwrite(f'{results_path}/articles.png',image)
    update_image_element(window,'result_img',f'{results_path}/articles.png')


def fix_blocks_method(window:sg.Window,image_path:str):
    '''Apply fix blocks method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    fix_ocr(image_path,results_path)
    update_image_element(window,'result_img',f'{results_path}/fixed/result_fixed.png')


def journal_template_method(window:sg.Window,image_path:str):
    '''Apply journal template method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if fixed result file exists
    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
        fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    image_info = get_image_info(image_path)
    journal = estimate_journal_template(ocr_results,image_info)
    img = draw_journal_template(journal,image_path)
    cv2.imwrite(f'{results_path}/result_journal_template.png',img)
    update_image_element(window,'result_img',f'{results_path}/result_journal_template.png')

def reading_order_method(window:sg.Window,image_path:str,values:dict):
    '''Apply reading order method to image and update image element'''

    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if fixed result file exists
    if not os.path.exists(f'{results_path}/fixed/result_fixed.json'):
        fix_ocr(image_path,results_path)

    ocr_results = OCR_Tree(f'{results_path}/fixed/result_fixed.json')
    ocr_results.id_boxes([2],delimiters=False)
    image_info = get_image_info(f'{results_path}/fixed/result_fixed.png')
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
    image = draw_bounding_boxes(ocr_results,image_path,[2],id=True)
    cv2.imwrite(f'{results_path}/result_reading_order.png',image)
    update_image_element(window,'result_img',f'{results_path}/result_reading_order.png')


def auto_rotate_method(window:sg.Window,image_path:str):
    '''Apply auto rotate method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    img = rotate_image(image_path,direction='auto')
    update_image_element(window,'result_img',img)



def unite_blocks_method(window:sg.Window,image_path:str):
    '''Apply unite blocks method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    ocr_results = OCR_Tree(f'{results_path}/result.json')
    ocr_results.id_boxes([2])
    ocr_results = categorize_boxes(ocr_results)
    ocr_results = unite_blocks(ocr_results)
    # save results
    result_dict_file = open(f'{results_path}/fixed/united.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,image_path,[2],id=True)
    cv2.imwrite(f'{results_path}/fixed/united.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/fixed/united.csv')

    update_image_element(window,'result_img',f'{results_path}/fixed/united.png')


def divide_columns_method(window:sg.Window,image_path:str,values:dict):
    '''Apply divide columns method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    analyses_type = values['select_list_1_1'].strip().lower()

    if analyses_type == 'blocks':
        ocr_results = OCR_Tree(f'{results_path}/result.json')
        column_boxes = get_columns(ocr_results)
    else:
        column_boxes = get_columns_pixels(image_path)


    image_info = get_image_info(image_path)
    page_tree = OCR_Tree()

    for column in column_boxes:
        column.update(top=image_info.top,bottom=image_info.bottom)
        column_tree = OCR_Tree()
        column_tree.box = column
        page_tree.add_child(column_tree)



    result_image_path = f'{results_path}/test/columns.png'
    if not os.path.exists(f'{results_path}/test'):
        os.mkdir(f'{results_path}/test')
        
    image = draw_bounding_boxes(page_tree,image_path,[1])
    cv2.imwrite(result_image_path,image)

    update_image_element(window,'result_img',result_image_path)


def divide_journal_method(window:sg.Window,image_path:str):
    '''Apply divide journal method to image and update image element'''
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'
    # check if results folder exists
    if not os.path.exists(f'{results_path}/fixed'):
        os.mkdir(f'{results_path}/fixed')

    ocr_results = OCR_Tree(f'{results_path}/result.json')
    journal_areas = get_journal_areas(ocr_results)

    image_info = get_image_info(image_path)
    page_tree = OCR_Tree()

    if 'body' in journal_areas:
        body_box = journal_areas['body']
        body_box.update(right=image_info.right)
        body_tree = OCR_Tree()
        body_tree.box = body_box
        page_tree.add_child(body_tree)


    if 'footer' in journal_areas:
        footer_box = journal_areas['footer']
        footer_box.update(right=image_info.right)
        footer_tree = OCR_Tree()
        footer_tree.box = footer_box
        page_tree.add_child(footer_tree)


    if 'header' in journal_areas:
        header_box = journal_areas['header']
        header_box.update(right=image_info.right)
        header_tree = OCR_Tree()
        header_tree.box = header_box
        page_tree.add_child(header_tree)


    result_image_path = f'{results_path}/test/journal_areas.png'
    if not os.path.exists(f'{results_path}/test'):
        os.mkdir(f'{results_path}/test')
        
    image = draw_bounding_boxes(page_tree,image_path,[1])
    cv2.imwrite(result_image_path,image)

    update_image_element(window,'result_img',result_image_path)






#### TAB 2

def calculate_dpi_method(window:sg.Window,image_path:str,resolution:str):
    '''Apply calculate dpi method to image and update image element'''
    # get image info
    image_info = get_image_info(image_path)

    # get resolution info from configs
    resolution = consts.config['resolutions'][resolution]
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
