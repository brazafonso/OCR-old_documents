import math
import os
import json
import re
from OSDOCR.aux_utils.box import Box
'''Module to generalize OCR result into box object\n'''


class OCR_Tree_load_error(Exception):
    '''Exception to handle OCR_Tree load errors\n'''

    def __init__(self,*args):
        super().__init__(*args)


    

class OCR_Tree:
    '''Class to represent OCR results as a tree object\n'''
    

    def __init__(self,*args):
        '''Initialize ocr_tree object\n
        Available constructors:\n
        ocr_tree() - default empty constructor\n
        ocr_tree(level:int, page_num:int, block_num:int, par_num:int, line_num:int, word_num:int, box:Box, text:str='',conf:int=-1,id=None,type:str=None)\n
        ocr_tree(json_list:list[dict])\n
        ocr_tree(json_file:str)\n'''
        self.level = None # 0 = document, 1 = page, 2 = block, 3 = paragraph, 4 = line, 5 = word
        self.page_num = None
        self.block_num = None
        self.par_num = None
        self.line_num = None
        self.word_num = None
        self.box = Box(0,0,0,0) # info about box size and position on page
        self.text = None 
        self.conf = None
        self.id = None
        self.type = None # type of box (text, image ,delimiter, table, etc)
        self.children = []
        self.parent = None
        self.start_text = None
        self.end_text = None
        if len(args) == 1:
            # from args list
            if isinstance(args[0],list):
                self.from_json(args[0])
            # from args dict
            elif isinstance(args[0],dict):
                if isinstance(args[0]['box'],dict):
                    args[0]['box'] = Box(args[0]['box'])
                self.init(**args[0])
            # from file
            elif isinstance(args[0],str):
                if os.path.isfile(args[0]):
                    with open(args[0],'r') as f:
                        self.from_json(json.load(f))
                else:
                    raise OCR_Tree_load_error(f'File {args[0]} not found')
        # normal method
        else:
            self.init(*args)

    def init(self, level:int=0, page_num:int=0, block_num:int=0, par_num:int=0, line_num:int=0, 
                 word_num:int=0, box:Box=Box(0,0,0,0), text:str='',conf:int=-1,id=None,type:str=None,**opts:dict):
        '''Initialize ocr_tree object'''
        self.level = level
        self.page_num = page_num
        self.block_num = block_num
        self.par_num = par_num
        self.line_num = line_num
        self.word_num = word_num
        self.box = box
        self.text = text
        self.conf = conf
        self.id = id
        self.type = type
        self.children = []
        self.parent = None

        if opts:
            for k,v in opts.items():
                setattr(self,k,v)

    def from_json(self,json_list:list[dict]):
        '''Load ocr_results from json list'''
        for k in json_list[0].keys():
            if k != 'box':
                setattr(self,k,json_list[0][k])
            else:
                self.box = Box(json_list[0][k])
        node_stack = [self]
        for i in range(1,len(json_list)):
            current_node = node_stack[-1]
            node = OCR_Tree(json_list[i])
            if node.level == current_node.level + 1:
                current_node.add_child(node)
                node_stack.append(node)
            elif node.level == current_node.level:
                node_stack.pop()
                current_node = node_stack[-1]
                current_node.add_child(node)
                node_stack.append(node)
            else:
                while node.level != current_node.level + 1:
                    node_stack.pop()
                    current_node = node_stack[-1]
                current_node.add_child(node)
                node_stack.append(node)


    def to_json(self):
        data = []
        self_dict = {}
        for k in self.__dict__.keys():
            if k in ['mean_height','children','parent']:
                continue
            if k not in ['box']:
                self_dict[k] = getattr(self,k)
            else:
                self_dict[k] = self.box.to_json()

        data.append(self_dict)

        for child in self.children:
            data += child.to_json()
        return data
    
    def save_json(self,file:str):
        with open(file,'w') as f:
            json.dump(self.to_json(),f,indent=4)
    
    def to_dict(self,result:dict=None):
        if not result:
            result = {k:[] for k in self.__dict__.keys()}
        for k in self.__dict__.keys():
            if k in ['mean_height']:
                continue
            if k not in ['box']:
                if k in result.keys():
                    result[k].append(getattr(self,k))
            else:
                result[k].append(self.box.to_dict())
        for child in self.children:
            child.to_dict(result)
        return result

    def copy(self):
        '''Copy ocr_tree object'''
        ocr_tree = OCR_Tree()
        # copy attributes
        for k in self.__dict__.keys():
            if k in ['children','parent','box']:
                continue
            setattr(ocr_tree,k,getattr(self,k))
        ocr_tree.box = self.box.copy()
        # copy children
        for child in self.children:
            ocr_tree.add_child(child.copy())

        return ocr_tree
    

    def attribute_is_value(self,attribute:str,value):
        '''Check if attribute is value'''
        if hasattr(self,attribute):
            attr_v = getattr(self,attribute)
            if isinstance(value,list):
                if isinstance(attr_v,list):
                    return value == attr_v
                else:
                    return attr_v in value
            else:
                return attr_v == value  
        else:
            return False
            
        

    def __str__(self):
        return f'ocr_tree(level={self.level},page_num={self.page_num},block_num={self.block_num},par_num={self.par_num},line_num={self.line_num},word_num={self.word_num},box={self.box},text={self.text},conf={self.conf},id={self.id})'

    def pretty_print(self,index:int=0):
        print('  '*index + str(self))
        for child in self.children:
            child.pretty_print(index+1)


    def add_child(self, child:'OCR_Tree'):
        '''Add child to ocr_results'''
        # fix child level (recursive)
        child.reset_level(self.level + 1)
        
        child.parent = self
        self.children.append(child)
        self.box.join(child.box)

    def reset_level(self,level:int):
        '''Reset level of ocr_results'''
        self.level = level
        for child in self.children:
            child.reset_level(level + 1)

    def id_boxes(self,level:list[int]=[2],ids:dict=None,delimiters:bool=True,area:Box=None,override:bool=True):
        '''Id boxes in ocr_results
        
        Args:
            * level (list[int], optional): Levels to id. Defaults to [2].
            * ids (dict, optional): Dict that saves the current id for each level. Defaults to None.
            * delimiters (bool, optional): If False, only id non delimiters. Defaults to True.
            * area (Box, optional): Area to id boxes. Defaults to None.'''
        if not ids:
            ids = {l:0 for l in level}
        if self.level in level:
            if (delimiters or not self.is_delimiter()) and (not area or self.box.is_inside_box(area)):
                if self.id is None or override:
                    self.id = ids[self.level]
                    ids[self.level] += 1
                else:
                    # update level id if same or greater than current level id
                    if self.id >= ids[self.level]:
                        ids[self.level] = self.id + 1
        if self.level < max(level):
            for child in self.children:
                child.id_boxes(level,ids,delimiters,area,override)

    def clean_ids(self,level:list[int]=[2]):
        '''Clean ids in ocr_results
        
        Args:
            level (list[int], optional): Levels to clean. Defaults to [2].'''
        if self.level in level:
            self.id = None
        if self.level < max(level):
            for child in self.children:
                child.clean_ids(level)

    def get_box_id(self,id:int=0,level:int=2):
        '''Get box with id and level in ocr_results'''
        group_boxes = None
        if self.level == level and self.id == id:
            group_boxes = self
        else:
            for child in self.children:
                if child.level <= level:
                    group_boxes = child.get_box_id(id,level)
                if group_boxes:
                    break
        return group_boxes
    
    def get_boxes_level(self,level:int,ignore_type:list[str]=[],conf:int=-1)->list['OCR_Tree']:
        '''Get boxes with level in ocr_results'''
        group_boxes = []
        if self.level == level and self.type not in ignore_type and (self.conf >= conf or self.level < 5):
            group_boxes.append(self)
        else:
            for child in self.children:
                if child.level <= level:
                    group_boxes += child.get_boxes_level(level,ignore_type,conf)
        return group_boxes
    
    def calculate_mean_height(self,level:int=5,conf:int=-1)->float:
        '''Get mean height of group boxes'''
        line_sum = 0
        count = 0
        boxes_level = self.get_boxes_level(level,conf=conf)
        for box in boxes_level:
            line_sum += box.box.height
            count += 1
        
        return line_sum/count if count > 0 else 0
    
    def is_text_size(self,text_size:float,mean_height:float=None,range:float=0.3,level:int=5,conf:int=-1):
        '''Check if text size is in range'''
        mean_height = mean_height
        if not mean_height:
            mean_height = self.calculate_mean_height(level,conf=conf)
        if mean_height >= text_size*(1-range) and mean_height <= text_size*(1+range):
            return True
        return False
    
    def is_empty(self,conf:int=0,only_text:bool=False)->bool:
        '''Check if box is empty'''
        if not only_text:
            if self.type in ['image']:
                return False
        text = self.to_text(conf).strip()
        has_text = re.search(r'[\w\d]+',text)
        return has_text == None
    
    def text_is_title(self,normal_text_size:int,conf:int=0,range:float=0.1,level:int=5):
        '''Check if text is title'''
        if not self.is_vertical_text(conf) and not self.is_text_size(normal_text_size,range=range,level=level) and self.calculate_mean_height(level=level) >= normal_text_size:
            return True
        return False
    

    def is_delimiter(self,conf:int=0,only_type:bool=False)->bool:
        '''Check if box is delimiter'''
        if only_type:
            return self.type in ['delimiter']
        
        if self.type in ['delimiter'] or (self.level == 2 and self.is_empty(conf)):
            if self.box.width >= self.box.height*4 or self.box.height >= self.box.width*4:
                return True
        return False
    
    def is_image(self,conf:int=0,text_size:int=0,only_type:bool=False)->bool:
        '''Check if box is image'''
        if only_type:
            return self.type in ['image']
        if self.type in ['image'] or (self.level == 2 and self.is_empty(conf=conf) and not self.is_delimiter(conf=conf)):
            if self.box.height > text_size*3:
                return True
        return False
    
    def is_vertical_text(self,conf:int=0):
        '''Check if box is vertical text'''
        if not self.is_empty(conf,only_text=True):
            lines = self.get_boxes_level(4)
            if not lines:
                return False
            # single line
            if len(lines) == 1:
                words = self.get_boxes_level(5)
                # single word
                ## check width and height
                if len(words) == 1:
                    if words[0].box.height >= words[0].box.width*2:
                        return True
                # multiple words
                ## check if most words overlap on x axis
                else:
                    # word with greatest horizontal range
                    widest_word = max(words, key=lambda x: x.box.width)
                    overlapped_words = 0
                    for word in words:
                        if word == widest_word:
                            continue
                        if word.box.within_horizontal_boxes(widest_word.box,range=0.1):
                            overlapped_words += 1
                    if overlapped_words/len(words) >= 0.5:
                        return True

            # multiple lines
            ## check if most lines overlap on y axis
            else:
                # line with greatest vertical range
                tallest_line = max(lines, key=lambda x: x.box.height)
                overlapped_lines = 0
                for line in lines:
                    if line == tallest_line:
                        continue

                    if line.box.within_vertical_boxes(tallest_line.box,range=0.1):
                        overlapped_lines += 1
                
                if overlapped_lines/len(lines) >= 0.5:
                    return True
                
        return False
    

    def get_boxes_type(self,level:int,types:list[str])->list['OCR_Tree']:
        '''Get boxes with type in ocr_results'''
        group_boxes = []
        if self.level == level and self.__getattribute__('type') and self.type in types:
            group_boxes.append(self)
        elif self.level < level:
            for child in self.children:
                group_boxes += child.get_boxes_type(level,types)
        return group_boxes


    def get_delimiters(self,search_area:Box=None,orientation:str=None,conf:int=0):
        '''Get delimiters in ocr_results\n
        Delimiters are boxes with level 2 and empty text'''
        delimiters = []
        if self.is_delimiter(conf):
            valid = True
            if search_area and not self.box.is_inside_box(search_area):
                valid = False
            if orientation and self.box.get_box_orientation() != orientation:
                valid = False
            if valid:
                delimiters.append(self)
        elif self.level < 2:
            for child in self.children:
                delimiters += child.get_delimiters(search_area,orientation,conf)
        return delimiters
    

    def to_text(self,conf:int=0,text_delimiters:dict=None):
        '''Return text in ocr_results.
        
        Arguments:
            conf {int} -- confidence threshold
            text_delimiters {dict} -- delimiters dictionary. default: {5:' ',4:'\n',3:'\n\t'}
        '''
        text = ''
        text_delimiter = ''
        line_delimiter = ''
        par_delimiter = ''
        if text_delimiters:
            text_delimiter = text_delimiters.get(5,' ')
            line_delimiter = text_delimiters.get(4,'')
            par_delimiter = text_delimiters.get(3,'')

        if self.level == 5 and self.conf >= conf:
            text += self.text + ' ' + text_delimiter
        elif self.level == 4:
            text += '\n' + line_delimiter
        elif self.level == 3:
            text += '\n\t' + par_delimiter
        for child in self.children:
            text += child.to_text(conf,text_delimiters)
        return text
    
    def remove_box_id(self,id:int,level:int=2):
        '''Remove box in ocr_results with id and level'''
        if self.level == level and self.id == id:
            if self.parent:
                self.parent.children.remove(self)
        else:
            for child in self.children:
                child.remove_box_id(id,level)


    def get_boxes_in_area(self,area:Box,level:int=2,conf:int=-1,ignore_type:list[str]=[])->list['OCR_Tree']:
        '''Get boxes in area\n
        If level is -1, get all boxes in area'''
        boxes = []
        if area:
            if (level == -1 or self.level == level ) and self.conf >= conf and self.box.is_inside_box(area) and self.type not in ignore_type:
                boxes.append(self)
            elif self.level < level or level == -1:
                for child in self.children:
                    child:OCR_Tree
                    boxes += child.get_boxes_in_area(area,level,conf,ignore_type)
        return boxes
    
    def prune_children_area(self,area:Box=None):
        '''Prune children area so that they are inside box'''
        # is parent
        if not area:
            area = self.box
        # is child, prune
        else:
            if self.box.left < area.left:
                self.box.left = area.left
            if self.box.right > area.right:
                self.box.right = area.right
            if self.box.top < area.top:
                self.box.top = area.top
            if self.box.bottom > area.bottom:
                self.box.bottom = area.bottom
        for child in self.children:
            child.prune_children_area(area)
    

    def type_color(self,rgb:bool=False,normalize:bool=False)->tuple[int,int,int]:
        '''Get block color, in bgr value, based on type
        
        Colors:
            - text: yellow
            - image: black
            - title: red
            - highlight : purple
            - delimiter: blue
            - caption : white
            - other: green'''
        color = (0,1,0) if normalize else (0,255,0)
        if self.type == 'text':
            color = (0,1,1) if normalize else (0,255,255)
        elif self.type == 'image':
            color = (0,0,0)
        elif self.type == 'title':
            color = (0,0,1) if normalize else (0,0,255)
        elif self.type == 'highlight':
            color = (0.6,0,0.8) if normalize else (153,0,204)
        elif self.type == 'delimiter':
            color = (1,0,0) if normalize else (255,0,0)
        elif self.type == 'caption':
            color = (1,1,1) if normalize else (255,255,255)

        if rgb:
            color = (color[2],color[1],color[0])
        return color
        

    def boxes_below(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks below\n
        Get blocks below block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks below block
        below_blocks = [b for b in blocks if b.box.top > self.box.top and b.box.intersects_box(block_extended)]
        return below_blocks
    
    def boxes_right(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks right\n
        Get blocks right block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.left > self.box.left and b.box.intersects_box(block_extended)]
        return right_blocks
    
    def boxes_above(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks above\n
        Get blocks above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and b.box.intersects_box(block_extended)]
        return above_blocks
    
    def boxes_left(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks left\n
        Get blocks left block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks left block
        left_blocks = [b for b in blocks if b.box.right < self.box.right and b.box.intersects_box(block_extended)]
        return left_blocks



    def boxes_directly_below(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block below\n
        Get block below block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks below block
        below_blocks = [b for b in blocks if b.box.top > self.box.top and not b.box.is_inside_box(self.box) and b.box.intersects_box(block_extended)]
        # print('below blocks',[b.id for b in below_blocks])


        ## clean directly below blocks
        ### make sure no blocks are below directly below blocks
        clean_directly_below_blocks = []
        for b1 in below_blocks:
            valid = True
            for b2 in below_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_vertical=True,inside=True)) and b1.box.top > b2.box.top:
                    valid = False
                    break
            if valid:
                clean_directly_below_blocks.append(b1)

        directly_below_blocks = clean_directly_below_blocks

        return directly_below_blocks
    

    def boxes_directly_right(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block right\n
        Get block right block, lowest distance, and intersecting with extension of block\n'''

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.right > self.box.right and not b.box.is_inside_box(self.box) and b.box.intersects_box(self.box,extend_horizontal=True) and not b.box.intersects_box(self.box,extend_vertical=True)]

        # clean directly right blocks
        ## make sure no blocks are to the right of directly right blocks
        clean_directly_right_blocks = []
        for b1 in right_blocks:
            valid = True
            for b2 in right_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_horizontal=True,inside=True)) and b1.box.left > b2.box.left:
                    valid = False
                    break
            if valid:
                clean_directly_right_blocks.append(b1)
        directly_right_blocks = clean_directly_right_blocks
                
        return directly_right_blocks
    

    def boxes_directly_above(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block above\n
        Get block above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and not b.box.is_inside_box(self.box) and b.box.intersects_box(block_extended)]
        
        ## clean directly above blocks
        ### make sure no blocks are above directly above blocks
        clean_directly_above_blocks = []
        for b1 in above_blocks:
            valid = True
            for b2 in above_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_vertical=True,inside=True)) and b1.box.bottom < b2.box.bottom:
                    valid = False
                    break
            if valid:
                clean_directly_above_blocks.append(b1)
        directly_above_blocks = clean_directly_above_blocks

        return directly_above_blocks
    

    def change_ids(self,ids:dict,level:int=2,clean:bool=True):
        '''Change ids in ocr_results'''
        if self.level == level and self.id:
            if self.id in ids:
                self.id = ids[self.id]
            elif clean:
                self.id = None
        elif self.level < level:
            for child in self.children:
                child.change_ids(ids,level,clean)



    def join_trees(self,tree:'OCR_Tree',orientation:str='vertical'):
        '''Join trees of the same level'''
        if self.level == tree.level:
            if orientation not in ['vertical','horizontal']:
                raise ValueError('orientation must be vertical or horizontal')
            if orientation == 'vertical':
                # join tree bellow self
                # add tree childrens
                ## adapt children metadata to make sense in new tree (block_num,par_num)
                if self.children:
                    last_child : OCR_Tree = self.children[-1]
                    tree.update_children_metadata(reference_block=last_child.block_num,reference_par=last_child.par_num)
                self.children += tree.children
            else:
                self_children = self.children
                tree_children = tree.children
                # when in last level, children are sorted from left to right
                if tree_children and not tree_children[0].children:
                    tree_children = sorted(tree_children,key=lambda b: b.box.left)
                # check if not intersecting
                ## add in free space
                # if intersecting, join with intersecting child
                for child in tree_children:
                    # if not lowest level, check where to insert
                    if child.children:
                        # sort children by top
                        self_children = sorted(self_children,key=lambda b: b.box.top)
                        ## check if can be inserted in top or bottom
                        if self_children[0].box.top > child.box.bottom:
                            self.children = [child] + self.children
                        elif self_children[-1].box.bottom < child.box.top:
                            self.children += [child]
                        else:
                            joined = False
                            for i in range(len(self_children)):
                                # slot to insert
                                if self_children[i].box.bottom < child.box.top and self_children[i+1].box.top > child.box.bottom:
                                    # insert in the middle
                                    self.children = self_children[:i] + [child] + self_children[i:]
                                    joined = True
                                    # if intercept, will have to use recursive join
                                elif self_children[i].box.intersects_box(child.box,extend_horizontal=True):
                                    intersect_height = min(self_children[i].box.bottom,child.box.bottom) - max(self_children[i].box.top,child.box.top)
                                    # if intersecting with more than 70% of child, join the two
                                    if intersect_height / child.box.height >= 0.7 or intersect_height / self_children[i].box.height >= 0.7:
                                        if self_children[i].children:
                                            self_children[i].join_trees(child,orientation=orientation)
                                        else:
                                            self.children = self_children[:i+1] + [child] + self_children[i+1:]
                                        joined = True
                                    else:
                                        # find lowest place to insert
                                        for j in range(i,len(self_children)):
                                            if not self_children[j].box.bottom < child.box.bottom:
                                                self.children = self_children[:j] + [child] + self_children[j:]
                                                joined = True
                                                break
                                        # if not found, insert at the end
                                        if not joined:
                                            self.children+=[child]
                                            joined = True
                                if joined:
                                    break
                    # if lowest level, insert at the end
                    else:
                        self.children += [child]
                    
                    self_children = self.children

            # join boxes
            self.box.join(tree.box)



    def update_children_metadata(self,reference_block:int,reference_par:int):
        '''Update children metadata to make sense in new tree (block_num,par_num)'''
        self.block_num = reference_block
        self.par_num += reference_par
        for child in self.children:
            child.update_children_metadata(reference_block,reference_par)


    def remove_blocks_inside(self,id:int,debug:bool=False):
        '''Remove blocks inside of block id'''
        block = self.get_box_id(id)
        if block:
            block_level = block.level
            blocks = self.get_boxes_level(block_level)

            for b in blocks:
                if b.id != id and b.box.is_inside_box(block.box):
                    if debug:
                        print(f'Removing Box : {b.id} is inside {block.id}')
                    self.remove_box_id(b.id)


    def average_conf(self,level:int=2)->tuple[int,int]:
        '''Get average confidence of boxes in level'''
        if self.level == level:
            return self.conf, 1
        else:
            conf = 0
            count = 0
            for child in self.children:
                chlid_conf, child_count = child.average_conf(level)
                conf += chlid_conf
                count += child_count
            return conf,count
        

    def update_position(self,top:int=None,left:int=None,absolute:bool=False):
        '''Update position of box and children.
        
        Arguments:
            top (int, optional): Top position. Defaults to None.
            left (int, optional): Left position. Defaults to None.
            absolute (bool, optional): If True, positions are absolute, else values are added to current position. Defaults to False.'''
        
        if not any([top,left]):
            return
        
        if top is not None:
            if absolute:
                self.box.update(top=top,bottom=top+self.box.height)
            else:
                self.box.move(y=top)
        if left is not None:
            if absolute:
                self.box.update(left=left,right=left+self.box.width)
            else:
                self.box.move(x=left)

        for child in self.children:
            child.update_position(top=top,left=left,absolute=absolute)


    def update_size(self,top:int=None,left:int=None,bottom:int=None,right:int=None,absolute:bool=False):
        '''Update size of box and children.'''

        if not any([top,left,bottom,right]):
            return

        old_top = self.box.top
        old_left = self.box.left
        old_bottom = self.box.bottom
        old_right = self.box.right

        if top is not None:
            if absolute:
                self.box.update(top=top)
            else:
                self.box.update(top=self.box.top + top)

        if left is not None:
            if absolute:
                self.box.update(left=left)
            else:
                self.box.update(left=self.box.left + left)

        if bottom is not None:
            if absolute:
                self.box.update(bottom=bottom)
            else:
                self.box.update(bottom=self.box.bottom + bottom)

        if right is not None:
            if absolute:
                self.box.update(right=right)
            else:
                self.box.update(right=self.box.right + right)

        # update children on edges
        for child in self.children:
            update_top = top is not None and child.box.top == old_top
            update_left = left is not None and child.box.left == old_left
            update_bottom = bottom is not None and child.box.bottom == old_bottom
            update_right = right is not None and child.box.right == old_right
            if update_top or update_left or update_bottom or update_right:
                new_top = top if update_top else None
                new_left = left if update_left else None
                new_bottom = bottom if update_bottom else None
                new_right = right if update_right else None
                child.update_size(top=new_top,left=new_left,bottom=new_bottom,right=new_right,absolute=absolute)



    def update_box(self,left:int=None,right:int=None,top:int=None,bottom:int=None,children:bool=False):
        '''Update box and children positions.
        
        Arguments:
            left (int, optional): Left position. Defaults to None.
            right (int, optional): Right position. Defaults to None.
            top (int, optional): Top position. Defaults to None.
            bottom (int, optional): Bottom position. Defaults to None.
            children (bool, optional): If True, adjust coordinate instead of replacing. Defaults to False.
            '''
        
        if not any([left,right,top,bottom]):
            return
        
        if left:
            if children:
                self.box.update(left=max(self.box.left,left))
            else:
                self.box.update(left=left)

        if right:
            if children:
                self.box.update(right=min(self.box.right,right))
            else:
                self.box.update(right=right)

        if top:
            if children:
                self.box.update(top=max(self.box.top,top))
            else:
                self.box.update(top=top)

        if bottom:
            if children:
                self.box.update(bottom=min(self.box.bottom,bottom))
            else:
                self.box.update(bottom=bottom)

        for child in self.children:
            child.update_box(left=left,right=right,top=top,bottom=bottom,children=True)
        
        

    


