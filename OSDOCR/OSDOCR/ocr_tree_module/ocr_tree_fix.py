import numpy as np
from scipy import stats
from .ocr_tree import *
from OSDOCR.ocr_tree_module.ocr_tree_analyser import analyze_text,categorize_boxes,categorize_box
from OSDOCR.aux_utils.box import Box
from pytesseract import Output
from PIL import Image
import pytesseract
import jellyfish

def block_bound_box_fix(ocr_results:OCR_Tree,text_confidence:int=10,find_delimiters:bool=True,find_images:bool=True,debug:bool=False)->OCR_Tree:
    '''Fix block bound boxes.   
    
    Removes empty blocks that are not potential delimiters or images; tries to remove intersections and empty overlapping blocks.
    
    Args:
        ocr_results (OCR_Tree): ocr results
        text_confidence (int, optional): confidence of text, used for finding empty blocks. Defaults to 10.
        find_delimiters (bool, optional): if True, try to find delimiters using rules, else checks for block type. Defaults to True.
        find_images (bool, optional): if True, try to find images using rules, else checks for block type. Defaults to True.
        
    Returns:
        OCR_Tree: ocr results cleaned
    '''
    i = 0
    current_box = None
    text_analysis = analyze_text(ocr_results,conf=text_confidence)
    blocks = ocr_results.get_boxes_level(2)

    
    # remove blocks that have no text and take more than 80% of image
    ## if no flags for finding delimiters or images are set, remove all empty blocks
    image_box = ocr_results.get_boxes_level(0)[0].box
    image_area = image_box.area()
    for i,block in enumerate(blocks):
        if block.is_empty(conf=text_confidence,only_text=True):
            if block.box.area() >= image_area*0.8:
                if debug:
                    print(f'Removing Box : {block.id} is empty and too big')
                ocr_results.remove_box_id(block.id)
                blocks.pop(i)
                continue

            if not find_delimiters:
                if not block.is_delimiter(conf=text_confidence,only_type=True):
                    if debug:
                        print(f'Removing Box : {block.id} is empty and not a delimiter')
                    ocr_results.remove_box_id(block.id)
                    blocks.pop(i)
                    continue
            
            if not find_images:
                if not block.is_image(conf=text_confidence,only_type=True):
                    if debug:
                        print(f'Removing Box : {block.id} is empty and not an image')
                    ocr_results.remove_box_id(block.id)
                    blocks.pop(i)
                    continue


    boxes_to_check = {}
    checked_boxes = []
    og_len = len(blocks)
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i< len(blocks):
        # get current box to analyse
        if not current_box and blocks[i].id not in checked_boxes:
            if (not blocks[i].is_empty(conf=text_confidence)) or blocks[i].is_delimiter(conf=text_confidence,only_type=find_delimiters == False):
                current_box = blocks[i]
                i+=1
            else:
                if debug:
                    print(f'Removing Box : {blocks[i].id} is empty and not a delimiter')
                ocr_results.remove_box_id(blocks[i].id)
                blocks.pop(i)
            continue
        # check if boxes are within each other
        if current_box and blocks[i].id != current_box.id:
            #print('Comparing boxes',current_box.id,blocks[i].id)
            compare_box = blocks[i]

            # compared box inside current box
            if compare_box.is_empty(conf=text_confidence) and compare_box.box.is_inside_box(current_box.box):
                if debug:
                    print(f'Removing Box : {compare_box.id} is inside {current_box.id}')
                ocr_results.remove_box_id(compare_box.id)
                if compare_box.id in boxes_to_check: 
                    del boxes_to_check[compare_box.id]
            # current box inside compared box
            elif current_box.is_empty(conf=text_confidence) and current_box.box.is_inside_box(compare_box.box):
                if debug:
                    print(f'Removing Box : {current_box.id} is inside {compare_box.id}')
                ocr_results.remove_box_id(current_box.id)
                current_box = None
            # boxes intersect (with same level, so as to be able to merge seemlessly)
            elif current_box.box.intersects_box(compare_box.box):
                # update boxes so that they don't intersect
                # smaller box is reduced
                if current_box.box.box_is_smaller(compare_box.box):
                    intersect_area = compare_box.box.intersect_area_box(current_box.box)
                    #print(f'Box {current_box.id} is smaller than {compare_box.id}')
                    current_box.box.remove_box_area(intersect_area)
                    # update current box's children
                    current_box.prune_children_area()
                else:
                    intersect_area = current_box.box.intersect_area_box(compare_box.box)
                    #print(f'Box {compare_box.id} is smaller than {current_box.id}')
                    compare_box.box.remove_box_area(intersect_area)
                    # update compare box's children
                    compare_box.prune_children_area()
            else:
                if compare_box.id not in checked_boxes and compare_box.id not in boxes_to_check:
                    boxes_to_check[compare_box.id] = compare_box
        i+=1
        # change current box to next one
        if (i == len(blocks) and boxes_to_check) or (not current_box and boxes_to_check):
            current_box = None
            keys = list(boxes_to_check.keys())
            # get next not empty block
            while not current_box and boxes_to_check:
                current_box = boxes_to_check[id]
                current_box:OCR_Tree
                id = keys.pop(0)
                del boxes_to_check[id]
                checked_boxes.append(current_box.id)
                # check if box is empty
                # remove if true
                if current_box.is_empty(conf=text_confidence) and not current_box.is_delimiter(conf=text_confidence,only_type=find_delimiters == False):
                    # if potential image (big box) dont remove
                    if current_box.is_image(conf=text_confidence,text_size=text_analysis['normal_text_size'],only_type= find_images == False):
                        ocr_results.remove_box_id(current_box.id)
                        current_box = None
                i = 0

    if debug:
        print(f'''
        Initial number of boxes: {og_len}
        Final number of boxes: {len(ocr_results.get_boxes_level(2))}
        ''')
    return ocr_results


