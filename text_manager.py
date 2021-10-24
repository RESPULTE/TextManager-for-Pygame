from pygame import font as myfont
from pygame import Surface, Color
from dataclasses import dataclass
from pprint import pformat
from copy import deepcopy

myfont.init()

@dataclass
class TextBox:

    surf: Surface
    text: str
    config: dict

    def __getattr__(self, attr):
        # reroute all the attribute access of the text container class to here
        try:
            # try to provide the attribute requested, 
            orig_attr = getattr(self, attr)
            return orig_attr
        except:
            # if that's not possible, then try 
            # getting the attribute from the surface of the text container object
            try:
                orig_attr = getattr(self.surf, attr)
                return orig_attr
            except:
                # if that is STILL somehow not possible
                # just raise an exception, something invalid has been requested
                raise ValueError(f'{attr} is invalid') 


    def modify(self, **config):
        txt = config.pop('text') if 'text' in config else self.text
        self.config.update(config)

        # pass the updated config into the configurator(fancy name lmao) 
        # get the txt surf that it spits out
        # and then update the text container accordingly
        # the 'usual' assignment of the modified config to the text container is not needed 
        # as, it is already updated from the lil line above is block of text
        txt_surf = TextBox.create_surf(txt, **self.config)
        self.__dict__.update(dict(surf=txt_surf, text=txt))


    @classmethod
    def create_txt_box(cls, text: str, **config):    
        font_surf = TextBox.create_surf(text, **config)
        return cls(font_surf, text, config)
                   

    @staticmethod
    def create_surf(text: str, **config):
        '''
        generate a text surface with the pre-determined configs of the text manager
        + additional configs can be passed in as keyword arguements
        '''
        # starting setups for font object in pygame using te modified config
        font_config = myfont.SysFont(
            config['font'], 
            config['font_size']
            )

        # straight up setting the attribute for the font object using the modified config's setting
        for setting, value in config["settings"].items():
            try:
                setattr(font_config, setting, value)
            except:
                raise ValueError(f"what the heck is dis {setting}: {value}")
        # creating the actual text surface
        font_surf = font_config.render(
            text, 
            config['AA'], 
            config['font_color'], 
            config['background']
            )

        return font_surf 


