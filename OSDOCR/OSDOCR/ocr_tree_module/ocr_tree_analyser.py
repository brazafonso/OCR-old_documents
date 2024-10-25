import random
import re
from typing import Tuple
import cv2
import math
from scipy.signal import *
from OSDOCR.aux_utils.graph import *
from OSDOCR.aux_utils.box import *
from document_image_utils.image import *
from .ocr_tree import *
from whittaker_eilers import WhittakerSmoother




def get_text_sizes(ocr_results:OCR_Tree,method:str='WhittakerSmoother',conf:int=10,logs:bool=False)->dict:
    '''Get text sizes from ocr_results using peak detection on line size frequency\n
    
    Frequency graph is smoothened using chosen method.
    
    Available methods:
        - WhittakerSmoother
        - savgol_filter'''
    methods = ['WhittakerSmoother','savgol_filter']
    if method not in methods:
        method = 'WhittakerSmoother'


    text_sizes = {
        'normal_text_size': 0,
    }


    lines = ocr_results.get_boxes_level(4)
    line_sizes = []
    # save line sizes
    for line in lines:
        if not line.is_empty(conf=conf,only_text=True) and not line.is_vertical_text(conf=conf):
            lmh = line.calculate_mean_height(level=5,conf=conf)
            lmh = round(lmh)
            if len(line_sizes) <= lmh:
                line_sizes += [0] * (lmh - len(line_sizes) + 2)
            words = line.get_boxes_level(5,conf=conf)
            words = [w for w in words if w.text.strip()]
            # frequency is weighted by number of words in the line
            line_sizes[lmh] += 1 + len(words)


    if line_sizes:

        # add 10% to lists (because of smoothing might not catch peaks on edges)
        line_sizes = [0] * round(len(line_sizes)*0.1) + line_sizes + [0] * round(len(line_sizes)*0.1)

        if logs:
            # normal
            peaks,_ = find_peaks(line_sizes,prominence=0.01*sum(line_sizes))

        # smoothed 
        if method == 'WhittakerSmoother':
            whittaker_smoother = WhittakerSmoother(lmbda=1e1, order=3, data_length = len(line_sizes))
            line_sizes_smooth = whittaker_smoother.smooth(line_sizes)
        elif method == 'savgol_filter':
            line_sizes_smooth = savgol_filter(line_sizes, round(len(line_sizes)*0.1), 2)

        line_sizes_smooth = [i if i > 0 else 0 for i in line_sizes_smooth ]
        line_sizes_smooth = line_sizes_smooth[:len(line_sizes)] # filter adds to x axis length

        peaks_smooth,_ = find_peaks(line_sizes_smooth,prominence=0.1*max(line_sizes_smooth))
        if logs:
            # print peaks
            print('peaks:',peaks)
            print('frequency:',[line_sizes[peak] for peak in peaks])

            # turn line sizes into numpy array
            log_line_sizes = np.array(line_sizes)
            log_line_sizes_smooth = np.array(line_sizes_smooth)
            # create 2 plots
            plt.subplot(1, 2, 1)
            plt.plot(peaks, log_line_sizes[peaks], "ob"); plt.plot(log_line_sizes); plt.legend(['prominence'])
            plt.subplot(1, 2, 2)
            plt.plot(peaks_smooth, log_line_sizes_smooth[peaks_smooth], "ob"); plt.plot(log_line_sizes_smooth); plt.legend(['prominence'])

            plt.show()

        peaks_smooth:np.ndarray
        peaks_smooth = peaks_smooth.tolist()
        frequencies = [line_sizes_smooth[peak] for peak in peaks_smooth]

        sizes = {k:v for k,v in zip(peaks_smooth,frequencies)}
        

        text_sizes['normal_text_size'] = max(sizes,key=sizes.get)

        
        # categorize greater and smaller other text sizes
        lower_peaks = {k:v for k,v in sizes.items() if k < text_sizes['normal_text_size']}
        higher_peaks = {k:v for k,v in sizes.items() if k > text_sizes['normal_text_size']}
        i = 0
        while lower_peaks:
            text_sizes[f'small_text_size_{i}'] = max(lower_peaks,key=lower_peaks.get)
            del lower_peaks[text_sizes[f'small_text_size_{i}']]
            i += 1

        i = 0
        while higher_peaks:
            text_sizes[f'big_text_size_{i}'] = max(higher_peaks,key=higher_peaks.get)
            del higher_peaks[text_sizes[f'big_text_size_{i}']]
            i += 1

        # remove padding
        padding = round(len(line_sizes)*0.1)
        text_sizes = {k:v - padding for k,v in text_sizes.items() if v > 0}
        
    return text_sizes