def text_bound_box_fix(ocr_results:OCR_Tree,text_confidence:int=10,debug:bool=False)->OCR_Tree:
    '''Fix bound boxes of blocks with text by reducing their sides when confidence of side text is too low.'''

    blocks = ocr_results.get_boxes_level(2)
    text_blocks = [b for b in blocks if b.to_text(conf=text_confidence).strip()]

    for b in text_blocks:
        block_min_left = None
        block_max_right = None
        block_min_top = None
        block_max_bottom = None

        # get adjusted box coordinates
        lines = b.get_boxes_level(4)
        for i,l in enumerate(lines):
            words = [w for w  in l.get_boxes_level(5,conf=text_confidence) if w.text.strip()]
            if words:
                # get left and right
                first_word = words[0]
                last_word = words[-1]
                block_min_left = min(block_min_left,first_word.box.left) if block_min_left else first_word.box.left
                block_max_right = max(block_max_right,last_word.box.right) if block_max_right else last_word.box.right

                # get top and bottom (first and last line)
                if i == 0:
                    top_most_word = sorted(words,key=lambda w: w.box.top)[0]
                    block_min_top = top_most_word.box.top
                if i == len(lines)-1:
                    bottom_most_word = sorted(words,key=lambda w: w.box.bottom)[-1]
                    block_max_bottom = bottom_most_word.box.bottom


        # update box
        if block_min_left and block_max_right and block_min_top and block_max_bottom and \
              (b.box.left < block_min_left or b.box.right > block_max_right or b.box.top < block_min_top or b.box.bottom > block_max_bottom):
            new_left = max(b.box.left,block_min_left)
            new_right = min(b.box.right,block_max_right)
            new_top = max(b.box.top,block_min_top)
            new_bottom = min(b.box.bottom,block_max_bottom)
            if debug:
                print(f'Updating box {b.id} with min left {new_left} and max right {new_right} and min top {new_top} and max bottom {new_bottom}| Old box: {b.box}')
            b.update_box(left=new_left,right=new_right,top=new_top,bottom=new_bottom)

    return ocr_results






def bound_box_fix(ocr_results:OCR_Tree,level:int,image_info:Box=None,text_confidence:int=10,find_images:bool=True,find_delimiters:bool=True,debug:bool=False)->OCR_Tree:
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_ocr_results = {}
    if level == 2:
        new_ocr_results = block_bound_box_fix(ocr_results,text_confidence=text_confidence,find_images=find_images,find_delimiters=find_delimiters,debug=debug)
    elif level == 5:
        new_ocr_results = text_bound_box_fix(ocr_results,text_confidence=text_confidence,debug=debug)

    return new_ocr_results



