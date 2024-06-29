from .ocr_tree import *
from OSDOCR.ocr_tree_module.ocr_tree_analyser import analyze_text
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

        # get min left point and max right point
        lines = b.get_boxes_level(4)
        for l in lines:
            words = [w for w  in l.get_boxes_level(5,conf=text_confidence) if w.text.strip()]
            if words:
                first_word = words[0]
                last_word = words[-1]
                block_min_left = min(block_min_left,first_word.box.left) if block_min_left else first_word.box.left
                block_max_right = max(block_max_right,last_word.box.right) if block_max_right else last_word.box.right

        # update box
        if block_min_left and block_max_right and (b.box.left < block_min_left or b.box.right > block_max_right):
            new_left = max(b.box.left,block_min_left)
            new_right = min(b.box.right,block_max_right)
            if debug:
                print(f'Updating box {b.id} with min left {new_left} and max right {new_right} | Old box: {b.box}')
            b.update_box(left=new_left,right=new_right)

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
    blocks =  [b for b in ocr_results.get_boxes_level(2,ignore_type=['delimiter']) if not b.is_empty(conf=conf,only_text=True)]

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
                # cut block in two
                ## get level 3 blocks in area
                ### if delimiter is horizontal, cut area horizontally
                if current_delimiter_orientation == 'horizontal':
                    area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':block.box.left, 'bottom':current_delimiter_box.top+1})
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
                    # update first block
                    blocks_1 = None
                    blocks_2 = None
                    ## blocks need to be gathered according to delimter orientation (division cut)
                    ### if horizontal 
                    #### gather all lines and check which belong to what area
                    #### create new paragraphs according to lines
                    ### if vertical
                    #### gather all lines and paragraphs
                    #### for each line check what words belong to what area

                    # horizontal cut
                    if current_delimiter_orientation == 'horizontal':
                        lines = block.get_boxes_level(4)
                        area_1_lines = []
                        area_2_lines = []
                        for line in lines:
                            if line.box.is_inside_box(area_1):
                                area_1_lines.append(line)
                            else:
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
                                else:
                                    if cur_par == line.par_num:
                                        par_lines += [line]
                                        par_box = par_box.join(line.box)
                                    else:
                                        par = OCR_Tree({'level':3,'box':par_box})
                                        for line in par_lines:
                                            par.add_child(line)
                                        blocks_1.append(par)
                                        par_box = line.box
                                        par_lines = [line]
                                        cur_par = line.par_num

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
                                else:
                                    if cur_par == line.par_num:
                                        par_lines += [line]
                                        par_box = par_box.join(line.box)
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
                        ocr_results.id_boxes(level=[5])
                        blocks_1 = [b.copy() for b in block.get_boxes_level(3)]
                        blocks_2 = [b.copy() for b in block.get_boxes_level(3)]
                        # only leave each word in one of the areas
                        for i,p in enumerate(blocks_1):
                            par_words = p.get_boxes_level(5)
                            for w in par_words:
                                if not w.box.is_inside_box(area_1):
                                    blocks_1[i].remove_box_id(w.id,level=5)
                                else:
                                    blocks_2[i].remove_box_id(w.id,level=5)
                            # update par boxes
                            blocks_1[i].update_box(right=area_1.right)
                            blocks_2[i].update_box(left=area_2.left)

                    block_1 = OCR_Tree({'level':2,'box':area_1})
                    for c in blocks_1:
                        block_1.add_child(c)
                    print(f'Block 1: {block_1.box}')

                    # update second block
                    block_2 = OCR_Tree({'level':2,'box':area_2})
                    for c in blocks_2:
                        block_2.add_child(c)
                    # remove current block
                    ocr_results.remove_box_id(block.id,level=2)
                    # add new blocks
                    page = ocr_results.get_boxes_level(1)[0]
                    page.add_child(block_1)
                    page.add_child(block_2)
                    # add blocks to list
                    blocks.append(block_1)
                    blocks.append(block_2)
                    # id boxes again
                    ocr_results.id_boxes(level=[2])
            j += 1

    if logs:
        print('Remaining boxes:',len(ocr_results.get_boxes_level(2)))

    return ocr_results




