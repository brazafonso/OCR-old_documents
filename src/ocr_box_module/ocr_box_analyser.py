import re
import pytesseract
import cv2
import jellyfish
from pytesseract import Output
from PIL import Image
from aux_utils.graph import *
from aux_utils.page_tree import *
from aux_utils.image import *
from aux_utils.box import *
from ocr_box_module.ocr_box import *
import math




def analyze_text(ocr_results:OCR_Box)->dict:
    '''Analyse text from ocr_results and return text data as dict\n
    Tries to find info about normal text size, number of lines and number of columns\n
    
    ### Result dict:
    - normal_text_size: average size of normal text
    - normal_text_gap: average gap between normal text lines
    - number_lines: estimated number of lines
    - number_columns: estimated number of columns
    - columns: list of columns bounding boxes\n
    '''
    number_columns = 0

    lines = ocr_results.get_boxes_level(4)
    left_margin_n = {}
    right_margin_n = {}

    line_sizes = []
    
    # save text sizes and margins
    for line in lines:
        left_margin = round(line.box.left,-1)
        if left_margin not in left_margin_n:
            left_margin_n[left_margin] = 0
        left_margin_n[left_margin] += 1

        right_margin = round((line.box.left + line.box.width),-1)
        if right_margin not in right_margin_n:
            right_margin_n[right_margin] = 0
        right_margin_n[right_margin] += 1

        lmh = line.calculate_mean_height()
        line.mean_height = lmh
        line_sizes.append(lmh)

    
    
    # estimate normal text size
    # calculate until good standard deviation is found
    ## normal text size average
    normal_text_size = sum(line_sizes)/len(line_sizes)
    ## normal text size standard deviation
    normal_text_size_std = math.sqrt(sum([(x-normal_text_size)**2 for x in line_sizes])/len(line_sizes))
    while normal_text_size_std > normal_text_size*2:
        # remove outliers (greatest value)
        line_sizes.remove(max(line_sizes))
        # recalculate normal text size
        normal_text_size = sum(line_sizes)/len(line_sizes)
        # recalculate normal text size standard deviation
        normal_text_size_std = math.sqrt(sum([(x-normal_text_size)**2 for x in line_sizes])/len(line_sizes))


    # estimate normal text size
    normal_text_gap = None

    last_block = None
    last_top = None
    last_line = None
    last_paragraph = None

    # estimate normal text gap
    for line in lines:
        if last_block:
            if line.block_num == last_block and line.par_num == last_paragraph and line.line_num == last_line + 1 and line.is_text_size(normal_text_size,mean_height=line.mean_height):
                if normal_text_gap:
                    normal_text_gap += line.box.top - last_top - normal_text_size
                    normal_text_gap /= 2
                else:
                    normal_text_gap = line.box.top - last_top - normal_text_size
            
        last_block = line.block_num
        last_top = line.box.top
        last_line = line.line_num
        last_paragraph = line.par_num

    # estimate number of lines
    highest_normal_text  = None
    lowest_normal_text = None

    ## find highest and lowest normal text
    for line in lines:
        if line.is_text_size(normal_text_size,mean_height=line.mean_height):
            if not highest_normal_text or line.box.top <= highest_normal_text:
                highest_normal_text = line.box.top
            if not lowest_normal_text or line.box.top+normal_text_size >= lowest_normal_text:
                lowest_normal_text = line.box.top+normal_text_size
    number_lines = (lowest_normal_text - highest_normal_text) // (normal_text_size + normal_text_gap)


    # estimate number of columns
    probable_columns = sorted([k for k in sorted(left_margin_n, reverse=True,key=left_margin_n.get) if left_margin_n[k]>=0.45*number_lines])
    number_columns = len(probable_columns)

    columns = []

    # create columns bounding boxes
    for i in range(len(probable_columns)):
        if i < len(probable_columns)-1:
            left = probable_columns[i]*0.98
            right = probable_columns[i+1]*1.02
            top = highest_normal_text*0.98
            bottom = lowest_normal_text*1.02
            columns.append(((left,top),(right,bottom)))
        # last column
        else:
            left = probable_columns[i]*0.98
            right = max(right_margin_n.keys())*1.02
            top = highest_normal_text*0.98
            bottom = lowest_normal_text*1.02
            columns.append(((left,top),(right,bottom)))
                


    return {
        'normal_text_size':normal_text_size,
        'normal_text_gap':normal_text_gap,
        'number_lines':number_lines,
        'number_columns':number_columns,
        'columns':columns
    }




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