def unite_blocks(ocr_results:OCR_Tree,conf:int=10,logs:bool=False)->OCR_Tree:
    '''Unite same type of blocks if they are horizontally aligned and adjacent to each other'''

    
    # get all blocks
    blocks = ocr_results.get_boxes_level(2)
    non_visited = [b.id for b in blocks if b.id]
    available_blocks = [b for b in blocks if b.id]
    # get first block
    target_block_id = non_visited.pop(0)
    # iterate over all blocks
    while non_visited:
        united = False

        target_block = ocr_results.get_box_id(target_block_id,level=2)
        if logs:
            print(f'Visiting block {target_block_id}',f' Available blocks: {len(available_blocks)}',f' Non visited blocks: {len(non_visited)}')
        # get adjacent bellow blocks
        bellow_blocks = target_block.boxes_directly_below(available_blocks)
        

        # if bellow blocks exist
        if bellow_blocks:
            # filter blocks of same type and horizontally aligned
            bellow_blocks = [b for b in bellow_blocks if b.type == target_block.type and b.box.within_horizontal_boxes(target_block.box,range=0.1)]

            # treating text blocks
            if not target_block.is_empty(conf=conf,only_text=True):
                # if block is vertical text, can only unite with vertical text blocks
                if target_block.is_vertical_text(conf=conf):
                    bellow_blocks = [b for b in bellow_blocks if b.is_vertical_text(conf=conf)]

            # non text blocks
            else:
                target_orientation = target_block.box.get_box_orientation()
                # orientation should be the same
                bellow_blocks = [b for b in bellow_blocks if b.box.get_box_orientation() == target_orientation]

            # if single block passed, unite with target block
            if len(bellow_blocks) == 1:
                if logs:
                    print('Unite with block',bellow_blocks[0].id)
                # get bellow block
                bellow_block = bellow_blocks[0]
                # remove bellow block
                available_blocks = [b for b in available_blocks if b.id != bellow_block.id]
                non_visited = [id for id in non_visited if id != bellow_block.id]

                # unite
                target_block.join_trees(bellow_block)

                # remove bellow block from main tree
                ocr_results.remove_box_id(bellow_block.id,level=2)

                united = True
            
        if not united:
            # next block
            target_block_id = non_visited.pop(0)



    return ocr_results



def improve_bounds_precision(ocr_results,target_image_path,progress_key,window):
    'Rerun tesseract on within the boundings of a text box to improve its width and height precision'
    progress_text = f'Progress: 0 / {len(ocr_results["text"])}'
    window[progress_key].update(progress_text)
    window.refresh()
    original_img = Image.open(target_image_path)
    for i in range(len(ocr_results['text'])):
        if ocr_results[i].level == 5 and ocr_results[i].conf > 60:
            (x, y, w, h) = (ocr_results[i].left, ocr_results[i].top, ocr_results[i].width, ocr_results[i].height)
            img = original_img.crop((x-0.2*w,y-0.2*h,x+w*1.2,y+h*1.2))
            new_values = pytesseract.image_to_data(img, output_type=Output.DICT,config='--psm 8',lang='por')
            print(ocr_results[i].text)
            print(new_values['text'])
            print(new_values['conf'])
            for j in range(len(new_values['text'])):
                if new_values['level'][j] == 5 and jellyfish.levenshtein_distance(new_values['text'][j],ocr_results[i].text) < len(ocr_results[i].text)*0.3:
                    print('Updated:',ocr_results[i].text,new_values['text'][j])
                    print(' Old:',ocr_results[i].width,ocr_results[i].height)
                    print(' New:',new_values['width'][j],new_values['height'][j])
                    ocr_results[i].width = new_values['width'][j]
                    ocr_results[i].height = new_values['height'][j]
                    break
        progress_text = f'Progress: {i} / {len(ocr_results["text"])}'
        window[progress_key].update(progress_text)
        window.refresh()
    return ocr_results


def remvove_empty_boxes(ocr_results:OCR_Tree,conf:int=10,logs:bool=False)->OCR_Tree:
    'Remove empty boxes (with no text when considering given confidence threshold)'

    if logs:
        print('Removing empty boxes')
        print('Original boxes:',len(ocr_results.get_boxes_level(2)))

    # id boxes
    ocr_results.id_boxes(level=[2])

    blocks = ocr_results.get_boxes_level(2)
    for block in blocks:
        if block.is_empty(conf=conf):
            ocr_results.remove_box_id(block.id,level=2)

    if logs:
        print('Remaining boxes:',len(ocr_results.get_boxes_level(2)))

    return ocr_results


