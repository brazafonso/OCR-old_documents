'''Module for text manipulation'''

import re


def fix_hifenization(text:str)->str:
    '''Fix hifenization in text.
    
    Solves cases:
    
    - Word continuing in next line
    - Words separated by hyfen with whitespaces between them'''
    text = re.sub(r'(\w)[\r\t\f\v ]*-(\s*\n\s*-*)+(\w)',r'\1\3',text,re.MULTILINE)
    text = re.sub(r'(\w)[\r\t\f\v ]*-[\r\t\f\v ]*(\w)',r'\1-\2',text)

    return text

    