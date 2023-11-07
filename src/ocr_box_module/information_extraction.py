from ocr_box_module.ocr_box import OCR_Box


def journal_template_to_text(journal_template:dict,ocr_results:OCR_Box):
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
        text += f'''COLUMN {i}:

'''
        column_boxes = ocr_results.get_boxes_in_area(column,2)
        for box in column_boxes:
            text += box.to_text() + '\n'

    # footer text
    text += '''FOOTER:

'''
    footer_area = journal_template['footer']
    footer_boxes = ocr_results.get_boxes_in_area(footer_area,2)

    for box in footer_boxes:
        text += box.to_text() + '\n'

    return text