def join_aligned_delimiters(delimiters:list[OCR_Box],orientation='horizontal'):
    '''Join aligned delimiters\n'''
    aligned_delimiters = []
    for delimiter in delimiters:
        delimiter_box = delimiter.box
        delimiter_box.right = delimiter_box.left + delimiter_box.width
        delimiter_box.bottom = delimiter_box.top + delimiter_box.height
        if not aligned_delimiters:
            aligned_delimiters.append(delimiter_box)
        else:
            joined = False
            for aligned in aligned_delimiters:
                if delimiter_box.is_aligned(aligned,orientation):
                    aligned.join(delimiter_box)
                    joined = True
                    break
            if not joined:
                aligned_delimiters.append(delimiter_box)
    return aligned_delimiters

    

def estimate_journal_header(ocr_results:OCR_Box,image_info:Box):
    '''Estimate journal header blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''

    header = None

    # get delimiter blocks
    search_area = Box(0,image_info.width,0,image_info.height*0.5) 
    delimiters = ocr_results.get_delimiters(search_area=search_area)

    
    if delimiters:
        # get widthest delimiter
        widthest_delimiter = sorted(delimiters,key=lambda x: x.box.width)[-1]
        
        # widder than treshold
        if widthest_delimiter.box.width >= image_info.width*0.3:
            header = {
            'left':None,
            'top':None,
            'width':None,
            'height':None,
            'right':None,
            'bottom':None,
            'boxes':[]
            }
                
            # update header
            header['left'] = widthest_delimiter.box.left
            header['right'] = widthest_delimiter.box.left + widthest_delimiter.box.width
            header['top'] = widthest_delimiter.box.top
            header['bottom'] = widthest_delimiter.box.top

            # get header boxes
            header_boxes = []
            blocks = ocr_results.get_boxes_level(2)
            for block in blocks:
                # delimiter block above delimiter
                if ( block.box.top + block.box.height) < widthest_delimiter.box.top:
                    header_boxes.append(block)
                    block_right = block.box.left + block.box.width
                    # update header info
                    if header['left'] > block.box.left:
                        header['left'] = block.box.left
                    if header['top'] > block.box.top:
                        header['top'] = block.box.top
                    if header['right'] < block_right:
                        header['right'] = block_right
            
            if header['top'] >= header['bottom']:
                header['bottom'] = widthest_delimiter.box.bottom
            
            header = Box(header['left'],header['right'],header['top'],header['bottom'])

    return header





def estimate_journal_columns(ocr_results,image_info:Box,header=None,footer=None):
    '''Estimate journal columns blocks and dimensions\n
    Main focus on pivoting using potential delimiters'''
    columns = []
    # defining margins of search area
    upper_margin = 0
    lower_margin = image_info.height
    if header:
        upper_margin = header.bottom
    if footer:
        lower_margin = footer.top

    # get delimiter blocks
    search_area = Box(0,image_info.width,upper_margin,lower_margin)
    delimiters = ocr_results.get_delimiters(search_area=search_area,orientation='vertical')

    if delimiters:
        # joint aligned delimiters
        column_delimiters = join_aligned_delimiters(delimiters,orientation='vertical')
        right_margin = Box(image_info.width,image_info.width,upper_margin,lower_margin)
        column_delimiters.append(right_margin)
        # sort delimiters
        column_delimiters = sorted(column_delimiters,key=lambda x: x.left)
        # estimate column boxes
        for i in range(len(column_delimiters)):
            left = 0
            if i > 0:
                left = column_delimiters[i-1].right
            column_box = Box(left,column_delimiters[i].right,upper_margin,lower_margin)
            columns.append(column_box)
    
    return columns

    
def estimate_journal_template(ocr_results,image_info):
    '''Tries to estimate a journal's template, such as header and different columns'''
    # get header boxes
    header = estimate_journal_header(ocr_results,image_info)
    #TODO: get footer boxes
    footer = None
    # get columns
    columns = estimate_journal_columns(ocr_results,image_info,header,footer)

    return {
        'header':header,
        'columns':columns,
        'footer':footer
    }