def delimiters_fix(ocr_results:OCR_Tree,conf:int=10,logs:bool=False,debug:bool=False)->OCR_Tree:
    '''Fix delimiters. Adjust bounding boxes, and remove delimiters inside text.'''

    if logs:
        print('Fix delimiters')
        print('Original boxes:',len(ocr_results.get_boxes_level(2)))

    # id boxes
    ocr_results.id_boxes(level=[2])

    delimiters = ocr_results.get_boxes_type(level=2,types=['delimiter'])
    blocks =  [b for b in ocr_results.get_boxes_level(2,ignore_type=['delimiter']) if not b.is_empty(conf=conf,only_text=True) or b.is_image(only_type=True)]

    # for each delimiter
    ## check if intersects with other blocks
    ### in which case adjust bounding box
    ## check if inside other blocks
    ### in which case remove delimiter
    for delimiter in delimiters:
        current_delimiter_box = delimiter.box
        current_delimiter_id = delimiter.id
        current_delimiter_orientation = current_delimiter_box.get_box_orientation()
        j = 0
        while j < len(blocks):
            block = blocks[j]
            # inside other blocks
            if current_delimiter_box.is_inside_box(block.box):
                if debug:
                    print(f'Removing delimiter {current_delimiter_id} inside block {block.id}')
                ocr_results.remove_box_id(current_delimiter_id,level=2)
                break
            # intersects with other blocks
            elif current_delimiter_box.intersects_box(block.box):
                # intercepting with image, probably is a border of a canvas
                if block.is_image(only_type=True):
                    intercept_area = block.box.intersect_area_box(current_delimiter_box).area()
                    delimiter_area = current_delimiter_box.area()
                    ## if more than 50% of delimiter is inside image, remove delimiter
                    if intercept_area/delimiter_area >= 0.5:
                        if debug:
                            print(f'Removing delimiter {current_delimiter_id} inside image {block.id}')
                        ocr_results.remove_box_id(current_delimiter_id,level=2)
                        break
                    else:
                        # adjust delimiter
                        current_delimiter_box.remove_box_area(block.box)
                else:
                    # cut block in two
                    ## get level 3 blocks in area
                    ### if delimiter is horizontal, cut area horizontally
                    if current_delimiter_orientation == 'horizontal':
                        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':block.box.right, 'bottom':current_delimiter_box.top+1})
                        area_2 = Box({'left':block.box.left, 'top':current_delimiter_box.bottom-1, 'right':block.box.right, 'bottom':block.box.bottom})
                    ### if delimiter is vertical, cut area vertically
                    else:
                        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':current_delimiter_box.left-1, 'bottom':block.box.bottom})
                        area_2 = Box({'left':current_delimiter_box.right+1, 'top':block.box.top, 'right':block.box.right, 'bottom':block.box.bottom})

                    # if delimiter passes through block, check block text if able to cut block in two
                    text_in_area_1 = block.get_boxes_in_area(area_1,level=5,conf=conf)
                    text_in_area_2 = block.get_boxes_in_area(area_2,level=5,conf=conf)
                    if not (len(text_in_area_1) > 1 and len(text_in_area_2) > 1):
                        # can't cut block in two
                        ## just adjust bounding box
                        ### check if adjust block or delimiter
                        if current_delimiter_orientation == 'horizontal':
                            if block.box.right < current_delimiter_box.left or block.box.left > current_delimiter_box.right:
                                # adjust block
                                if debug:
                                    print(f'Adjusting bounding box of block {block.id} | intersection with delimiter {current_delimiter_id}')       
                                block.box.remove_box_area(current_delimiter_box)
                            else:
                                # adjust delimiter
                                if debug:
                                    print(f'Adjusting bounding box of delimiter {current_delimiter_id} | intersection with block {block.id}')
                                current_delimiter_box.remove_box_area(block.box)
                        else:
                            if block.box.top > current_delimiter_box.top or block.box.bottom < current_delimiter_box.bottom:
                                # adjust block
                                if debug:
                                    print(f'Adjusting bounding box of block {block.id} | intersection with delimiter {current_delimiter_id}')  
                                block.box.remove_box_area(current_delimiter_box)
                            else:
                                # adjust delimiter
                                if debug:
                                    print(f'Adjusting bounding box of delimiter {current_delimiter_id} | intersection with block {block.id}')
                                current_delimiter_box.remove_box_area(block.box)
                    else:
                        if debug:
                            print(f'Can cut block {block.id} in two with delimiter {current_delimiter_id}')
                            print(f'Area 1: {area_1}')
                            print(f'Area 2: {area_2}')
                        new_blocks = split_block(block,current_delimiter_box,current_delimiter_orientation,conf=conf,debug=debug)

                        block_1 = new_blocks[0]
                        print(f'Block 1: {block_1.box}')

                        block_2 = new_blocks[1]
                        # add new blocks
                        page = ocr_results.get_boxes_level(1)[0]
                        page.add_child(block_2)
                        # add blocks to list
                        blocks.append(block_2)
                        # id boxes again
                        ocr_results.id_boxes(level=[2])
            j += 1

    if logs:
        print('Remaining boxes:',len(ocr_results.get_boxes_level(2)))

    return ocr_results



