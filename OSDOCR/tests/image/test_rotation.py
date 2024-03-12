
import os


file_path = os.path.dirname(os.path.realpath(__file__))
study_cases_folder = f'{file_path}/../../study_cases'

image_module = __import__('...src.document_image_utils.src.image')
calculate_rotation_direction_method = image_module.calculate_rotation_direction

def test_rotation_direction_counter_clockwise_1():
    rotated_image = f'{study_cases_folder}/rotated/1928_0001.tif'
    assert calculate_rotation_direction_method(rotated_image) == 'counter_clockwise'

def test_rotation_direction_clockwise_1():
    rotated_image = f'{study_cases_folder}/rotated/1928_0002.tif'
    assert calculate_rotation_direction_method(rotated_image) == 'clockwise'

def test_rotation_direction_clockwise_2():
    rotated_image = f'{study_cases_folder}/rotated/1928_0008.tif'
    assert calculate_rotation_direction_method(rotated_image) == 'clockwise'


