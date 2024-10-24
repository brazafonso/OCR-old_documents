'''Module for journal article output'''

import os
import re
from OSDOCR.ocr_tree_module.ocr_tree_analyser import analyze_text
from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.aux_utils.box import Box
from OSDOCR.output_module.text import fix_hifenization


class Article:
    '''Class that represents a journal article\n
    Stores the text of the article, its title, authors, etc.; as well as its bounding box'''



    def __init__(self,*args):
        '''Initialize Article object\n
        Available constructors:\n
        Article(ocr_tree:ocr_tree)\n
        Article(title:str,authors:list[str],abstract:str,body:str,bounding_box:Box)\n
        '''
        self.title = None
        self.subtitle = []
        self.authors = []
        self.abstract = None
        self.body = []
        self.bounding_box = None
        self.original_ocr_tree = None
        self.metadata = None
        self.sorted = False
        # single arg (ocr_tree)
        if isinstance(args[0],OCR_Tree):
            ocr_tree = [args[0]]
            args[0] = ocr_tree
            self.from_ocr_trees(*args)
        elif isinstance(args[0],list):
            self.from_ocr_trees(*args)
        # multiple args (title, authors, etc)
        else:
            self.init(*args)



    def from_ocr_trees(self,ocr_trees:list[OCR_Tree],conf:int=0):
        '''Initialize Article object from list of ocr_tree objects'''
        # create original ocr box
        self.original_ocr_tree = OCR_Tree(
            {'level':1,'page_num':0,'block_num':0,'par_num':0,'line_num':0,
             'word_num':0,'box':Box(0,0,0,0)}
             )
        self.original_ocr_tree.children = ocr_trees


        # analyze text
        text_analysis = analyze_text(self.original_ocr_tree)
        # print('article analysis',text_analysis)


        # get title
        ## biggest box before normal text
        potential_title_boxes = []
        abstract_boxes = []
        for ocr_tree in ocr_trees:
            if not ocr_tree.is_empty(conf=conf):
                if block_type:=ocr_tree.__getattribute__('type'):
                    if block_type == 'title':
                        potential_title_boxes.append(ocr_tree)
                    elif block_type == 'text' and potential_title_boxes:
                        break
                    else:
                        abstract_boxes.append(ocr_tree)
                else:
                    if ocr_tree.text_is_title(text_analysis['normal_text_size'],conf=conf):
                        potential_title_boxes.append(ocr_tree)
                    # break when normal text is found and there are potential title boxes
                    elif ocr_tree.is_text_size(text_analysis['normal_text_size']) and potential_title_boxes:
                        break
                    else:
                        abstract_boxes.append(ocr_tree)


        # print('potential title boxes',potential_title_boxes)
        if potential_title_boxes:
            ## get biggest box
            title_box = max(potential_title_boxes,key=lambda x: x.calculate_mean_height())
            # print('title box',title_box.to_text(),title_box.calculate_mean_height())
            self.title = title_box.to_text()
            ## get subtitle
            ## all other potential title boxes
            potential_title_boxes.remove(title_box)
            self.subtitle = [box.to_text() for box in potential_title_boxes]

        
        # abstract
        if abstract_boxes and self.title:
            self.abstract = ' '.join([box.to_text() for box in abstract_boxes])

        body_boxes = []
        if self.title:
            body_boxes = [b for b in ocr_trees if b != title_box]
        else:
            body_boxes = ocr_trees
        # create body list
        ## if box is of type image, add tuple ("image",image_path)
        ## if box is of type text, add tuple ("text",text)
        item = None
        text_delimiters = {
            5: ' ',
            4: ' \n',
            3: '\n\t',
        }
        for box in body_boxes:
           new_item = None
           if box.type == 'image':
               image_path = ''
               try:
                   image_path = box.__getattribute__('image_path')
               except:
                   pass
               new_item = ('image',image_path)
           else:
               box_text = box.to_text(conf=conf,text_delimiters=text_delimiters)
               new_item = ('text',box_text)
           
           if item:
               if item[0] == new_item[0] and item[0] == 'text':
                   # join text
                   item = (item[0],item[1] + ' ' + new_item[1])
               else:
                   self.body.append(item)
                   item = new_item
           else:
               item = new_item

        if item:
            self.body.append(item)




    def init(self,title:str,authors:list[str],abstract:str,body:list[(str,str)],bounding_box:Box):
        '''Initialize Article object from title, authors, abstract, body and bounding box'''
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.body = body
        self.bounding_box = bounding_box



    def pretty_print(self):
        '''Prints article in a pretty way'''
        text = ''
        text += f'''TITLE: {self.title}
----------------------------------'''
        text += f'''
----------------------------------
        AUTHORS: {", ".join(self.authors)}
----------------------------------'''
        text += f'''
----------------------------------
        ABSTRACT: 
        {self.abstract}
----------------------------------'''
        text += f'''
----------------------------------
        BODY: 
{self.body}

----------------------------------'''
        return text
    
    def __str__(self):
        return f'Article(title={self.title},authors={self.authors},bounding_box={self.bounding_box})'
    
    def to_md(self,output_path:str,fix_hifenization_flag:bool=True):
        '''Returns article in markdown format.Output path is optional, used to create relative image paths.'''
        text = ''
        # title
        clean_title = 'Default Title'
        if self.title:
            if fix_hifenization_flag:
                clean_title = fix_hifenization(self.title)
            clean_title = re.sub(r'\s\s+', ' ', self.title)
            clean_title = re.sub(r'\n', ' ', clean_title)
        text += f'''# {clean_title}
        '''
        
        # body
        text += f'''

------------------------------------------------------------------'''

        for item in self.body:
            if item[0] == 'text':
                box_text = item[1]
                if fix_hifenization_flag:
                    box_text = fix_hifenization(box_text)
                # small replace because of markdown specific formatting
                box_text = re.sub(r'(^|\n) *([\#\*\-])\s', r'\1\\\2 ', box_text)
                text += f'{box_text}'
            elif item[0] == 'image':
                # check if image path is valid
                text += '\n\n'
                if os.path.exists(item[1]):
                    relative_image_path = os.path.relpath(item[1],output_path)
                    text += f'![image]({relative_image_path})'
                else:
                    text += f'![image](image)'
                text += '\n\n'

        text +=f'''

------------------------------------------------------------------'''
        return text
    

    def to_txt(self,fix_hifenization_flag:bool=True):
        '''Returns article in txt format'''
        text = f'{self.title}\n'

        for item in self.body:
            if item[0] == 'text':
                if fix_hifenization_flag:
                    item = (item[0],fix_hifenization(item[1]))
                text += f'{item[1]}'
            
        text += f'\n'
        return text