def remove_solo_words(ocr_results:OCR_Tree,conf:int=10,debug:bool=False)->OCR_Tree:
    '''Remove boxes with single words that are inside of other boxes. Bloxes need to be IDed and typed before calling this function.'''

    blocks = ocr_results.get_boxes_level(2)

    i = 0
    while i < len(blocks):
        block = blocks[i]
        if not block.is_empty(conf=conf):
            text = block.to_text(conf=conf)
            # check if text is single word and inside of other boxes of different type
            if len(text.strip().split(' ')) == 1:
                for b in blocks:
                    if b.id != block.id and block.box.is_inside_box(b.box):
                        if b.type != block.type:
                            if debug:
                                print(f'Removing solo word: {block.id} | inside {b.id} | type: {block.type} | {text}')
                            ocr_results.remove_box_id(block.id,level=2)
                            blocks.pop(i)
                            i -= 1
                            break

        i += 1
    return ocr_results



def find_text_titles(ocr_results:OCR_Tree,conf:int=10,id_blocks:bool=True,categorize_blocks:bool=True,debug:bool=False)->OCR_Tree:
    '''From ocr_results, searches within text blocks for titles and separatest them from the rest.
    Potential titles should be lines that are taller than normal text size, and come after closed text, or are in the beggining of the block.'''

    if id_blocks:
        ocr_results.id_boxes(level=[2])

    if categorize_blocks:
        ocr_results = categorize_boxes(ocr_results,conf=conf,debug=debug)

    ocr_analysis = analyze_text(ocr_results,conf=conf)

    page = ocr_results.get_boxes_level(1)[0]
    blocks = [b for b in ocr_results.get_boxes_level(2) if b.type == 'text']
    last_id = sorted([b.id for b in blocks])[-1] + 1
    i = 0
    # find titles in text blocks
    while i < len(blocks):
        block = blocks[i]
        # id lines in block
        block.id_boxes(level=[4])
        lines = block.get_boxes_level(4)
        if len(lines) < 2:
            i += 1
            continue
        j = 0
        for j,line in enumerate(lines):
            potential_title = []
            line_category = categorize_box(line,blocks,ocr_analysis,conf=conf)
            if line_category == 'title':
                if j > 0:
                    last_line = lines[j-1]
                    last_line_text = last_line.to_text(conf=conf).strip()
                else:
                    last_line_text = ''
                # check if last line is ended
                if not re.search(r'[\d\w]+',last_line_text) or last_line_text[-1] in ['.','?','!']:
                    potential_title.append(line)
                    # check next lines for title continuation
                    for j in range(j+1,len(lines)):
                        next_line = lines[j]
                        next_line_category = categorize_box(next_line,blocks,ocr_analysis,conf=conf)
                        if next_line_category == 'title':
                            potential_title.append(next_line)
                        else:
                            break
            if potential_title:
                # adjust current blocks and create new title block
                ## create new title block
                title_block = OCR_Tree({'level':2,'box':potential_title[0].box,'type':'title','id':last_id})
                ### create paragraph for lines
                title_block_par = OCR_Tree({'level':3,'box':potential_title[0].box})
                ### add lines to paragraph
                for line in potential_title:
                    title_block_par.add_child(line.copy())
                ### add paragraph to title block
                title_block.add_child(title_block_par)
                ### add title block to ocr results
                page.add_child(title_block)
                last_id += 1

                if debug:
                    print(f'Found title: {title_block.to_text(conf=conf)}')

                ## adjust current blocks
                new_blocks = split_block(block,title_block.box,orientation='horizontal',conf=conf,debug=debug)

                if len(new_blocks) > 1:
                    # add new block
                    new_block = new_blocks[-1]
                    new_block.id = last_id
                    new_block.type = 'text'
                    last_id += 1
                    page.add_child(new_block)
                    blocks.append(new_block)

                break
            j += 1

        i += 1
    return ocr_results



