'''Module for text manipulation'''

import re


def fix_hifenization(text:str)->str:
    '''Fix hifenization in text.
    
    Solves cases:
    
    - Word continuing in next line
    - Words separated by hyfen with whitespaces between them'''
    if text.strip() == '': return text

    text = re.sub(r'(\w)[\r\t\f\v ]*-(\s*\n\s*-*)([a-z0-9_])',r'\1\3',text,re.MULTILINE)
    text = re.sub(r'(\w)[\r\t\f\v ]*-[\r\t\f\v ]*([a-z0-9_])',r'\1-\2',text)

    return text
    