'''Module for journal article output'''

from ocr_box_module.ocr_box_analyser import analyze_text
from ocr_box_module.ocr_box import OCR_Box
from aux_utils.box import Box


class Article:
    '''Class that represents a journal article\n
    Stores the text of the article, its title, authors, etc.; as well as its bounding box'''



    def __init__(self,*args):
        '''Initialize Article object\n
        Available constructors:\n
        Article(ocr_box:OCR_Box)\n
        Article(title:str,authors:list[str],abstract:str,body:str,bounding_box:Box)\n
        '''
        self.title = None
        self.subtitle = []
        self.authors = []
        self.abstract = None
        self.body = None
        self.bounding_box = None
        self.original_ocr_box = None
        self.metadata = None
        # single arg (OCR_Box)
        if len(args) == 1:
            if isinstance(args[0],OCR_Box):
                self.from_ocr_box(args[0])
            elif isinstance(args[0],list):
                self.from_ocr_boxes(args[0])
            else:
                raise TypeError(f'Invalid type {type(args[0])} for Article constructor')
        # multiple args (title, authors, etc)
        else:
            self.init(*args)



    def from_ocr_boxes(self,ocr_boxes:list[OCR_Box]):
        '''Initialize Article object from list of OCR_Box objects'''
        # create original ocr box
        self.original_ocr_box = OCR_Box(
            {'level':1,'page_num':0,'block_num':0,'par_num':0,'line_num':0,
             'word_num':0,'box':Box(0,0,0,0)}
             )
        self.original_ocr_box.children = ocr_boxes

        # analyze text
        text_analysis = analyze_text(self.original_ocr_box)
        print('article analysis',text_analysis)

        # order ocr_boxes by y position
        ocr_boxes.sort(key=lambda x: x.box.top)


        # get title
        ## biggest box before normal text
        potential_title_boxes = []
        abstract_boxes = []
        for ocr_box in ocr_boxes:
            if not ocr_box.is_empty():
                if not ocr_box.is_text_size(text_analysis['normal_text_size'],range=0.6) and ocr_box.calculate_mean_height() > text_analysis['normal_text_size']:
                    potential_title_boxes.append(ocr_box)
                # break when normal text is found and there are potential title boxes
                elif ocr_box.is_text_size(text_analysis['normal_text_size']) and potential_title_boxes:
                    break
                else:
                    abstract_boxes.append(ocr_box)


        print('potential title boxes',potential_title_boxes)
        if potential_title_boxes:
            ## get biggest box
            title_box = max(potential_title_boxes,key=lambda x: x.calculate_mean_height())
            print('title box',title_box.to_text(),title_box.calculate_mean_height())
            self.title = title_box.to_text()
            ## get subtitle
            ## all other potential title boxes
            potential_title_boxes.remove(title_box)
            self.subtitle = [box.to_text() for box in potential_title_boxes]

        
        # abstract
        if abstract_boxes and self.title:
            self.abstract = ' '.join([box.to_text() for box in abstract_boxes])

        # authors
        ## TODO

        # body
        ## boxes after title
        body_boxes = []
        if self.title:
            title_box_index = ocr_boxes.index(title_box)
            body_boxes = ocr_boxes[title_box_index+1:]
        else:
            body_boxes = ocr_boxes
        self.body = ' '.join([box.to_text() for box in body_boxes])




    def init(self,title:str,authors:list[str],abstract:str,body:str,bounding_box:Box):
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