def split_block(block:OCR_Tree,delimiter:Box,orientation:str='horizontal',conf:int=10,debug:bool=False)->list['OCR_Tree']:
    '''Splits block into new blocks, based on delimiter and cut direction. Adjust text inside blocks to fit new area.'''
    new_blocks = [block]

    if not delimiter.intersects_box(block.box):
        return new_blocks

    if debug:
        print(f'Splitting block {block.id}')

    if orientation == 'horizontal':
        if debug:
            print('Splitting block by x')

        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':block.box.right, 'bottom':delimiter.top})
        area_2 = Box({'left':block.box.left, 'top':delimiter.bottom, 'right':block.box.right, 'bottom':block.box.bottom})
    elif orientation == 'vertical':
        if debug:
            print('Splitting block by y')

        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':delimiter.left, 'bottom':block.box.bottom})
        area_2 = Box({'left':delimiter.right, 'top':block.box.top, 'right':block.box.right, 'bottom':block.box.bottom})


    if debug:
        print(f'Area 1: {area_1}')
        print(f'Area 2: {area_2}')

    # update first block
    blocks_1 = []
    blocks_2 = []
    ## blocks need to be gathered according to delimter orientation (division cut)
    ### if horizontal 
    #### gather all lines and check which belong to what area
    #### create new paragraphs according to lines
    ### if vertical
    #### gather all lines and paragraphs
    #### for each line check what words belong to what area

    # horizontal cut
    if orientation == 'horizontal':
        lines = block.get_boxes_level(4)
        area_1_lines = []
        area_2_lines = []
        for line in lines:
            if line.box.is_inside_box(area_1):
                area_1_lines.append(line)
            elif line.box.is_inside_box(area_2):
                area_2_lines.append(line)

        blocks_1 = []
        if area_1_lines:
            par_box = None
            par_lines = []
            cur_par = None
            for line in area_1_lines:
                if not par_box:
                    par_box = line.box
                    cur_par = line.par_num
                    par_lines.append(line)
                else:
                    if cur_par == line.par_num:
                        par_lines.append(line)
                        par_box.join(line.box)
                    else:
                        # conclude paragraph
                        par = OCR_Tree({'level':3,'box':par_box})
                        for line in par_lines:
                            par.add_child(line)
                        blocks_1.append(par)
                        # create new paragraph
                        par_box = line.box
                        par_lines = [line]
                        cur_par = line.par_num
            # add last paragraph
            if par_lines:
                par = OCR_Tree({'level':3,'box':par_box})
                for line in par_lines:
                    par.add_child(line)
                blocks_1.append(par)

        if area_2_lines:
            par_box = None
            par_lines = []
            cur_par = None
            for line in area_2_lines:
                if not par_box:
                    par_box = line.box
                    cur_par = line.par_num
                    par_lines.append(line)
                else:
                    if cur_par == line.par_num:
                        par_lines.append(line)
                        par_box.join(line.box)
                    else:
                        par = OCR_Tree({'level':3,'box':par_box})
                        for line in par_lines:
                            par.add_child(line)
                        blocks_2.append(par)
                        par_box = line.box
                        par_lines = [line]
                        cur_par = line.par_num

            if par_lines:
                par = OCR_Tree({'level':3,'box':par_box})
                for line in par_lines:
                    par.add_child(line)
                blocks_2.append(par)

    # vertical cut
    else:
        # id words
        block.id_boxes(level=[5])
        blocks_1 = [b.copy() for b in block.get_boxes_level(3)]
        blocks_2 = [b.copy() for b in block.get_boxes_level(3)]
        # only leave each word in one of the areas
        for i,p in enumerate(blocks_1):
            par_words = p.get_boxes_level(5)
            for w in par_words:
                if not w.box.is_inside_box(area_1):
                    blocks_1[i].remove_box_id(w.id,level=5)
                if not w.box.is_inside_box(area_2):
                    blocks_2[i].remove_box_id(w.id,level=5)
            # update par boxes
            blocks_1[i].update_box(right=area_1.right)
            blocks_2[i].update_box(left=area_2.left)

    if blocks_1:
        # update current block
        ## box 
        block.box.update(left=area_1.left,top=area_1.top,right=area_1.right,bottom=area_1.bottom)
        ## children
        block.children = []
        for b in blocks_1:
            block.add_child(b)
    
    if blocks_2:

        if not blocks_1 and (area_1.height == 0 or area_1.width == 0):
            # update current block with area 2
            if debug:
                print(f'Area 1 is empty. Update block with area 2')
            block.box.update(left=area_2.left,top=area_2.top,right=area_2.right,bottom=area_2.bottom)
            block.children = []
            for b in blocks_2:
                block.add_child(b)


        else:
            # create second block
            new_block = OCR_Tree({'level':block.level,'box':area_2})

            for b in blocks_2:
                new_block.add_child(b)

            new_blocks = [block,new_block]
    

    return new_blocks