def draw_journal_template(journal_data,image_path):
    '''Draw bounding boxes on journal image of path \'image_path\'\n'''

    img = cv2.imread(image_path)

    # draw header
    if journal_data['header']:
        header = journal_data['header']
        (x, y, w, h) = (header.left, header.top, header.width, header.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # draw columns
    for column in journal_data['columns']:
        (x, y, w, h) = (column.left, column.top, column.width, column.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return img


def draw_bounding_boxes(ocr_results:OCR_Box,image_path:str,draw_levels=[2],conf=60,id=False):
    '''Draw bounding boxes on image of type MatLike from cv2\n
    Return image with bounding boxes'''

    img = cv2.imread(image_path)
    box_stack = [ocr_results]
    while box_stack:
        current_node = box_stack.pop()
        if current_node.level in draw_levels:
            # only draw text boxes if confidence is higher than conf
            if id and current_node.id or not id:
                if current_node.level == 5 and current_node.conf < conf:
                    continue
                (x, y, w, h) = (current_node.box.left, current_node.box.top, current_node.box.width, current_node.box.height)
                color = current_node.type_color()
                img = cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                
                if id and current_node.id:
                    img = cv2.putText(img, str(current_node.id), (round(x+0.1*w), round(y+0.3*h)), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,0,0), 6)
        for child in current_node.children:
            box_stack.append(child)
    return img



def next_top_block(blocks:list[OCR_Box],origin:Box=Box(0,0,0,0)):
    '''Get next top block\n
    Estimates block with best potential to be next top block\n
    Uses top and leftmost blocks for reference\n'''
    next_block = None
    if blocks:
        potential_top_block = None
        potential_leftmost_block = None

        # get top blocks
        blocks.sort(key=lambda x: x.box.top)
        highest_block_value = blocks[0].box.top
        next_block = blocks[0]
        top_blocks = [block for block in blocks if block.box.top == highest_block_value]

        # get blocks within vertical range of top blocks
        potential_top_blocks = []
        potential_top_blocks += top_blocks
        for block in blocks:
            for top_block in top_blocks:
                if block.box.within_vertical_boxes(top_block.box,range=0.05):
                    potential_top_blocks.append(block)

        
        if potential_top_blocks:
            # get leftmost block
            potential_top_blocks.sort(key=lambda x: x.box.left)
            leftmost_block= potential_top_blocks[0]
            next_block = potential_top_blocks[0]
            # get blocks within horizontal range of leftmost blocks
            potential_top_blocks = []
            for block in blocks:
                if block.box.within_horizontal_boxes(leftmost_block.box,range=0.05):
                    potential_top_blocks.append(block)


            if potential_top_blocks:
                # get highest block
                potential_top_blocks.sort(key=lambda x: x.box.top)
                next_block = potential_top_blocks[0]
                potential_top_block = potential_top_blocks[0]
        
        # get leftmost blocks
        blocks.sort(key=lambda x: x.box.left)
        leftmost_block_value = blocks[0].box.left

        # get blocks within horizontal range of leftmost blocks
        potential_leftmost_blocks = []
        leftmost_blocks = [block for block in blocks if block.box.left == leftmost_block_value]

        for block in blocks:
            for leftmost_block in leftmost_blocks:
                if block.box.within_horizontal_boxes(leftmost_block.box,range=0.05):
                    potential_leftmost_blocks.append(block)

        if potential_leftmost_blocks:
            # get top block
            potential_leftmost_blocks.sort(key=lambda x: x.box.top)
            next_block = potential_leftmost_blocks[0]
            potential_leftmost_block = potential_leftmost_blocks[0]

        if potential_leftmost_block and potential_top_block:
            # get block with least distance to top left corner
            leftmost_distance = math.sqrt(((origin.left-potential_leftmost_block.box.left)**2)+((origin.top-potential_leftmost_block.box.top)**2))
            top_distance = math.sqrt(((origin.left-potential_top_block.box.left)**2)+((origin.top-potential_top_block.box.top)**2))
            if leftmost_distance < top_distance:
                next_block = potential_leftmost_block
            else:
                next_block = potential_top_block

    return next_block
    


def calculate_reading_order_naive(ocr_results:OCR_Box,area:Box=None):
    '''Calculate reading order of OCR_Box of block level.

    Order left to right, top to bottom.

    Naive approach: only takes into account boxes position, not taking into account context such as article group\n'''

    # id blocks
    ocr_results.clean_ids()
    ocr_results.id_boxes([2],{2:1},False,area)

    # get blocks
    if area:
        blocks = ocr_results.get_boxes_in_area(area,2)
    else:
        blocks = ocr_results.get_boxes_level(2)

    # remove delimiter blocks
    non_del_blocks = [block for block in blocks if not block.is_delimiter()]

    blocks = non_del_blocks.copy()
    # order map
    # for each block, list of blocks that come after it
    order_map = {block.id:[] for block in blocks}




    # first block
    ## best block between the top blocks and the leftmost blocks
    current_block = next_top_block(blocks)
    

    blocks.remove(current_block)
    # calculate order map
    while blocks:
        if current_block:
            print('Current block:',current_block.id)
            # compare with other blocks
            for block in blocks:
                # block is aligned with current block vertically
                if block.box.within_vertical_boxes(current_block.box,range=0.2):
                    # block is to the right of current block
                    if block.box.left >= current_block.box.left:
                        # current block not in block's order map
                        if current_block.id not in order_map[block.id]:
                            order_map[current_block.id].append(block.id)
                # block is below current block
                elif block.box.top > current_block.box.top:
                    # current block not in block's order map
                    if current_block.id not in order_map[block.id]:
                        order_map[current_block.id].append(block.id)
            
            # get next block
            ## search for vertically aligned blocks bellow current block
            ## if none found, search for highest leftmost block
            next_block = None
            potential_next_blocks = []
            for block in blocks:
                # block is below current block
                if block.box.top > current_block.box.top:
                    # block is aligned with current block horizontally
                    if block.box.within_horizontal_boxes(current_block.box,range=0.2):
                        potential_next_blocks.append(block)
            
            if potential_next_blocks:
                print('Potential next blocks:',[block.id for block in potential_next_blocks])
                next_block = next_top_block(potential_next_blocks)



            if not next_block:
                print('No next block found',current_block.id)
                next_block = next_top_block(blocks)


            
            if next_block:
                blocks.remove(next_block)
                # if next block is not in current_block's order map, add it
                if next_block.id not in order_map[current_block.id]:
                    order_map[current_block.id].append(next_block.id)
                current_block = next_block
            else:
                current_block = None
        else:
            break
    
    print('Order map:',order_map)

    # order map to list
    order_list = []
    while len(order_list) < len(order_map):
        # get first block
        # no blocks before it in order_map, that are not already in order_list
        first_block = None
        for block in order_map:
            if block not in order_list:
                potential_first_block = block
                valid = True
                for other_blocks in order_map:
                    # potential first block in other block's order map
                    if potential_first_block in order_map[other_blocks]:
                        # other block not in order list
                        if other_blocks not in order_list:
                            valid = False
                            break
                if valid:
                    first_block = potential_first_block
                    break

        # add blocks to order_list
        order_list.append(first_block)

    print('Order list:',order_list)
    # change blocks id to order
    for block in non_del_blocks:
        block.id = order_list.index(block.id) +1

    # change delimiter id to 0
    for block in [block for block in ocr_results.get_boxes_level(2) if block.type == 'delimiter']:
        block.id = 0

    return ocr_results



def next_top_block_context(blocks:list[OCR_Box],current_block:OCR_Box=None):
    '''Get next top block
    
    Estimates block with best potential to be next top block, using context such as block type as reference
    
    If current_block is given, uses it as further reference'''

    next_block = None
    current_block_type = None
    if current_block:
        current_block_type = current_block.type

    non_delimiters = [block for block in blocks if block.type != 'delimiter']
    if non_delimiters:
        # if no current block, get title blocks
        if not current_block_type:
            print('No current block, getting title blocks')
            title_blocks = [block for block in blocks if block.type == 'title']
            if title_blocks:
                # get best title block
                next_block = next_top_block(title_blocks)
            else: 
                # remove text blocks with start_text=False
                potential_blocks = [block for block in non_delimiters if not (block.type == 'text' and block.start_text == False)]
                next_block = next_top_block(potential_blocks)

        # block title
        ## search for blocks bellow title block, different from title
        ## if none found try other types of block (other, image, caption)
        elif current_block_type == 'title':
            print('Current block is title')
            # get text blocks
            bellow_blocks = [block for block in non_delimiters if block.box.top > current_block.box.top and current_block.box.within_horizontal_boxes(block.box,range=0.3)]
            if bellow_blocks:
                print('Bellow blocks found',[block.id for block in bellow_blocks])
                # get best text block
                bellow_block = next_top_block(bellow_blocks)
                print('Bellow block:',bellow_block.id)
                if bellow_block and bellow_block.type != 'title':
                    next_block = bellow_block

        # block text
        ## if current block has unfinished text, search for text blocks bellow current block with start_text=False
        ## if none found, search for text blocks to the right of current block with start_text=False
        ## if none found, search for text blocks directly bellow current block
        ### if delimiter found, search for text blocks to the right of block and within delimiter's horizontal range
        elif current_block_type == 'text':
            print('Current block is text',current_block.id,current_block.start_text,current_block.end_text)
            # get text blocks
            text_blocks = [block for block in blocks if block.type == 'text']
            bellow_blocks = [block for block in blocks if block.box.top > current_block.box.top and current_block.box.within_horizontal_boxes(block.box,range=0.1)]
            bellow_block = None
            if bellow_blocks:
                # get top block
                bellow_blocks.sort(key=lambda x: x.box.top)
                bellow_block = bellow_blocks[0]
            ## text not finished
            if current_block.end_text == False:
                print('Text not finished')
                ## if bellow block is delimiter, search to the right of block and within delimiter's horizontal range
                if bellow_block and bellow_block.type == 'delimiter' and bellow_block.box.get_box_orientation() == 'horizontal':
                    print('Bellow block is delimiter',bellow_block.id)
                    potential_blocks = [block for block in text_blocks if  block.box.top < bellow_block.box.top and block.box.within_horizontal_boxes(bellow_block.box,range=0.3)]
                    if potential_blocks:
                        # get top block
                        ## TODO: may lack title context
                        next_block = next_top_block(potential_blocks)
                ## if bellow block is not delimiter, search for text blocks bellow current block with start_text=False
                ### if text block is found with start_text=True before a block with start_text=False, search for text blocks to the right of block with start_text=False
                #### TODO: title context could be helpful
                elif bellow_block:
                    print('Bellow block is not delimiter')
                    #### TODO: dont ignore non text blocks
                    bellow_blocks = [block for block in text_blocks if block.box.top > current_block.box.top and block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                    if bellow_blocks:
                        # get top block
                        bellow_block = next_top_block(bellow_blocks)
                        # if bellow block has start_text=False
                        if bellow_block.start_text == False:
                            # get text blocks to the right of current block with start_text=False
                            next_block = bellow_block
                        # else search to the right
                        else:
                            ## choose block to the right if it has start_text=False
                            potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                            next_block = next_top_block(potential_blocks)
                            ## else search for text blocks bellow current block
                            if next_block and next_block.start_text == True:
                                next_block = next_top_block(bellow_blocks)

                    # no blocks bellow current block, search to the right
                    else:
                        potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3) and block.start_text == False]
                        next_block = next_top_block(potential_blocks)
                else:
                    potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3) and block.start_text == False]
                    next_block = next_top_block(potential_blocks)
            ## text finished
            ### if bellow block is delimiter, search to the right of block and within delimiter's horizontal range
            ### TODO: title context could be helpful to decide if search to the right
            else:
                print('Text finished')
                if bellow_block:
                    print('Bellow block:',bellow_block.id)
                    # if bellow is type text
                    if bellow_block.type == 'text':
                        # if start_text=True, is next block
                        if bellow_block.start_text == True:
                            next_block = bellow_block
                    # next block is bellow block
                    else:
                        next_block = bellow_block

                # no blocks bellow current block
                else:
                    potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                    next_block = next_top_block(potential_blocks)

        # image block
        ## search for caption blocks bellow current block
        elif current_block_type == 'image':
            print('Current block is image')
            # get caption blocks
            caption_blocks = [block for block in blocks if block.type == 'caption' and block.box.top > current_block.box.top]
            if caption_blocks:
                # get best caption block
                next_block = next_top_block(caption_blocks)
                
        if not next_block or next_block.type == 'delimiter' and non_delimiters:
            print('No next block found',current_block.id if current_block else None)
            next_block = next_top_block(non_delimiters)
        
    return next_block





