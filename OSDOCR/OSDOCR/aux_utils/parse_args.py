import argparse


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
    
    '''
    def __init__(self, *args, **kwargs):
        """
        argparse custom action.
        :param check_func: callable to do the real check.
        """
        super(CustomAction_tesseract_config, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        final_values = {}
        known_flags = ['dpi','l','psm']
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

        values = final_values
        setattr(namespace, self.dest, values) 