def get_columns(ocr_results:OCR_Tree,method:str='WhittakerSmoother',logs:bool=False)->list[Box]:
    '''Get columns from ocr_results using peak detection on box left margin frequency\n
    
    Frequency graph is smoothened using chosen method.
    
    Available methods:
        - WhittakerSmoother
        - savgol_filter'''
    
    columns = []
    
    methods = ['WhittakerSmoother','savgol_filter']
    if method not in methods:
        method = 'WhittakerSmoother'

    left_margins = []
    right_margins = []
    blocks = ocr_results.get_boxes_level(2)
    for block in blocks:
        if not block.is_empty():
            words = block.get_boxes_level(5)
            words = [w for w in words if w.text.strip()]

            left = round(block.box.left)
            if len(left_margins) <= left:
                left_margins += [0] * (left - len(left_margins) + 1)
            left_margins[left] += 1 + len(words)

            right = round(block.box.left + block.box.width)
            if len(right_margins) <= right:
                right_margins += [0] * (right - len(right_margins) + 1)
            right_margins[right] += 1 + len(words)

    if len(left_margins) > 2:

        # add 10% to lists (because of smoothing might not catch peaks on edges)
        left_margins += [0] * round(len(left_margins)*0.1)
        right_margins += [0] * round(len(right_margins)*0.1)

        # calculate peaks

        ## left

        if logs:
            ### normal
            peaks_l,_ = find_peaks(left_margins,prominence=0.01*sum(left_margins))

        ### smoothed 
        if method == 'WhittakerSmoother':
            whittaker_smoother = WhittakerSmoother(lmbda=2e4, order=2, data_length = len(left_margins))
            left_margins_smooth = whittaker_smoother.smooth(left_margins)
        elif method == 'savgol_filter':
            left_margins_smooth = savgol_filter(left_margins, round(len(left_margins)*0.1), 2)

        left_margins_smooth = [i if i > 0 else 0 for i in left_margins_smooth ]
        left_margins_smooth = left_margins_smooth[:len(left_margins)] # filter adds to x axis length


        peaks_smooth_l,_ = find_peaks(left_margins_smooth,prominence=0.1*max(left_margins_smooth))

        ## right

        if logs:
            ### normal
            peaks_r,_ = find_peaks(right_margins,prominence=0.01*sum(right_margins))

        ### smoothed 
        if method == 'WhittakerSmoother':
            whittaker_smoother = WhittakerSmoother(lmbda=2e4, order=2, data_length = len(right_margins))
            right_margins_smooth = whittaker_smoother.smooth(right_margins)
        elif method == 'savgol_filter':
            right_margins_smooth = savgol_filter(right_margins, round(len(right_margins)*0.1), 2)

        right_margins_smooth = [i if i > 0 else 0 for i in right_margins_smooth ]
        right_margins_smooth = right_margins_smooth[:len(right_margins)] # filter adds to x axis length


        peaks_smooth_r,_ = find_peaks(right_margins_smooth,prominence=0.1*max(right_margins_smooth))

        if logs:
            # print peaks
            print('peaks:',peaks_l)
            print('frequency:',[left_margins[peak] for peak in peaks_l])

            # turn line sizes into numpy array
            log_left_margins = np.array(left_margins)
            log_left_margins_smooth = np.array(left_margins_smooth)
            log_right_margins = np.array(right_margins)
            log_right_margins_smooth = np.array(right_margins_smooth)


            # create 4 plots
            plt.subplot(2, 2, 1)
            plt.plot(peaks_l, log_left_margins[peaks_l], "ob"); plt.plot(log_left_margins); plt.legend(['prominence'])
            plt.title('Frequency Peaks - Left')

            plt.subplot(2, 2, 2)
            plt.plot(peaks_smooth_l, log_left_margins_smooth[peaks_smooth_l], "ob"); plt.plot(log_left_margins_smooth); plt.legend(['prominence'])
            plt.title('Frequency (smoothed) Peaks - Right')

            plt.subplot(2, 2, 3)
            plt.plot(peaks_r, log_right_margins[peaks_r], "ob"); plt.plot(log_right_margins); plt.legend(['prominence'])
            plt.title('Frequency Peaks - Right')

            plt.subplot(2, 2, 4)
            plt.plot(peaks_smooth_r, log_right_margins_smooth[peaks_smooth_r], "ob"); plt.plot(log_right_margins_smooth); plt.legend(['prominence'])
            plt.title('Frequency Peaks - Right')

            plt.show()

        
        peaks_smooth_l:np.ndarray
        peaks_smooth_r:np.ndarray
        peaks_smooth_l = peaks_smooth_l.tolist()
        peaks_smooth_r = peaks_smooth_r.tolist()
        for i in range(len(peaks_smooth_l)-1):
            column = Box({'left':peaks_smooth_l[i],'right':peaks_smooth_l[i+1] if i < len(peaks_smooth_l)-1 else peaks_smooth_l[i] + 100,'top':0,'bottom':1})
            columns.append(column)

    return columns






def get_journal_areas(ocr_results:OCR_Tree,method:str='WhittakerSmoother',logs:bool=False)->dict:
    '''Get areas of journal (header, body, footer) based on line box top margin frequency.\n
    
    Frequency graph is smoothened using chosen method.
    
    Available methods:
        - WhittakerSmoother
        - savgol_filter'''
    
    areas = {
        'header' : None,
        'body' : None,
        'footer' : None
    }
    
    methods = ['WhittakerSmoother','savgol_filter']
    if method not in methods:
        method = 'WhittakerSmoother'

    top_margins = []
    blocks = ocr_results.get_boxes_level(4)
    for block in blocks:
        if not block.is_empty():
            words = block.get_boxes_level(5)
            words = [w for w in words if w.to_text(conf=1).strip()]

            top = round(block.box.top)
            if len(top_margins) <= top:
                top_margins += [0] * (top - len(top_margins) + 1)
            top_margins[top] += 1 + len(words)

    max_frequency = max(top_margins)
    
    # reverse frequencies
    for i in range(len(top_margins)):
        top_margins[i] = max_frequency - top_margins[i]

    if top_margins:

        # add 10% to lists (because of smoothing might not catch peaks on edges)
        top_margins += [0] * round(len(top_margins)*0.1)

        # calculate peaks


        ### normal
        peaks_l,properties_l = find_peaks(top_margins,prominence=0.01*sum(top_margins),width=1)

        ### smoothed 
        if method == 'WhittakerSmoother':
            whittaker_smoother = WhittakerSmoother(lmbda=2e2, order=2, data_length = len(top_margins))
            top_margins_smooth = whittaker_smoother.smooth(top_margins)
        elif method == 'savgol_filter':
            top_margins_smooth = savgol_filter(top_margins, round(len(top_margins)*0.1), 2)

        top_margins_smooth = [i if i > 0 else 0 for i in top_margins_smooth ]
        top_margins_smooth = top_margins_smooth[:len(top_margins)] # filter adds to x axis length


        peaks_smooth_l,properties_smooth_l = find_peaks(top_margins_smooth,prominence=0.1*max(top_margins_smooth),width=1)


        if logs:
            # print peaks
            print('peaks:',peaks_l)
            print('frequency:',[top_margins[peak] for peak in peaks_l])

            # turn line sizes into numpy array
            log_top_margins = np.array(top_margins)
            log_top_margins_smooth = np.array(top_margins_smooth)


            # create 4 plots
            plt.subplot(2, 2, 1)
            plt.plot(peaks_l, log_top_margins[peaks_l], "ob"); plt.plot(log_top_margins); plt.legend(['prominence'])
            plt.vlines(x=peaks_l, ymin=log_top_margins[peaks_l] - properties_l["prominences"],
                    ymax = log_top_margins[peaks_l], color = "C1")
            plt.hlines(y=properties_l["width_heights"], xmin=properties_l["left_ips"],
                    xmax=properties_l["right_ips"], color = "C1")
            plt.title('Frequency Peaks - Left')

            plt.subplot(2, 2, 2)
            plt.plot(peaks_smooth_l, log_top_margins_smooth[peaks_smooth_l], "ob"); plt.plot(log_top_margins_smooth); plt.legend(['prominence'])
            plt.vlines(x=peaks_smooth_l, ymin=log_top_margins_smooth[peaks_smooth_l] - properties_smooth_l["prominences"],
                    ymax = log_top_margins_smooth[peaks_smooth_l], color = "C1")
            plt.hlines(y=properties_smooth_l["width_heights"], xmin=properties_smooth_l["left_ips"],
                    xmax=properties_smooth_l["right_ips"], color = "C1")
            plt.title('Frequency (smoothed) Peaks - Right')

            plt.show()

        

        # get areas
        ## group consecutive non-zero frequencies in signal
        ### biggest group is body
        groups = []
        group = (None,None)
        for i in range(len(top_margins_smooth)):
            if top_margins_smooth[i] > 0:
                if group[0]:
                    group = (group[0],i)
                else:
                    group = (i,None)
            elif group[0]:
                groups.append(group)
                group = (None,None)
        if group[0]:
            groups.append(group)

        biggest_group = max(groups, key=lambda x: x[1]-x[0])

        # print('groups:',groups)
        # print('body:',biggest_group)

        # get width of first peak inside biggest group
        first_peak = None
        for p,value in enumerate(peaks_smooth_l):
            if value > biggest_group[0] and value < biggest_group[1]:
                first_peak = p
                break
        last_peak = None
        for p,value in enumerate(reversed(peaks_smooth_l)):
            if value > biggest_group[0] and value < biggest_group[1]:
                last_peak = p
                break
        body_top = 0
        body_bottom = 0

        if first_peak:
            body_top = round(properties_smooth_l["left_ips"][first_peak])
        else:
            body_top = biggest_group[0]
        if last_peak:
            body_bottom = round(properties_smooth_l["right_ips"][last_peak])
        else:
            body_bottom = biggest_group[1]

        areas['body'] = Box({'left':0,'top':body_top,'right':0,'bottom':body_bottom})
        
        ## footer and header are relative to body
        areas['footer'] = Box({'left':0,'top':body_bottom,'right':0,'bottom':len(top_margins_smooth)})
        areas['header'] = Box({'left':0,'top':0,'right':0,'bottom':body_top})

    return areas



