
import os
from document_image_utils.image import calculate_rotation_direction


file_path = os.path.dirname(os.path.realpath(__file__))
study_cases_folder = f'{file_path}/../../../../study_cases'


def test_rotation_direction_counter_clockwise_1():
    rotated_image = f'{study_cases_folder}/rotated/1928_0001.tif'
    assert calculate_rotation_direction(rotated_image) == 'counter_clockwise'

def test_rotation_direction_clockwise_1():
    rotated_image = f'{study_cases_folder}/rotated/1928_0002.tif'
    assert calculate_rotation_direction(rotated_image) == 'clockwise'

def test_rotation_direction_clockwise_2():
    rotated_image = f'{study_cases_folder}/rotated/1928_0008.tif'
    assert calculate_rotation_direction(rotated_image) == 'clockwise'


def test_rotation_direction_none_1():
    rotated_image = f'{study_cases_folder}/ideal/AAA-13.png'
    assert calculate_rotation_direction(rotated_image) == 'none'

def test_rotation_direction_none_2():
    rotated_image = f'{study_cases_folder}/ideal/AAA-19.png'
    assert calculate_rotation_direction(rotated_image) == 'none'


