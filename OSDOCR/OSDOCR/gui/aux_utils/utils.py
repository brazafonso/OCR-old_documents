from typing import Union
import PySimpleGUI as sg
import cv2
import numpy

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
    current_window_size = window.size
    for window_size_dict in window_sizes:
        if current_window_size >= window_size_dict['window_size']:
            normal_image_size = window_size_dict['normal_image_size']
            break
    
    


def update_image_element(window:sg.Window,image_element:str,new_image:Union[str,cv2.typing.MatLike],size:tuple=None):
    '''Update image element'''
    size = size or normal_image_size
    if type(new_image) in [str,numpy.ndarray]:
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