def analyze_text(ocr_results:OCR_Tree,conf:int=10)->dict:
    '''Analyse text from ocr_results and return text data as dict\n
    Tries to find info about normal text size, number of lines and number of columns\n
    
    ### Result dict:
    - normal_text_size: normal text size of the document page
    - <other text sizes>* : other text sizes of the document if any (need to be found as peaks by get_text_sizes)
    - columns: list of columns as Box class\n
    - average_word_distance: average distance between words
    '''
    analyze_results = {}

    text_sizes = get_text_sizes(ocr_results,method='WhittakerSmoother',conf=conf,logs=False)
    analyze_results.update(text_sizes)
    columns = get_columns(ocr_results,method='WhittakerSmoother',logs=False)
    analyze_results.update({'columns':columns})
    # average word distance
    distance_sum = 0
    distance_count = 0
    lines = ocr_results.get_boxes_level(4)
    for line in lines:
        words = line.get_boxes_level(5,conf=conf)
        for word in words[:-1]:
            word_dist = words[words.index(word)+1].box.left - word.box.right
            distance_sum += word_dist
            distance_count += 1
    if distance_count:
        analyze_results['average_word_distance'] = distance_sum/distance_count
    else:
        analyze_results['average_word_distance'] = 0


    return analyze_results



def estimate_journal_header(ocr_results:OCR_Tree,image_info:Box)->Box:
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


def join_aligned_delimiters(delimiters:list[OCR_Tree],orientation='horizontal'):
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


def estimate_journal_columns(ocr_results:OCR_Tree,image_info:Box,header:Box=None,footer:Box=None)->list[Box]:
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
        # join aligned delimiters
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

    
def estimate_journal_template(ocr_results:OCR_Tree,image_info:Box)->dict:
    '''Tries to estimate a journal's template, such as header and different columns'''
    # get header boxes
    header = estimate_journal_header(ocr_results,image_info)
    footer = None
    # get columns
    columns = estimate_journal_columns(ocr_results,image_info,header,footer)

    return {
        'header':header,
        'columns':columns,
        'footer':footer
    }


def draw_journal_template(journal_data:dict,image_path:Union[str,cv2.typing.MatLike],line_thickness:int=2)->cv2.typing.MatLike:
    '''Draw bounding boxes on journal image of path \'image_path\'\n'''

    if isinstance(image_path,str):
        img = cv2.imread(image_path)
    else:
        img = image_path

    # draw header
    if journal_data['header']:
        header = journal_data['header']
        (x, y, w, h) = (header.left, header.top, header.width, header.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), thickness=line_thickness)
    
    # draw columns
    for column in journal_data['columns']:
        (x, y, w, h) = (column.left, column.top, column.width, column.height)
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), thickness=line_thickness)

    return img


def draw_bounding_boxes(ocr_results:OCR_Tree,img:Union[str,cv2.typing.MatLike],draw_levels=[2],conf=60,id=False)->cv2.typing.MatLike:
    '''Draw bounding boxes on image of type MatLike from cv2\n
    Return image with bounding boxes'''

    if isinstance(img,str):
        img = cv2.imread(img)

    box_stack = ocr_results if isinstance(ocr_results,list) else [ocr_results]
    while box_stack:
        current_node = box_stack.pop()
        if current_node.level in draw_levels:
            # only draw text boxes if confidence is higher than conf
            if (id and current_node.id != None) or not id:
                if current_node.level == 5 and current_node.conf < conf:
                    continue
                (x, y, w, h) = (current_node.box.left, current_node.box.top, current_node.box.width, current_node.box.height)
                color = current_node.type_color()
                img = cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                if id and current_node.id != None:
                    img = cv2.putText(img, str(current_node.id), (round(x+0.1*w), round(y+0.3*h)), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,0,0), 6)
        for child in current_node.children:
            box_stack.append(child)
    return img


def draw_articles(articles:list[list[OCR_Tree]],image_path:str)->cv2.typing.MatLike:
    '''Draw articles in image\n
    
    Choose a unique color for each article\n'''

    # get image
    img = cv2.imread(image_path)

    # choose colors
    colors = []
    for i in range(len(articles)):
        unique_color = False
        color = None
        while not unique_color:
            color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
            if color not in colors:
                unique_color = True
        colors.append(color)

    # draw articles
    for i in range(len(articles)):
        for block in articles[i]:
            block:OCR_Tree
            (x, y, w, h) = (block.box.left, block.box.top, block.box.width, block.box.height)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), colors[i], 2)

    return img
            