def calculate_reading_order_naive_context(ocr_results:OCR_Box,area:Box=None):
    '''Calculate reading order of OCR_Box of block level.

    Order left to right, top to bottom.

    Naive approach: only takes into account boxes position, not taking into account context such as article group
    
    Context approach: takes into account context such as caracteristics of blocks - title, caption, text, etc\n'''

    # id blocks
    # ocr_results.clean_ids()
    # ocr_results.id_boxes([2],{2:1},False,area)

    # get blocks
    if area:
        o_blocks = ocr_results.get_boxes_in_area(area,2)
    else:
        o_blocks = ocr_results.get_boxes_level(2)


    blocks = o_blocks.copy()
    # order map
    # for each block, list of blocks that come after it
    order_map = {block.id:[] for block in blocks if block.type != 'delimiter'}


    # first block
    ## best block between the top blocks and the leftmost blocks
    current_block = next_top_block_context(blocks)
    

    blocks.remove(current_block)
    # calculate order map
    while blocks:
        if current_block:
            print('Current block:',current_block.id,current_block.type)
            next_block = next_top_block_context(blocks,current_block)
            if next_block:
                print('Next block:',next_block.id)
                if next_block.id in order_map:
                    blocks.remove(next_block)
                    # if next block is not in current_block's order map, add it
                    if next_block.id not in order_map[current_block.id]:
                        order_map[current_block.id].append(next_block.id)
                        
                current_block = next_block
            else:
                current_block = None
            
        else:
            break
    
    print('Order map:',order_map)

    # order map to list
    order_list = []
    while len(order_list) < len(order_map):
        # get first block
        # no blocks before it in order_map, that are not already in order_list
        first_block = None
        for block in order_map:
            if block not in order_list:
                potential_first_block = block
                valid = True
                for other_blocks in order_map:
                    # potential first block in other block's order map
                    if potential_first_block in order_map[other_blocks]:
                        # other block not in order list
                        if other_blocks not in order_list:
                            valid = False
                            break
                if valid:
                    first_block = potential_first_block
                    break

        # add blocks to order_list
        order_list.append(first_block)

    print ('Order list:',order_list)
    
    # change blocks id to order
    for block in [block for block in ocr_results.get_boxes_level(2) if block.type != 'delimiter' and block.id]:
        block.id = order_list.index(block.id) +1

    # change delimiter id to 0
    for block in [block for block in ocr_results.get_boxes_level(2) if block.type == 'delimiter']:
        block.id = len(order_list) +1
    
    return ocr_results