class TextManager:

    '''generate text container objects with pre-determined settings'''

    def __init__(self, font, font_color, font_size, AA=False, background=False,  **settings):
        # P.S : had to change the retval of the < Color > function from pygame 
        #       into tuples because pygame.Color is unhashable
        # -> needed the hashing to do deep-copying in the < create_txt_box function >
        # --> can just use getattr and copy everything, but its a lil too verbose for my likings ://

        # mandantory attributes that defines a font
        self.font = font
        self.font_color = tuple(Color(font_color))
        self.font_size = font_size

        # optional attributes for the font rendering
        self.AA = AA
        self.background = tuple(Color(background))
        self.settings = dict(settings)

        # check if the settings passed in is a valid setting in pygame's font module
        for stg, val in settings.items():
            if not hasattr(myfont, stg, val):
                raise ValueError(f"what the heck is dis {setting}: {value}")

        # for keeping track of all the text surfaces that has been created by this text manager
        self._catalogue = {}

    @property
    def catalogue(self):
        return self._catalogue


    def create_txt(self, text, **extra_config):
        '''
        pretty self-explanatory 
        1. just creates a surface
        2. log it in the manager's catalogue  
        3. spits out a reference to the txt surface

        P.S : any changes to the text surface should therefore be done in the text manager
              so proper logging could be done
        '''

        # get a deepcopy of the text manager's configs
        # to modify with any additional configs that's passed in
        # -> getting a deepcopy is necessary to avoid any references of the actual text manager's dict being stored
        # --> in essence, deepcopy gud, shallow/normal copy bad :D
        modified_config = self.__dict__.copy()
        modified_config['settings'] = deepcopy(self.settings)
        del modified_config['_catalogue']

        # if additional configs is passed in
        # -> check if it's in the text manager's attribute(excluding the settings)
        # --> if not, verify it and set it to the copied config 
        if extra_config:
            for k, v in extra_config.items():
                if k in modified_config:
                    modified_config[k] = v
                else:
                    modified_config['settings'][k] = v

        text_box = TextBox.create_txt_box(text, **modified_config)
        self.catalogue_txt(text, text_box)

        return text_box


    def catalogue_txt(self, text, text_box):
        '''
        catalogue the text surface in the text manager's catalogue
        '''

        # generate a unique id for text manager's catalogue
        # check if the text already exists as an id in the text manager's _catalogue
        # -> if it is, set a counter and increment it until a unique id for the text can be generated
        catalogue_text = f"{text}-(0)"
        if catalogue_text in self._catalogue:
            temp_counter = 1
            while f"{text}-({temp_counter})" in self._catalogue:
                temp_counter += 1 
            catalogue_text = f"{text}-({temp_counter})"

        self._catalogue[catalogue_text] = text_box


    def set_txt_surf(self, name_id=None, setAll=False, **config):
        '''
        change the text surfaces that has been created
        + name_id: The id used for the catalogue of the text container
                   the specific index can be omitted if both name_id and setAll is given
        + setAll: set the changes to all the text container, 
                  if name_id is given, the changes will affect all the text conatiner 
                  with the same text as the name_id (minus the cataloguing index at the back)
        + config: changes to be made for the specified text surfaces
        '''

        if not setAll and not name_id:
            raise ValueError(f'expecting at least name_id or setAll as arguements')

        # if the name_id given is not in the catalogue, 
        # create a temporary catalogue_check set with all the catalogue index removed
        # if the name_id is still not found, an invalid name_id has been given, raise an error
        if name_id not in self._catalogue and name_id:
            catalogue_check = set(n_id.rsplit('-', 1)[0] for n_id in self._catalogue)
            if name_id not in catalogue_check:
                raise ValueError(f'name_id of text not found {name_id}')

        # if name_id and setAll are both specified, split the name at the end with the '-' (catalogue index)
        # --> change it to the same format as the text in the text_boxs
        if setAll and type(name_id) == str:
            if '-' in name_id:
                name_id = name_id.rsplit('-', 1)[0]

        # loop through all the text_box with the same text or catalogue id as the name_id 
        # operator 'or' can be used because:
        # case 1: if setAll and name_id is both specified: (text_box.text == name_id)
        #         - name_id will have been splitted (removed catalogue index) 
        #         - all the text_conatiner with the same text as the name_id will be changed 
        # case 2: if only name_id is specified: (id_ == name_id) 
        #         - name_id will not have been splitted 
        #         - only the specific text_box will be selected using the catalogue id as refernce
        # case 3: if only setAll is specified: (not name_id and setAll)
        #         - just change everything that's in the catalogue, pretty self explanatory
        #
        # P.S: a copy of the catalogue is used as to avoid runtime error
        #     -> deepcopy is unnessary and impossible since text container objects are unhasable and 
        #        we're not creating new text container objects anyway, we're simply modifying it
        for id_, text_box in self._catalogue.copy().items():
            if (text_box.text == name_id) or (id_ == name_id) or (not name_id and setAll):
                # get the text container out from the catalogue
                txt_container = self._catalogue.pop(id_)
                txt = config['text'] if 'text' in config else txt_container.text
                txt_container.modify(**config)
                self.catalogue_txt(txt, txt_container)


    def set_config(self, **config):
        '''
        modify the configs for the text manager
        '''
        for k, v in config.items():
            if k not in self.__dict__:
                self.verify_text_config(k)
            setattr(self, k, v)


    def __str__(self):
        return pformat(vars(self), indent=4, sort_dicts=False)


    def __getitem__(self, name):
        '''
        check all the generated text surfaces that have the same name/text
        '''
        temp_dict = {txt_id: config for txt_id, config in self._catalogue.items() if txt_id.rsplit("-", 1)[0] == name}

        return pformat(temp_dict, indent=6)
