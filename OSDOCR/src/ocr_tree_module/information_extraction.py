from ocr_tree_module.ocr_tree import OCR_Tree
from aux_utils.box import Box
from output_module.journal.article import Article
from ocr_tree_module.ocr_tree_analyser import analyze_text

def journal_template_to_text(journal_template:dict,ocr_results:OCR_Tree):
    '''Converts ocr_results to text using journal_template'''
    text = ''

    # header text
    text += '''HEADER:

'''
    header_area = journal_template['header']
    header_boxes = ocr_results.get_boxes_in_area(header_area,2)

    for box in header_boxes:
        text += box.to_text() + '\n'

    # columns text
    for i,column in enumerate(journal_template['columns']):
        text += f'''
####################################################################################################
        COLUMN {i}:

'''
        column_boxes = ocr_results.get_boxes_in_area(column,2)
        column_page = OCR_Tree(
            {'level':1,'page_num':0,'block_num':0,'par_num':0,'line_num':0,
             'word_num':0,'box':column}
             )
        column_page.children = column_boxes
        # separate column in articles
        articles = []
        ## get horizontal delimiters
        article_delimiters = []
        for box in column_boxes:
            delimiters = box.get_delimiters(orientation='horizontal')
            article_delimiters += delimiters

        if article_delimiters:
            ### order delimiters by y position
            article_delimiters.sort(key=lambda x: x.box.top)
            ### divide areas between delimiters
            article_areas = []
            for i in range(len(article_delimiters)-1):
                if i == 0:
                    upper_border = column.top
                else:
                    upper_border = article_delimiters[i-1].box.bottom
                lower_border = article_delimiters[i].box.top
                left_border = column.left
                right_border = column.right
                article_area = Box(upper_border,left_border,lower_border,right_border)
                article_areas.append(article_area)
            ### get boxes in each area
            for article_area in article_areas:
                article_boxes = ocr_results.get_boxes_in_area(article_area,2)
                article_page = OCR_Tree(
                    {'level':1,'page_num':0,'block_num':0,'par_num':0,'line_num':0,
                     'word_num':0,'box':article_area}
                     )
                article_page.children = article_boxes
                article = Article(article_page)
                articles.append(article)
            

        ## separate articles by analysing text
        else:
            text_analysis = analyze_text(column_page)
            print(text_analysis)
            article_areas = []
            ## order column boxes by y position
            column_boxes.sort(key=lambda x: x.box.top)

            ## get lower borders of articles
            i = 0 
            article_borders = []
            while i < len(column_boxes):
                # potential title
                ## new article if box is text and bigger than normal text and 
                ## last box was normal text or smaller than normal text
                if not column_boxes[i].is_empty():
                    if not column_boxes[i].is_text_size(text_analysis['normal_text_size']) and column_boxes[i].calculate_mean_height() > text_analysis['normal_text_size']:
                        if i != 0 and (column_boxes[i-1].is_text_size(text_analysis['normal_text_size']) or column_boxes[i-1].calculate_mean_height() < text_analysis['normal_text_size']):
                            print('potential new article',box.text)
                            article_borders.append(column_boxes[i].box.top)
                i += 1



            ## get article areas
            while i < len(article_borders):
                if i == 0:
                    upper_border = column.top
                else:
                    upper_border = article_borders[i]
                if i == len(article_borders)-1:
                    lower_border = column.bottom
                else:
                    lower_border = article_borders[i+1]
                left_border = column.left
                right_border = column.right
                article_area = Box(left_border,right_border,upper_border,lower_border)
                article_areas.append(article_area)
                i += 1

            if not article_areas:
                article_areas.append(column)

            ## divide column in articles
            for i in range(len(article_areas)):
                article_area = article_areas[i]
                article_boxes = ocr_results.get_boxes_in_area(article_area,2)
                if article_boxes:
                    article = Article(article_boxes)
                    articles.append(article)
                

        ## print articles
        for article in articles:
            text += article.pretty_print() + '\n'



    # footer text
    text += '''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        FOOTER:

'''
    footer_area = journal_template['footer']
    footer_boxes = ocr_results.get_boxes_in_area(footer_area,2)

    for box in footer_boxes:
        text += box.to_text() + '\n'

    return text