def next_top_block(blocks:list[OCR_Tree],origin:Box=Box(0,0,0,0),debug=False)->OCR_Tree:
    '''Get next top block\n
    Estimates block with best potential to be next top block\n
    Uses top and leftmost blocks for reference\n'''
    if debug:
        print('Get next top block')

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

        if debug:
            print(f'Potential top blocks: {[block.id for block in potential_top_blocks]}')
            print(f'Potential leftmost blocks: {[block.id for block in potential_leftmost_blocks]}')

        if potential_leftmost_block and potential_top_block:
            # get block with least distance to top left corner
            leftmost_distance = math.sqrt(((origin.left-potential_leftmost_block.box.left)**2)+((origin.top-potential_leftmost_block.box.top)**2))
            top_distance = math.sqrt(((origin.left-potential_top_block.box.left)**2)+((origin.top-potential_top_block.box.top)**2))
            if leftmost_distance < top_distance:
                next_block = potential_leftmost_block
            else:
                next_block = potential_top_block

    return next_block
    


def calculate_reading_order_naive(ocr_results:OCR_Tree,area:Box=None)->OCR_Tree:
    '''Calculate reading order of ocr_tree of block level.

    Order left to right, top to bottom.

    Naive approach: only takes into account boxes position, not taking into account context such as article group\n
    
    Returns ocr_results with id reordered'''

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
            ## search for vertically aligned blocks below current block
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



def next_top_block_context(blocks:list[OCR_Tree],current_block:OCR_Tree=None)->OCR_Tree:
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
        ## search for blocks below title block, different from title
        ## if none found try other types of block (other, image, caption)
        elif current_block_type == 'title':
            print('Current block is title')
            # get text blocks
            below_blocks = [block for block in non_delimiters if block.box.top > current_block.box.top and current_block.box.within_horizontal_boxes(block.box,range=0.3)]
            if below_blocks:
                print('Bellow blocks found',[block.id for block in below_blocks])
                # get best text block
                below_block = next_top_block(below_blocks)
                print('Bellow block:',below_block.id)
                if below_block and below_block.type != 'title':
                    next_block = below_block

        # block text
        ## if current block has unfinished text, search for text blocks below current block with start_text=False
        ## if none found, search for text blocks to the right of current block with start_text=False
        ## if none found, search for text blocks directly below current block
        ### if delimiter found, search for text blocks to the right of block and within delimiter's horizontal range
        elif current_block_type == 'text':
            print('Current block is text',current_block.id,current_block.start_text,current_block.end_text)
            # get text blocks
            text_blocks = [block for block in blocks if block.type == 'text']
            below_blocks = [block for block in blocks if block.box.top > current_block.box.top and current_block.box.within_horizontal_boxes(block.box,range=0.1)]
            below_block = None
            if below_blocks:
                # get top block
                below_blocks.sort(key=lambda x: x.box.top)
                below_block = below_blocks[0]
            ## text not finished
            if current_block.end_text == False:
                print('Text not finished')
                ## if below block is delimiter, search to the right of block and within delimiter's horizontal range
                if below_block and below_block.type == 'delimiter' and below_block.box.get_box_orientation() == 'horizontal':
                    print('Bellow block is delimiter',below_block.id)
                    potential_blocks = [block for block in text_blocks if  block.box.top < below_block.box.top and block.box.within_horizontal_boxes(below_block.box,range=0.3)]
                    if potential_blocks:
                        # get top block
                        next_block = next_top_block(potential_blocks)
                ## if below block is not delimiter, search for text blocks below current block with start_text=False
                ### if text block is found with start_text=True before a block with start_text=False, search for text blocks to the right of block with start_text=False
                elif below_block:
                    print('Bellow block is not delimiter')
                    below_blocks = [block for block in text_blocks if block.box.top > current_block.box.top and block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                    if below_blocks:
                        # get top block
                        below_block = next_top_block(below_blocks)
                        # if below block has start_text=False
                        if below_block.start_text == False:
                            # get text blocks to the right of current block with start_text=False
                            next_block = below_block
                        # else search to the right
                        else:
                            ## choose block to the right if it has start_text=False
                            potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                            next_block = next_top_block(potential_blocks)
                            ## else search for text blocks below current block
                            if next_block and next_block.start_text == True:
                                next_block = next_top_block(below_blocks)

                    # no blocks below current block, search to the right
                    else:
                        potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3) and block.start_text == False]
                        next_block = next_top_block(potential_blocks)
                else:
                    potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3) and block.start_text == False]
                    next_block = next_top_block(potential_blocks)
            ## text finished
            ### if below block is delimiter, search to the right of block and within delimiter's horizontal range
            else:
                print('Text finished')
                if below_block:
                    print('Bellow block:',below_block.id)
                    # if below is type text
                    if below_block.type == 'text':
                        # if start_text=True, is next block
                        if below_block.start_text == True:
                            next_block = below_block
                    # next block is below block
                    else:
                        next_block = below_block

                # no blocks below current block
                else:
                    potential_blocks = [block for block in text_blocks if not block.box.within_horizontal_boxes(current_block.box,range=0.3)]
                    next_block = next_top_block(potential_blocks)

        # image block
        ## search for caption blocks below current block
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





def calculate_reading_order_naive_context(ocr_results:OCR_Tree,area:Box=None)->OCR_Tree:
    '''Calculate reading order of ocr_tree of block level.

    Order left to right, top to bottom.

    Naive approach: only takes into account boxes position, not taking into account context such as article group
    
    Context approach: takes into account context such as caracteristics of blocks - title, caption, text, etc\n
    
    Returns: ocr_tree with id reordered'''

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