def split_whitespaces(ocr_results:OCR_Tree,conf:int=10,dif_ratio:int=3,debug:bool=False)->OCR_Tree:
    '''If a block contains sequence of whitespaces of ratio 'dif_ratio' compared to normal word distance, split the block into two blocks.
    
    Only possible if block has single line, or every line has similar amount of whitespaces in the same position.'''

    if debug:
        print('Splitting whitespaces...')

    text_analysis = analyze_text(ocr_results,conf=conf)
    avg_word_dist = text_analysis['average_word_distance']

    # id blocks
    ocr_results.id_boxes(level=[2])

    # get blocks with text
    blocks = [b for b in ocr_results.get_boxes_level(2) if not b.is_empty(conf=conf,only_text=True)]
    last_id = 0
    for b in blocks:
        if b.id >= last_id:
            last_id = b.id + 1

    
    for block in blocks:

        # get lines
        lines = block.get_boxes_level(4)
        line_seq_positions = []     # list of positions of whitespaces in each line
        valid_split = True

        # for each line, check if it contains a valid sequence of whitespaces
        ## saves the coordinates of the first and last whitespace in the sequence
        for line in lines:
            line_words = line.get_boxes_level(5)
            line_seq_position = [None,None]
            line_word_dists = []
            line_word_pairs = []

            for i,word in enumerate(line_words[:-1]):
                line_word_dists.append(line_words[i+1].box.left - word.box.right)
                line_word_pairs.append((word,line_words[i+1]))

            # identify word distance outliers
            line_word_dists = [d for d in line_word_dists if d > 0]
            if line_word_dists:
                # get average (adjusted with overall word distance)
                average = (sum(line_word_dists)/len(line_word_dists) + avg_word_dist)/2
                # check if any of the dists are bigger than 'dif_ratio' times the median
                for i,d in enumerate(line_word_dists):
                    if d >= dif_ratio*average:
                        line_seq_position[0] = line_word_pairs[i][0].box.right
                        line_seq_position[1] = line_word_pairs[i][1].box.left
                        break

                if not line_seq_position[0]:
                    valid_split = False
                    break
                else:
                    line_seq_positions.append(line_seq_position)

                

        if valid_split and line_seq_positions:
            # check max matching coordinates for split
            ## first check if all intervals intercept
            interception = True
            widest_interval = max(line_seq_positions,key=lambda x: x[1]-x[0])
            for interval in line_seq_positions:
                # check left and right
                if interval[0] > widest_interval[1] or interval[1] < widest_interval[0]:
                    interception = False
                    break
            ## if all intervals intercept, check widest common interval
            if interception:
                if debug:
                    print(f'Valid split found for block {block.id} | nº of lines: {len(line_seq_positions)} | widest interval: {widest_interval}')
                left = widest_interval[0]
                right = widest_interval[1]
                for interval in line_seq_positions:
                    if interval[0] > left:
                        left = interval[0]
                    if interval[1] < right:
                        right = interval[1]

                # split block
                delimiter = Box(left,right,block.box.top,block.box.bottom)
                blocks = split_block(block,delimiter,orientation='vertical',conf=conf)
                block = blocks[0]
                new_block = blocks[1] if len(blocks) == 2 else None

                # add new block
                if new_block:
                    new_block.id = last_id
                    last_id += 1
                    page = ocr_results.get_boxes_level(1)[0]
                    page.add_child(new_block)
                    blocks.append(new_block)

    return ocr_results