def categorize_boxes(ocr_results:OCR_Box):
    '''Categorize blocks into different types
    
    Types:
    - 1: Delimiter
    - 2: Title
    - 3: Caption
    - 4: Text
    - 5: Image
    - 6: Table
    - 7: Other
    '''

    # analyze boxes
    box_analysis = analyze_text(ocr_results)

    # get blocks
    blocks = ocr_results.get_boxes_level(2)

    # categorize blocks
    for block in blocks:
        # empty block
        if block.is_empty():
            if block.is_delimiter():
                block.type = 'delimiter'
            else:
                block.type = 'other'
            ## TODO: categorize empty such as images
        # non empty block
        else:
            if block.is_text_size(box_analysis['normal_text_size']):
                # text block
                block.type = 'text'
            # greater than normal text size
            elif block.calculate_mean_height() > box_analysis['normal_text_size']:
                # title block
                block.type = 'title'
            # smaller than normal text size
            elif block.calculate_mean_height() < box_analysis['normal_text_size']:
                # caption block
                block.type = 'caption'
            else:
                # other
                block.type = 'other'

            # text characteristics
            block_text = block.to_text().strip()
            # if first character is lower case, starts with lower case
            if not block_text[0].isupper() and not re.match(r'^-\s*[A-Z"]',block_text):
                block.start_text = False
            else:
                block.start_text = True
            # if last character is punctuation, ends text
            if block_text[-1] in ['.','!','?']:
                block.end_text = True
            else:
                block.end_text = False
    return ocr_results

            