def categorize_box(target_block:OCR_Tree,blocks:list[OCR_Tree],block_analysis:dict,conf:int=10,debug:bool=False)->str:
    '''Categorize single block into a type.
     
       Args:
           target_block: block to categorize
           blocks: list of blocks
           block_analysis: dictionary resulting from analyze_text. Needs at least normal_text_size as key.
           conf: text confidence level

       Returns block type'''
    block_type = None

    if debug:
        print('Categorizing block:',target_block.id,'Type:',target_block.type)

    # empty block
    if target_block.is_empty(conf=conf,only_text=True):
        if target_block.is_delimiter(conf=conf):
            block_type = 'delimiter'
        else:
            block_type = 'other'
        if debug:
            print('Empty block:',target_block.id,'| Type:',block_type)
    # non empty block
    else:
        block_text_size = target_block.calculate_mean_height(level=5,conf=conf)
        block_is_text_size = target_block.is_text_size(block_analysis['normal_text_size'],mean_height=block_text_size,
                                                       level=5,conf=conf,range=0.1)
        title_range = not target_block.is_text_size(block_analysis['normal_text_size'],mean_height=block_text_size,
                                                       level=5,conf=conf,range=1)
        blocks_directly_above = target_block.boxes_directly_above(blocks)

        if debug:
            print('Block:',target_block.id,'| Text size:',block_text_size)

        if block_is_text_size :
            if not len([b for b in blocks_directly_above if b.is_image(conf=conf)]):
                # text block
                block_type = 'text'
                if debug:
                    print('Text block:',target_block.id,f'| Is vertical: {target_block.is_vertical_text(conf=conf)} | Is text size: {block_is_text_size}')
            else:
                # caption block
                block_type = 'caption'
                if debug:
                    print('Caption block:',target_block.id,'| Has image above')
        # vertical text
        elif target_block.is_vertical_text(conf=conf):
            block_type = 'text'
            if debug:
                print('Text block:',target_block.id,f'| Is vertical: True')
        # greater than normal text size
        elif block_text_size > block_analysis['normal_text_size'] and title_range:
            words = target_block.get_boxes_level(5,conf=conf)
            words = [w for w in words if w.text.strip()]
            # title block
            ## less than 11 words
            if len(words) < 10:
                block_type = 'title'
                if debug:
                    print('Title block:',target_block.id,'| Text :',target_block.to_text(conf=conf).strip())
            ## highlight (some kind of second title)
            else:
                block_type = 'highlight'
                if debug:
                    print('Hihghlight block:',target_block.id,'| Too many words:',len(words))

        # smaller than normal text size and has image or caption directly above
        elif block_text_size < block_analysis['normal_text_size'] and \
            len([b for b in blocks_directly_above if b.is_image(conf=conf) or b.attribute_is_value('type','caption')]) > 0:
            # caption block
            block_type = 'caption'
            if debug:
                print('Caption block:',target_block.id,'| Is text size: ',block_is_text_size)


        # text characteristics
        ## for characteristics, needs to use minimum text confidence - 50 
        ##(avoid noise considered as dots, and other small errors)
        min_text_conf = max(50,conf)
        block_text = target_block.to_text(conf=min_text_conf).strip()
        # if first character is not uppercase or start of dialogue, not starts text
        if block_text and \
            (re.search(r'[a-z]',block_text) and not block_text[0].isupper() and not re.match(r'^(-|"|\')\s*[A-Z"]',block_text)):
            target_block.start_text = False
        else:
            target_block.start_text = True

        # if last character is punctuation, ends text
        if block_text and (re.search(r'(\.|!|\?|"|\')\s*$',block_text) or not re.search(r'[a-z]',block_text)):
            target_block.end_text = True
        else:
            target_block.end_text = False

        if debug:
            print('Block:',target_block.id,'| Start text:',target_block.start_text,'| End text:',target_block.end_text)

    if not block_type:
        if not target_block.is_empty(conf=conf):
            block_type = 'text'
        else:
            block_type = 'other'

        if debug:
            print('Block:',target_block.id,'| Type:',block_type)

    return block_type





def categorize_boxes(ocr_results:OCR_Tree,conf:int=10,override:bool=False,debug:bool=False)->OCR_Tree:
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
    box_analysis = analyze_text(ocr_results,conf=conf)
    if debug:
        print('Box analysis:',box_analysis)

    # get blocks
    blocks = ocr_results.get_boxes_level(2)


    # categorize blocks
    for block in blocks:
        if block.type and not override:
            continue
        type = categorize_box(block,blocks,box_analysis,conf=conf,debug=debug)
        block.type = type
                
    return ocr_results

            

def topologic_graph(ocr_results:OCR_Tree,area:Box=None,clean_graph:bool=True,debug:bool=False)->Graph:
    '''Generate topologic graph of blocks\n
    
    Return:
    - topological graph: for each block, Node object with list of blocks that come after it'''

    if debug:
        print('Generating topologic graph...')
        print('Area:',area)

    # get blocks
    if area:
        blocks = ocr_results.get_boxes_in_area(area,2)
    else:
        blocks = ocr_results.get_boxes_level(2)
    non_delimiters = [block for block in blocks if block.type != 'delimiter']
    if debug:
        print('Non delimiters:',[(block.id,block.type) for block in non_delimiters])

    if len(non_delimiters) == 0:
        return None

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
        current_block:OCR_Tree
        visited.append(current_node.id)
        if debug:
            print('Current block:',current_block.id,current_block.type,'|',current_block.to_text().strip()[:20])

        # block is before blocks directly below and to the right of it
        potential_before_blocks = []
        right_blocks = current_block.boxes_directly_right(non_delimiters)
        below_blocks = current_block.boxes_directly_below(non_delimiters)

        potential_before_blocks += right_blocks
        potential_before_blocks += below_blocks
        if debug:
            print('Potential before blocks:',[block.id for block in potential_before_blocks])
            print('Bellow blocks:',[block.id for block in below_blocks])
            print('Right blocks:',[block.id for block in right_blocks])

        # clean potential before blocks
        ## can't be before blocks that are connected to current block
        for before_block in potential_before_blocks:
            before_node = topologic_graph.get_node(before_block.id)
                
            if before_node.is_connected(current_block.id,only_parents=True):
                potential_before_blocks.remove(before_block)

        if debug:
            print('Cleaned potential before blocks:',[block.id for block in potential_before_blocks])
        # create edges
        for before_block in potential_before_blocks:
            before_node = topologic_graph.get_node(before_block.id)
            current_node.add_child_edge(before_node)
            #print('Added edge:',current_block.id,'->',before_block.id)


        # get next block
        next_block = None
        next_node = None

        # choose block below
        ## if no block below, choose next top block
        ## if next top block is not in current node's children, add it
        next_block = next_top_block([b for b in below_blocks if b.id not in visited],current_block.box)
        if next_block:
            next_node = topologic_graph.get_node(next_block.id)
        else:
            non_visited = [block for block in non_delimiters if block.id not in visited]
            next_block = next_top_block(non_visited)
            if next_block:
                next_node = topologic_graph.get_node(next_block.id)
                if not below_blocks:
                    # add node as child
                    current_node.add_child_edge(next_node)

        
        current_block = next_block
        current_node = next_node

    if debug:
        print('Topologic graph:')
        topologic_graph.self_print()

    # clean graph
    if clean_graph:
        order = sort_topologic_order(topologic_graph)
        topologic_graph.clean_graph(order)

    return topologic_graph


