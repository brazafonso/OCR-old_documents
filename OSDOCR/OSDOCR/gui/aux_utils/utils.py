from typing import Union
import PySimpleGUI as sg
import cv2
import numpy as np

normal_image_size = (600,800)
window_sizes = [
    {   
        'window_size':(3840,2160),
        'normal_image_size':(1300,1700),
    },
    {
        'window_size':(2560,1377),
        'normal_image_size':(1000,1400),
    },
    {
        'window_size':(1536,801),
        'normal_image_size':(600,800),
    },
    {
        'window_size':(1280,720),
        'normal_image_size':(600,800),
    },
    {
        'window_size':(800,600),
        'normal_image_size':(400,600),
    }
]
    


def update_sizes(window:sg.Window):
    '''Update window sizes, using window size dict and current window size'''
    global normal_image_size
    print(f'Current window size: {window.size}')
    current_window_size = np.array(window.size)
    closest_window_size = None
    closest_window_size_dist = None
    new_window_size_dict = None
    for window_size_dict in window_sizes:
        window_size = np.array(window_size_dict['window_size'])
        if closest_window_size is None:
            closest_window_size = window_size
            closest_window_size_dist = abs(np.linalg.norm(current_window_size-window_size))
            new_window_size_dict = window_size_dict

        elif abs(np.linalg.norm(current_window_size-window_size)) < closest_window_size_dist:
            closest_window_size = window_size
            closest_window_size_dist = abs(np.linalg.norm(current_window_size-window_size))
            new_window_size_dict = window_size_dict


    if closest_window_size is not None:
        normal_image_size = new_window_size_dict['normal_image_size']
    
    


def update_image_element(window:sg.Window,image_element:str,new_image:Union[str,cv2.typing.MatLike],size:tuple=None):
    '''Update image element'''
    size = size or normal_image_size
    if type(new_image) in [str,np.ndarray]:
        image = None
        bio = None
        if type(new_image) == str:
            image = cv2.imread(new_image)
        else:
            image = new_image

        image = cv2.resize(image,size)
        bio = cv2.imencode('.png',image)[1].tobytes()
        window[image_element].update(data=bio,visible=True)
        window.refresh()


def place(elem):
    '''
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    '''
    return sg.Column([[elem]], pad=(0,0))


def collapse(layout, key:str,visible:bool=True,vertical_alignment:str='top'):
    """
    Helper function that creates a Column that can be later made hidden, thus appearing "collapsed"
    :param layout: The layout for the section
    :param key: Key used to make this seciton visible / invisible
    :param visible: Whether the section should be visible by default
    :param vertical_alignment: The vertical alignment of the section
    :return: A pinned column that can be placed directly into your layout
    :rtype: sg.pin
    """
    return sg.pin(sg.Column(layout, key=key,visible=visible,expand_y=True),vertical_alignment=vertical_alignment,expand_y=True)



def rgb_to_hex(rgb:tuple[int,int,int]) -> str:
    '''Convert rgb tuple to hex string'''
    return '#%02x%02x%02x' % rgb


def hex_to_rgb(hex:str,normalize:bool=False) -> tuple[int,int,int]:
    '''Convert hex string to rgb tuple'''
    if hex[0] == '#':
        hex = hex[1:]
        
    color = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

    if normalize:
        color = tuple(c/255 for c in color)

    return color


def get_average_inverse_color(image:Union[str,cv2.typing.MatLike])->tuple:
    '''Get average inverse color of image. Returns tuple (R,G,B) normalized to 0-1'''
    if isinstance(image,str):
        image = cv2.imread(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    average_color = np.average(image, axis=(0, 1))
    inverted = 255 - average_color

    return tuple(inverted/255)