def topologic_graph(ocr_results:OCR_Box,area:Box=None)->Graph:
    '''Generate topologic graph of blocks\n
    
    Return:
    - topological graph: for each block, Node object with list of blocks that come after it'''

    # get blocks
    if area:
        blocks = ocr_results.get_boxes_in_area(area,2)
    else:
        blocks = ocr_results.get_boxes_level(2)
    non_delimiters = [block for block in blocks if block.type != 'delimiter']
    print('Non delimiters:',[block.id for block in non_delimiters])

    # calculate graph
    first_block = next_top_block(non_delimiters)
    first_node = Node(first_block.id,value=first_block)



    # topologic graph
    # Initialize graph with current_block
    topologic_graph = Graph()
    topologic_graph.add_node(first_node)
    current_node = first_node

    for block in non_delimiters:
        if block.id != first_block.id:
            node = Node(block.id,value=block)
            topologic_graph.add_node(node)

    visited = []

    while current_node:
        current_block = current_node.value
        current_block:OCR_Box
        visited.append(current_node.id)

        print('Current block:',current_block.id,current_block.type)
        # block is before blocks directly bellow and to the right of it
        potential_before_blocks = []
        right_blocks = current_block.blocks_directly_right(non_delimiters)
        bellow_blocks = current_block.blocks_directly_bellow(non_delimiters)
        potential_before_blocks += right_blocks
        potential_before_blocks += bellow_blocks
        print('Potential before blocks:',[block.id for block in potential_before_blocks])
        print('Bellow blocks:',[block.id for block in bellow_blocks])
        print('Right blocks:',[block.id for block in right_blocks])

        # clean potential before blocks
        ## can't be before blocks that are connected to current block
        for before_block in potential_before_blocks:
            before_node = topologic_graph.get_node(before_block.id)
                
            if before_node.is_connected(current_block.id,only_parents=True):
                potential_before_blocks.remove(before_block)


        print('Cleaned potential before blocks:',[block.id for block in potential_before_blocks])
        # create edges
        for before_block in potential_before_blocks:
            before_node = topologic_graph.get_node(before_block.id)
            current_node.add_child_edge(before_node)
            #print('Added edge:',current_block.id,'->',before_block.id)


        # get next block
        next_block = None
        next_node = None

        # choose block bellow
        ## if no block bellow, choose next top block
        ## if next top block is not in current node's children, add it
        next_block = next_top_block([b for b in bellow_blocks if b.id not in visited],current_block.box)
        if next_block:
            next_node = topologic_graph.get_node(next_block.id)
        else:
            non_visited = [block for block in non_delimiters if block.id not in visited]
            next_block = next_top_block(non_visited)
            if next_block:
                next_node = topologic_graph.get_node(next_block.id)
                if not current_node.in_children(next_node):
                    current_node.add_child_edge(next_node)

        
        current_block = next_block
        current_node = next_node
    topologic_graph.self_print()

    # # clean graph
    topologic_graph.clean_graph()

    return topologic_graph