def sort_topologic_order(topologic_graph:Graph,sort_weight:bool=False,next_node_filter:any=None,
                         log:bool=False,debug:bool=False)->list[int]:
    '''Sort topologic graph into list\n

    Searches for first block in topologic graph, that has no blocks before it in order map, that are not already in order list\n
    For next blocks, in case of ties, chooses block with greatest attraction\n

    If sort_weight is True, sorts blocks by weight, otherwise sorts by order of appearance. Narrows parents before sorting.\n
    Return:
    - order_list: list of block ids in order'''

    # clean graph (narrow parents by removing edges with lower attraction; reduces blocks' dependencies)
    if sort_weight:
        if debug:
            print('Narrowing parents')
        topologic_graph.narrow_parents()
    
    if debug:
        print('Topologic graph:')
        topologic_graph.self_print()

    order_list = []
    last_node = None
    last_node:Node
    while len(order_list) < len(topologic_graph.nodes):
        # get next block
        # no blocks before it in order_map, that are not already in order_list
        next_node = []
        potential_next_nodes = []
        check_weight = sort_weight

        if debug:
            print('Order list:',order_list)
            if last_node:
                print('Last node:',last_node.id)

        if last_node:
            potential_next_nodes = [edge.target for edge in last_node.children_edges \
                                    if edge.target.id not in order_list ]
        
        if debug:
            print('Potential next nodes:',[node.id for node in potential_next_nodes])

        if not potential_next_nodes:
            # apply filter if given
            if next_node_filter:
                potential_next_nodes = [next_node_filter(n) for n in topologic_graph.nodes if n.id not in order_list]
                potential_next_nodes = [n for n in potential_next_nodes if n is not None]

            if not potential_next_nodes:
                potential_next_nodes = [n for n in topologic_graph.nodes if n.id not in order_list]

                
        if debug:
            print('Potential next nodes:',[node.id for node in potential_next_nodes])

        # get valid next blocks
        for node in potential_next_nodes:
            if node.id not in order_list:
                potential_next_node = node
                valid = True
                for other_node in potential_next_nodes:
                    # potential first block in other block's order map
                    if other_node.is_connected(potential_next_node):
                        # other block not in order list
                        if other_node.id not in order_list:
                            valid = False
                            break
                if valid:
                    next_node.append(potential_next_node)

        if debug:
            print('Valid next nodes:',[node.id for node in next_node])


        # if more than one block, choose block with greatest attraction
        if len(next_node) > 1:
            if check_weight and last_node and (edges:=[e for e in last_node.children_edges if e.target in next_node]):
                next_node = sorted(edges,key=lambda x: x.weight,reverse=True)
                # deal with ties
                max_weight = next_node[0].weight
                next_node = [edge for edge in next_node if edge.weight == max_weight]
                if len(next_node) > 1:
                    next_node = [edge.target.value for edge in next_node]
                    next_block = next_top_block(next_node,debug=debug)
                    next_node = topologic_graph.get_node(next_block.id)
                else:
                    next_node = next_node[0].target

            else:
                next_blocks = [node.value for node in next_node]
                next_block = next_top_block(next_blocks,debug=debug)
                next_node = topologic_graph.get_node(next_block.id)
        elif len(next_node) == 1:
            next_node = next_node[0]
        else:
            next_block = next_top_block([node.value for node in potential_next_nodes],debug=debug)
            next_node = topologic_graph.get_node(next_block.id)

        if next_node:
            order_list.append(next_node.id)
            last_node = next_node
        else:
            last_node = None
            break
                    
                    
    return order_list



def topologic_order_context(ocr_results:OCR_Tree,area:Box=None,ignore_delimiters:bool=False,debug:bool=False)->Graph:
    '''Generate topologic order of blocks\n
    
    Context approach: takes into account context such as caracteristics of blocks - title, caption, text, etc\n
    Context will allow to estimate attraction between blocks, such as title blocks being very atracted to non title blocks\n'''

    ignore_type = ['delimiter'] if ignore_delimiters else []
    # get blocks
    if area:
        blocks = ocr_results.get_boxes_in_area(area,2,ignore_type=ignore_type)
    else:
        blocks = ocr_results.get_boxes_level(2,ignore_type=ignore_type)


    t_graph = topologic_graph(ocr_results,area,clean_graph=False,debug=debug)

    # calculate attraction of edges
    for node in t_graph.nodes:
        for edge in node.children_edges:
            # calculate attraction
            attraction = calculate_block_attraction(node.value,edge.target.value,blocks,debug=debug)
            edge.weight = attraction
        
        for edge in node.parent_edges:
            # calculate attraction
            attraction = calculate_block_attraction(edge.source.value,node.value,blocks,child=False,debug=debug)
            edge.weight = attraction

    # print attraction
    if debug:
        print('Attraction:')
        for node in t_graph.nodes:
            print(node.id,node.children_edges,'|',node.parent_edges)

    return t_graph



