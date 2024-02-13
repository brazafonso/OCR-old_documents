import sys
import pytesseract
import json
import os
from aux_utils import consts
from PIL import Image
from aux_utils.box import Box
from aux_utils.misc import path_to_id
from ocr_box_module.ocr_box import OCR_Box
from ocr_box_module.ocr_box_analyser import *



def tesseract_search_img(image_path:str)->dict:
    '''Search for text in image of path saved on \'target_image_path\' using tesseract\n
    Return dict with results in various formats, and image with bounding boxes'''

    img = Image.open(image_path)
    print('Using tesseract')
    data_dict = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT,lang='por')
    data_text = pytesseract.image_to_string(img,lang='por')
    data_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf',lang='por')
    data_xml = pytesseract.image_to_alto_xml(img,lang='por')
    print(data_dict.keys())

    print('Text search over')
    
    return {
        'ocr_results':tesseract_convert_to_ocrbox(data_dict),
        'data_text':data_text,
        'data_pdf':data_pdf,
        'data_xml':data_xml
    }


def tesseract_convert_index_to_box(data_dict:dict,index:int)->OCR_Box:
    '''Convert tesseract index box into box'''
    atributes = {}
    # gather box atributes
    for k in data_dict.keys():
        atributes[k] = data_dict[k][index]
    atributes['right'] = atributes['left'] + atributes['width']
    atributes['bottom'] = atributes['top'] + atributes['height']
    # create ocr_box
    box = Box(atributes['left'],atributes['right'],atributes['top'],atributes['bottom'])
    ocr_box = OCR_Box(atributes['level'],atributes['page_num'],atributes['block_num'],
                      atributes['par_num'],atributes['line_num'],atributes['word_num'],box,atributes['text'],atributes['conf'])
    return ocr_box


def tesseract_convert_to_ocrbox(data_dict:dict)->OCR_Box:
    '''Convert tesseract results into ocr_box'''
    document = OCR_Box({'level':0,'page_num':0,'block_num':0,'par_num':0,'line_num':0,'word_num':0,'box':Box(0,0,0,0),'text':'','conf':-1})
    box_stack = [document]
    for i in range(len(data_dict['text'])):
        current_node = box_stack[-1]
        node = tesseract_convert_index_to_box(data_dict,i)
        if node.level == current_node.level + 1:
            current_node.add_child(node)
            box_stack.append(node)
        elif node.level == current_node.level:
            box_stack.pop()
            current_node = box_stack[-1]
            current_node.add_child(node)
            box_stack.append(node)
        else:
            while node.level != current_node.level + 1:
                box_stack.pop()
                current_node = box_stack[-1]
            current_node.add_child(node)
            box_stack.append(node)
    return document


def save_results(ocr_results:OCR_Box,image_path:str):
    '''Saves results gathered from ocr_results to files'''

    result_folder_name = path_to_id(image_path)
    # create result folder
    if not os.path.exists(f'{consts.result_path}/{result_folder_name}'):
        os.makedirs(f'{consts.result_path}/{result_folder_name}')

    results_path = f'{consts.result_path}/{result_folder_name}'

    img = draw_bounding_boxes(ocr_results,image_path)
    # create result files

    # create result image
    cv2.imwrite(f'{results_path}/result.png',img)

    

    # save result data
    result_dict_file = open(f'{results_path}/result.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    result_csv_file = open(f'{results_path}/result.csv','w')
    df = pd.DataFrame(ocr_results.to_dict())
    df.to_csv(result_csv_file)
    result_csv_file.close()
    
    # save result processed data
    data_processed = analyze_text(ocr_results)
    result_file = open(f'{results_path}/result_processed.json','w')
    json.dump(data_processed,result_file,indent=4)
    result_file.close()


def run_tesseract(image_path):
    '''GUI - Run text search on target image'''

    results = tesseract_search_img(image_path)
    ocr_results = results['ocr_results']
    data_text = results['data_text']
    data_pdf = results['data_pdf']
    data_xml = results['data_xml']
    
    # save results

    # save results from ocr_results
    save_results(ocr_results,image_path)

    # results path
    results_path = f'{consts.result_path}/{path_to_id(image_path)}'

    # save result simple text
    result_file = open(f'{results_path}/result.txt','w')
    result_file.write(data_text)
    result_file.close()


    # save result pdf and xml
    result_pdf = open(f'{results_path}/result.pdf','wb')
    result_pdf.write(data_pdf)
    result_pdf.close()

    result_xml = open(f'{results_path}/result.xml','wb')
    result_xml.write(data_xml)
    result_xml.close()