def sort_topologic_order(topologic_graph:Graph,blocks:OCR_Box,sort_weight:bool=False)->list:
    '''Sort topologic graph into list\n

    Searches for first block in topologic graph, that has no blocks before it in order map, that are not already in order list\n
    For next blocks, in case of ties, chooses block with greatest attraction\n
    Return:
    - order_list: list of block ids in order'''
    # clean graph (remove transitive edges)
    # if not sort_weight:
    #     print('Cleaning graph')
    #     topologic_graph.clean_graph()

    #     topologic_graph.self_print()

    order_list = []
    last_node = None
    last_node:Node
    while len(order_list) < len(topologic_graph.nodes):
        # get next block
        # no blocks before it in order_map, that are not already in order_list
        next_node = []
        potential_next_nodes = []
        check_weight = sort_weight
        if last_node:
            potential_next_nodes = [edge.target for edge in last_node.children_edges if edge.target.id not in order_list and not last_node.is_connected(edge.target.id,only_parents=True)]
        
        if not potential_next_nodes:
            potential_next_nodes = [n for n in topologic_graph.nodes if n.id not in order_list]
            check_weight = False

        # get valid next blocks
        for node in potential_next_nodes:
            if node.id not in order_list:
                potential_next_node = node
                valid = True
                for other_node in potential_next_nodes:
                    # potential first block in other block's order map
                    if other_node.in_children(potential_next_node):
                        # other block not in order list
                        if other_node.id not in order_list:
                            valid = False
                            break
                if valid:
                    next_node.append(potential_next_node)

        # if more than one block, choose block with greatest attraction
        if len(next_node) > 1:
            if check_weight:
                edges = [e for e in last_node.children_edges if e.target in next_node]
                next_node = sorted(edges,key=lambda x: x.weight,reverse=True)
                # deal with ties
                max_weight = next_node[0].weight
                next_node = [edge for edge in next_node if edge.weight == max_weight]
                if len(next_node) > 1:
                    next_node = [edge.target.value for edge in next_node]
                    next_block = next_top_block(next_node)
                    next_node = topologic_graph.get_node(next_block.id)
                else:
                    next_node = next_node[0].target

            else:
                next_blocks = [node.value for node in next_node]
                next_block = next_top_block(next_blocks)
                next_node = topologic_graph.get_node(next_block.id)
        elif len(next_node) == 1:
            next_node = next_node[0]
        else:
            next_node = None

        if next_node:
            order_list.append(next_node.id)
            last_node = next_node
        else:
            last_node = None
            break
                    
                    
    return order_list



def topologic_order_context(ocr_results:OCR_Box,area:Box=None)->Graph:
    '''Generate topologic order of blocks\n
    
    Context approach: takes into account context such as caracteristics of blocks - title, caption, text, etc\n
    Context will allow to estimate attraction between blocks, such as title blocks being very atracted to non title blocks\n'''

    # get blocks
    if area:
        blocks = ocr_results.get_boxes_in_area(area,2)
    else:
        blocks = ocr_results.get_boxes_level(2)
    non_delimiters = [block for block in blocks if block.type != 'delimiter']

    t_graph = topologic_graph(ocr_results,area)

    # calculate attraction of edges
    for node in t_graph.nodes:
        for edge in node.children_edges:
            # calculate attraction
            attraction = calculate_block_attraction(node.value,edge.target.value,blocks)
            edge.weight = attraction
            edge.target.weight = attraction

    # print attraction
    print('Attraction:')
    for node in t_graph.nodes:
        print(node.id,node.children_edges,'|',node.parent_edges)

    return t_graph