def calculate_block_attraction(block:OCR_Tree,target_block:OCR_Tree,blocks:list[OCR_Tree],direction:str=None,child:bool=True,debug:bool=False)->int:
    '''Calculate attraction between blocks\n

    Attraction is calculated based on block's characteristics such as type, size, position, etc\n

    0: No attraction\n'''
    if debug:
        print('Calculating attraction between',block.id,target_block.id,'|','child' if child else 'parent')

    # calculate distances for normalization
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

    # estimate direction, if not given
    ## below,above,right,left
    if not direction:
        # above or below
        if block.box.intersects_box(target_block.box,extend_vertical=True):
            if block.box.top > target_block.box.top:
                direction = 'above'
            else:
                direction = 'below'
        # right or left
        elif block.box.intersects_box(target_block.box,extend_horizontal=True):
            if block.box.left < target_block.box.left:
                direction = 'right'
            else:
                direction = 'left'
        elif target_block.box.is_inside_box(block.box):
            direction = 'below'
        elif block.box.is_inside_box(target_block.box):
            direction = 'above'
        elif target_block.box.top < block.box.top:
            direction = 'above'
        else:
            direction = 'below'

    below_blocks = block.boxes_directly_below(blocks)
    
    if debug:
        print('Below blocks:',[b.id for b in below_blocks])

    right_blocks = block.boxes_directly_right(blocks)


    if debug:
        print('Right blocks:',[b.id for b in right_blocks])

    top_blocks = block.boxes_directly_above(blocks)

    if debug:
        print('Top blocks:',[b.id for b in top_blocks])

    if (direction in ['below','right']) or (direction in ['above','left']):
        attraction += 20
    elif direction in ['above','right'] and len(below_blocks) == 0:
        attraction += 20
        
    if debug:
        print('Direction:',direction,'Attraction:',attraction)


    # distance
    # normalize distance
    ## lower distance means higher attraction
    ## max attraction increase is 20
    ### exception, no below blocks (probably prefers upper block)
    border_point = {'above':'top','below':'bottom','left':'left','right':'right'}[direction]
    distance = block.box.distance_to(target_block.box,border=border_point)
    distance = abs((distance-min_distance)/(max_distance-min_distance))

    ## more atraction to blocks below
    ## or right blocks in conditional cases
    block_area = block.box.area()
    leftmost_block = None
    # checks for below blocks
    if below_blocks:
        below_blocks.sort(key=lambda x: x.box.left)
        leftmost_block = below_blocks[0]

        if leftmost_block == target_block:
            attraction += 10
            if debug:
                print('Leftmost block is target block','Attraction:',attraction)

        # delimiters
        below_delimiters = [b for b in below_blocks if b.type == 'delimiter']
        
        if len(below_delimiters) > 0 and block_area > 0:
            widest_delimiter = max(below_delimiters,key=lambda x: x.box.width)
            widest_delimiter:OCR_Tree
            intersection_area = widest_delimiter.box.intersect_area_box(block.box,extend_vertical=True)
            intersection_area_area = intersection_area.area()
            if direction == 'below' and intersection_area_area > 0:
                attraction -= (intersection_area_area/block_area) * 30
            elif direction != 'below' and intersection_area_area > 0:
                attraction += (intersection_area_area/block_area) * 30

            if debug:
                print('Below blocks has delimiters','Attraction:',attraction)
                print('Block area:',block_area,'Intersection area:',intersection_area_area)

    # checks for right blocks
    if right_blocks:

        # delimiters
        right_delimiters = [b for b in right_blocks if b.type == 'delimiter']
        
        if len(right_delimiters) > 0 and block_area > 0:
            widest_delimiter = max(right_delimiters,key=lambda x: x.box.height)
            widest_delimiter:OCR_Tree
            intersection_area = widest_delimiter.box.intersect_area_box(block.box,extend_horizontal=True)
            intersection_area_area = intersection_area.area()
            if direction == 'right' and intersection_area_area > 0:
                attraction -= (intersection_area_area/block_area) * 30
            elif direction != 'right' and intersection_area_area > 0:
                attraction += (intersection_area_area/block_area) * 30
            if debug:
                print('Right blocks has delimiters','Attraction:',attraction)
                print('Block area:',block_area,'Intersection area:',intersection_area_area)

    if below_blocks:
        attraction += round(20*(1-distance))
        if debug:
            print('Distance:',distance,'Attraction:',attraction)

    # intersection rate
    intersection_area = None
    if direction == 'above' or direction == 'below':
        intersection_area = target_block.box.intersect_area_box(block.box,extend_vertical=True)
    elif direction == 'right' or direction == 'left':
        intersection_area = target_block.box.intersect_area_box(block.box,extend_horizontal=True)

    target_block_area = target_block.box.area()
    if intersection_area and target_block_area > 0:
        intersection_area_area = intersection_area.area()
        ratio = 1 if intersection_area_area >= target_block_area else intersection_area_area/target_block_area
        attraction += round(20*ratio)

        if debug:
            print('Block encompasses target block','Attraction:',attraction)

    if below_blocks:
        if target_block in below_blocks:
            attraction += 20
            if debug:
                print('Target block is below','Attraction:',attraction)
    else:
        if direction in ['right','above']:
            attraction += 40
            if debug:
                print(f'Direction: {direction} - No below blocks','Attraction:',attraction)

            # if target block has no above blocks, more attraction
            if not target_block.boxes_directly_above(blocks):
                attraction += 20
                if debug:
                    print('Target block has no above blocks','Attraction:',attraction)
    
    if direction in ['below','right']:
        # if below block's width encompasses both block and target, more attraction
        if below_blocks:
            for below_block in below_blocks:
                if below_block != target_block and below_block.box.within_horizontal_boxes(block.box,range=0.3,only_self=True) and\
                        below_block.box.within_horizontal_boxes(target_block.box,range=0.3,only_self=True):
                    attraction += 20
                    if debug:
                        print('Below block encompasses block and target','Attraction:',attraction)

                    # shared child
                    blocks_above_encopassing_block = below_block.boxes_directly_above(blocks)
                    if blocks_above_encopassing_block and \
                        len([b for b in blocks_above_encopassing_block if b.id in [block.id,target_block.id]]) == 2:
                        attraction += 20
                        if debug:
                            print('Block and target block share child','Attraction:',attraction)
                    break
        # top block encompasses both block and target, more attraction
        if top_blocks:
            for top_block in top_blocks:
                if top_block != target_block and top_block.box.within_horizontal_boxes(block.box,range=0.3,only_self=True) and\
                        top_block.box.within_horizontal_boxes(target_block.box,range=0.3,only_self=True):
                    attraction += 20
                    if debug:
                        print('Top block encompasses block and target','Attraction:',attraction)

                    # shared parent
                    blocks_below_encopassing_block = top_block.boxes_directly_below(blocks)
                    if blocks_below_encopassing_block and \
                        len([b for b in blocks_below_encopassing_block if b.id in [block.id,target_block.id]]) == 2:
                        attraction += 20
                        if debug:
                            print('Block and target block share parent','Attraction:',attraction)

                    break



    # title
    ## title are very atracted to non title blocks
    ### below blocks are more atracted than right blocks
    ### right blocks are more attracted if below block is delimiter
    if block.type == 'title':
        if debug:
            print('Block is title','Attraction:',attraction)

        if direction == 'below':
            attraction += 20
            if debug:
                print('Target block is below','Attraction:',attraction)
                
        if target_block.type != 'title':
            attraction += 20
            if debug:
                print('Target block is not title','Attraction:',attraction)

            if target_block.type == 'text':
                if direction == 'below' and target_block.start_text == True:
                    attraction += 10
                    if debug:
                        print('Target block is text and text is started','Attraction:',attraction)
            
    # image
    ## images are very atracted to caption blocks
    elif block.type == 'image':
        if debug:
            print('Block is image','Attraction:',attraction)
        if target_block.type == 'caption':
            attraction += 50
            if debug:
                print('Target block is caption','Attraction:',attraction)
    
    # text
    ## for more than one line of text
    ## text is dependent on its content
    ## unfinished text is more atracted to unstarted text
    ## text is more attracted to text below it
    ### text to the right is more attracted if below block is delimiter
    ## unfineshed text is less atracted to non text block
    elif block.type == 'text':
        n_lines = len(block.get_boxes_level(4))
        if debug:
            print('Block is text',block.start_text,block.end_text,'Attraction:',attraction)
        if target_block.type =='text':
            if debug:
                print('Target block is text',target_block.start_text,target_block.end_text,'Attraction:',attraction)
            
            if n_lines > 1 and block.end_text == False and target_block.start_text == False:
                attraction += 50
                if debug:
                    print('Block text is not finished and target block text is not started','Attraction:',attraction)
            elif n_lines > 1 and block.end_text == True and target_block.start_text == True:
                attraction += 10
                if debug:
                    print('Block text is finished and target block text is started','Attraction:',attraction)

            if direction == 'below':
                if debug:
                    print('Target block is below','Attraction:',attraction)
                attraction += 20
            else:
                if debug:
                    print(f'Direction: {direction}','Attraction:',attraction)
                # text content

                if below_blocks:
                    if debug:
                        print('Bellow blocks:',[block.id for block in below_blocks],'Attraction:',attraction)
                    if not [b for b in below_blocks if b.type == 'text']:
                        attraction += 10
                        if debug:
                            print('No text directly below','Attraction:',attraction)
            

        ## unfineshed text is less atracted to not non-started text block
        elif n_lines > 1 and block.end_text == False and (target_block.type != 'text'or target_block.start_text == True):
            attraction -= 20
            if debug:
                print('Target block is not text and block text is not finished','Attraction:',attraction)


    if debug:
        print('Attraction:',attraction)
    return attraction



