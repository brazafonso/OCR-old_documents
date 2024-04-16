import torch
import aux_utils.consts as consts
from PIL import Image
from aux_utils.misc import *
from models.DE_GAN_old_docs.enhance import run_image_enhance
import torch
from PIL import Image



def run_waifu2x(target_image:str,method:str='scale2x',model_type:str='photo',noise_level:int=1,result_image_path:str=None,log:bool=False) -> str:
    '''Run Waifu2x to clean or upscale image.
    
    Args:
        target_image (str): path to image
        method (str, optional): method to use ['scale2x','scale4x','noise']. Defaults to 'scale2x'.
        model_type (str, optional): model type ['photo','art','art_scan']. Defaults to 'photo'.
        noise_level (int, optional): noise level [-1 (None),0,1,2,3]. Defaults to 1.
        result_image_path (str, optional): path to save result. Defaults to None, in which case result will be saved to same directory.
    '''
    if log:
        print(f'Running Waifu2x | target_image: {target_image} | method: {method} | model_type: {model_type} | noise_level: {noise_level} | result_image_path: {result_image_path}')
        print('Loading model')

    model = None
    if torch.cuda.is_available():
        model = torch.hub.load("nagadomi/nunif:master", "waifu2x",
                       method=method, noise_level=noise_level, model_type=model_type,trust_repo=True).to("cuda")
    else:
        model = torch.hub.load("nagadomi/nunif:master", "waifu2x",
                       method=method, noise_level=noise_level, model_type=model_type,trust_repo=True).to("cpu")
    # model.set_mode(method, noise_level) ## if no method chosen

    if log:
        print('finished loading model')
        print('running model')

    input_image = Image.open(target_image)
    result = model.infer(input_image)
    if not result_image_path:
        result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_waifu2x.png'
    result.save(result_image_path)

    if log:
        print('finished Waifu2x')

    return result_image_path



def run_degan_old_docs(target_image:str,result_image_path:str=None,method:str='binarize',log:bool=False) -> str:
    '''Run DEGAN to clean or upscale image.
    
    Args:
        target_image (str): path to image
        result_image_path (str, optional): path to save result. Defaults to None, in which case result will be saved to same directory.
        method (str, optional): method to use ['binarize','deblur']. Defaults to 'binarize'.
    '''
    if log:
        print(f'run DEGAN - {method}')
    if not result_image_path:
        result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_{method}.png'
    run_image_enhance(method,target_image,result_image_path)

    if log:
        print(f'finished DEGAN - {method}')


    return result_image_path