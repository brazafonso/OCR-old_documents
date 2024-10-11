import argparse
import json
import os

file_path = os.path.dirname(os.path.realpath(__file__))

class CustomAction_upscale_image(argparse.Action):
    '''
    Custom Action for Upscaling Image
    
Options
- waifu2x
    * scale2x
    * scale4x
    
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_upscale_image, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        # fix arguments for waifu2x
        if values[0] in ['scale2x','scale4x']:
            values = ['waifu2x',values[0]]

        
        setattr(namespace, self.dest, values) 



class CustomAction_denoise_image(argparse.Action):
    '''
    Custom Action for Upscaling Image
    
Options
- waifu2x
    * [-1,0,1,2,3]
- degan_old_docs
    
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_denoise_image, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        # fix arguments for waifu2x
        if values[0] in ['-1','0','1','2','3']:
            values = ['waifu2x',values[0]]
        elif values[0] == 'waifu2x' and len(values) > 1:
            if values[1] not in ['-1','0','1','2','3']:
                return parser.error(f'Invalid denoise value: {values[1]}')

        
        setattr(namespace, self.dest, values) 


class CustomAction_tesseract_config(argparse.Action):
    '''
    Custom Action for Tesseract config
    
Options (seperated by '__')
- __dpi int 
- __l str (default 'por')
- __psm int 
- __c str (default 'preserve_interword_spaces=1')
    
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        
        super(CustomAction_tesseract_config, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        final_values = {}
        known_flags = ['dpi','l','psm','c']
        i = 0
        while i < len(values):
            if '__' in values[i]:
                flag = values[i].split('__')[-1].lower().strip()
                if flag in known_flags:
                    if len(values) > i+1:
                        if flag == 'dpi' and values[i+1].isdigit():
                            final_values[flag] = int(values[i+1])
                        elif flag == 'psm' and values[i+1].isdigit():
                            final_values[flag] = int(values[i+1])
                        else:
                            final_values[flag] = values[i+1]
                    i += 2
                else:
                    i += 1
            else:
                i += 1


        # if arguments 'target_dpi'
        # make sure tesseract dpi corresponds to target_dpi
        dpi = getattr(namespace, 'target_dpi', '300')
        
        if dpi:
            if 'dpi' in final_values:
                final_values['dpi'] = dpi
            else:
                final_values['dpi'] = dpi

        values = final_values

        setattr(namespace, self.dest, values) 



class CustomAction_output_segments(argparse.Action):
    '''
    Custom Action for Output Segments option
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_output_segments, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        # if output segments "all" is given, remove other segments
        if 'all' in values:
            values = ['all']
        setattr(namespace, self.dest, values)
        

class CustomAction_skip_method(argparse.Action):
    '''
    Custom Action for Skip Method option
    '''

    preprocessing_methods = ['auto_rotate','noise_removal','blur_removal','light_correction',
                         'image_preprocess','remove_document_margins','remove_document_images',
                         'image_upscaling','identify_document_delimiters','binarize_image']

    posprocessing_methods = ['clean_ocr','bound_box_fix_image','split_whitespace','unite_blocks',
                            'calculate_reading_order','extract_articles','posprocessing',
                            'fix_hifenization','find_titles']

    other = ['output']

    skipable_methods = ['all'] + preprocessing_methods + posprocessing_methods + other

    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_skip_method, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        # if skip method "all" is given, add all methods
        if 'all' in values:
            values = self.skipable_methods
        elif 'image_preprocess' in values:
            values = self.preprocessing_methods
        elif 'posprocessing' in values:
            values = self.posprocessing_methods

        setattr(namespace, self.dest, values) 




class CustomAction_pipeline_config(argparse.Action):
    '''
    Custom Action for Pipeline config. Reads the config file and updates namespace accordingly
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_pipeline_config, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        config_path = values[0]

        # check and load config
        if not os.path.exists(config_path):
            parser.error(f'Config file not found: {config_path}')

        try:
            config = json.load(open(config_path,'r',encoding='utf-8'))
        except Exception as e:
            parser.error(f'Error loading config file: {str(e)}')

        # update namespace
        for k,v in config.items():
            setattr(namespace, k, v)
        

class CustomAction_calibrate(argparse.Action):
    '''
    Custom Action for Calibrate option
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_calibrate, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):

        # check and fix pipeline config path (second value)
        ## if single value is given, second value is default pipeline config folder
        if len(values) == 1:
            pipeline_configs_folder = f'{file_path}/../validation/pipeline_options'
            values = [values[0],pipeline_configs_folder]

        setattr(namespace, self.dest, values)