def calculate_block_attraction(block:OCR_Box,target_block:OCR_Box,blocks:list[OCR_Box],direction:str=None,log:bool=False)->int:
    '''Calculate attraction between blocks\n

    Attraction is calculated based on block's characteristics such as type, size, position, etc\n

    0: No attraction\n'''
    if log:
        print('Calculating attraction between',block.id,target_block.id)

    max_distance = None
    min_distance = None
    for b in blocks:
        if b != block:
            distance = block.box.distance_to(b.box)
            if not max_distance or distance > max_distance:
                max_distance = distance
            if not min_distance or distance < min_distance:
                min_distance = distance

    attraction = 0

    if not direction:
        if block.box.within_vertical_boxes(target_block.box,range=0.2) and block.box.left < target_block.box.left:
            direction = 'right'
        elif block.box.top < target_block.box.top:
            direction = 'bellow'
        else:
            direction = 'right'

    if direction == 'bellow':
        attraction += 20
        if log:
            print('Direction: bellow')

    bellow_blocks = block.blocks_directly_bellow(blocks)
    leftmost_block = None
    if bellow_blocks:
        bellow_blocks.sort(key=lambda x: x.box.left)
        leftmost_block = bellow_blocks[0]

    if leftmost_block:
        if leftmost_block.type == 'delimiter' and direction == 'bellow':
            attraction -= 10
            if log:
                print('Leftmost block is delimiter')
        elif leftmost_block.type == 'delimiter' and direction == 'right':
            attraction += 10
            if log:
                print('Leftmost block is delimiter')

    if bellow_blocks:
        if target_block in bellow_blocks:
            attraction += 30
            if log:
                print('Target block is bellow')
    else:
        if direction == 'right':
            attraction += 40
            if log:
                print('Direction: right')

    # distance
    # normalize distance
    ## lower distance means higher attraction
    ## max attraction increase is 20
    ### exception, no bellow blocks (probably prefers upper block)
    distance = block.box.distance_to(target_block.box)
    distance = (distance-min_distance)/(max_distance-min_distance)
    if bellow_blocks:
        attraction += round(20*(1-distance))
        if log:
            print('Distance:',distance)



    # title
    ## title are very atracted to non title blocks
    ### bellow blocks are more atracted than right blocks
    ### right blocks are more attracted if bellow block is delimiter
    if block.type == 'title':
        if log:
            print('Block is title')
        if target_block.type != 'title':
            attraction += 50
            if log:
                print('Target block is not title')
        else:
            if target_block in bellow_blocks:
                attraction += 20
                if log:
                    print('Target block is bellow')
            
    # image
    ## images are very atracted to caption blocks
    elif block.type == 'image':
        if log:
            print('Block is image')
        if target_block.type == 'caption':
            attraction += 50
            if log:
                print('Target block is caption')
        else:
            attraction += 20
            if log:
                print('Target block is not caption')
    
    # text
    ## text is dependent on its content
    ## unfinished text is more atracted to unstarted text
    ## text is more attracted to text bellow it
    ### text to the right is more attracted if bellow block is delimiter
    elif block.type == 'text':
        if log:
            print('Block is text',block.start_text,block.end_text)
        if target_block.type =='text':
            if log:
                print('Target block is text',target_block.start_text,target_block.end_text)
            if direction == 'right':
                if log:
                    print('Direction: right')
                # text content
                if block.end_text == False and target_block.start_text == False:
                    attraction += 30
                    if log:
                        print('Block text is not finished and target block text is not started')

                if bellow_blocks:
                    if log:
                        print('Bellow blocks:',[block.id for block in bellow_blocks])
                    if leftmost_block.type == 'delimiter':
                        attraction += 20
                        if log:
                            print('Leftmost block is delimiter')
            else:
                if target_block in bellow_blocks:
                    attraction += 20
                    if log:
                        print('Target block is bellow')
                
                if block.end_text == False and target_block.start_text == False:
                    attraction += 50
                    if log:
                        print('Block text is not finished and target block text is started')
    

    if log:
        print('Attraction:',attraction)
    return attraction