def graph_isolate_articles(graph:Graph,order_list:list=None,logs:bool=False)->list[OCR_Tree]:
    '''Isolate articles in topologic graph\n'''
    # sort nodes
    if not order_list: 
        order_list = sort_topologic_order(graph,sort_weight=True)

    if logs:
        print('Order list:',order_list)

    # isolate articles
    ## a new article begins when a title block is found and current article is not empty, unless it's last block is a title
    ## a new article ends when another title block is found and current article is not empty
    articles = []
    current_article = []
    has_title = False
    for node_id in order_list:
        node = graph.get_node(node_id)
        node:Node
        if node.value.type == 'title':
            if current_article and has_title:
                # if last element in article is not a title, create new article
                if not current_article[-1].type == 'title':
                    articles.append(current_article)
                    current_article = []
                    has_title = True
            else:
                has_title = True
        current_article.append(node.value)

    # add last article
    if current_article:
        articles.append(current_article)

    if logs:
        print('Articles:',len(articles))

    return articles




def order_ocr_tree(image_path:str,ocr_results:OCR_Tree,area:list[Box]=None,ignore_delimiters:bool=False,
                   target_segments:list[str]=['body'],next_node_filter:any=None,debug:bool=False)->list[OCR_Tree]:
    '''Calculates level 2 OCR Tree reading order and returns these blocks in an ordered list'''
    ordered_blocks = []
    header = None
    columns_area = None
    footer = None

    if area is None:
        areas = segment_document(image=image_path,target_segments=target_segments)
        header = areas[0]
        columns_area = areas[1]
        footer = areas[2]
    else:
        if len(area) >= len(target_segments):
            i = 0
            if 'header' in target_segments:
                header = area[i]
                i += 1
            if 'body' in target_segments:
                columns_area = area[i]
                i += 1
            if 'footer' in target_segments:
                footer = area[i]
        else:
            raise ValueError('Area must have same length as target segments')
        
    # clean areas
    if header and not header.valid():
        header = None

    if columns_area and not columns_area.valid():
        columns_area = None

    if footer and not footer.valid():
        footer = None

    if 'header' in target_segments and header:
        t_graph = topologic_graph(ocr_results,area=header,clean_graph=False,debug=debug)
    
        if t_graph:
            order_list = sort_topologic_order(t_graph,sort_weight=False,log=True,debug=debug)

            if debug:
                print('Order list:',order_list)

            for block_id in order_list:
                block = t_graph.get_node(block_id).value
                ordered_blocks.append(block)

    if 'body' in target_segments and columns_area:
        # run topologic_order context
        t_graph = topologic_order_context(ocr_results,area=columns_area,ignore_delimiters=ignore_delimiters,
                                        debug=debug)

        if t_graph:
            order_list = sort_topologic_order(t_graph,sort_weight=True,next_node_filter=next_node_filter,
                                            log=True,debug=debug)

            if debug:
                print('Order list:',order_list)

            for block_id in order_list:
                block = t_graph.get_node(block_id).value
                ordered_blocks.append(block)

    if 'footer' in target_segments and footer:
        # run topologic_order context
        t_graph = topologic_graph(ocr_results,area=footer,clean_graph=False,debug=debug)

        if t_graph:

            order_list = sort_topologic_order(t_graph,sort_weight=False,log=True,debug=debug)

            if debug:
                print('Order list:',order_list)

            for block_id in order_list:
                block = t_graph.get_node(block_id).value
                ordered_blocks.append(block)

    return ordered_blocks



def extract_articles(image_path:str,ocr_results:OCR_Tree,ignore_delimiters:bool=False,
                     calculate_reading_order:bool=True,target_segments:list[str]=['header','body','footer'],
                     next_node_filter:any=None,logs:bool=False,debug:bool=False)->Tuple[list[int],list[OCR_Tree]]:
    '''Extract articles from document using OCR results and image information. Articles are assumed to only be in body segment of target.'''

    delimiters = [b.box for b in ocr_results.get_boxes_type(level=2,types=['delimiter'])]
    _,body,_ = segment_document_delimiters(image=image_path,delimiters=delimiters,target_segments=target_segments,debug=debug)
    columns_area = body
    print('Columns area:',columns_area)

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results,area=columns_area,ignore_delimiters=ignore_delimiters,debug=debug)

    if calculate_reading_order:
        order_list = sort_topologic_order(t_graph,sort_weight=True,next_node_filter=next_node_filter,log=logs,debug=debug)
    else:
        # current order of ids
        ## small consideration if delimiters are ignored
        order_list = [block.id for block in ocr_results.get_boxes_level(2,ignore_type=[] if not ignore_delimiters else ['delimiter']) if t_graph.contains_id(block.id)]


    # isolate articles
    articles = graph_isolate_articles(t_graph,order_list=order_list,logs=debug)


    return order_list,articles