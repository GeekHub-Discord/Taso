import json
import getpass


class NoConfigLoadedError(Exception):
    def __init__(self, message, errors):
        super(Exception, self).__init__(message)
        self.errors = errors


class NoKeyFoundError(Exception):
    def __init__(self, message, errors):
        super(KeyError, self).__init__(message)
        self.errors = errors


class ConfigGenerator():
    def __init__(self):
        self.__config = dict()
        with open("./config/config.sample.json", 'r') as f:
            self.__sample_config = json.load(f)

    def bot_setup(self):
        special = ['token']
        for key in self.__sample_config:
            if key in special:
                special_key = getpass.getpass(prompt=f"{key}: ")
                self.__config[key] = special_key
            elif isinstance(self.__sample_config[key], list):
                self.__config[key] = list()
                keys = input(f"{key}: ")
                for i in keys.split(' '):
                    self.__config[key].append(i)
            else:
                key_input = input(f"{key}: ")
                self.__config[key] = key_input
        with open("./config/config.json", "w") as f:
            json.dump(self.__config, f)
        return self.__config


class botConfig():
    def __init__(self):
        self.__config = dict()
        try:
            with open('./config/config.json', 'r') as f:
                self.__config = json.load(f)
        except FileNotFoundError as e:
            self.__config = ConfigGenerator().bot_setup()
        for attr in self.__config:
            setattr(self.__class__, attr, self.__config[attr])


class Config():
    def __init__(self, configFile):
        self.configFile = configFile

    def load(self):
        with open(self.configFile, 'r') as conf:
            self.data = json.load(conf)

    def get(self, key):
        try:
            value = self.data[key]
        except KeyError as e:
            raise NoKeyFoundError(f"Specified key, {key} not in config file")
        except NameError as e:
            raise NoConfigLoadedError("No config file loaded!")
        return value

    def save(self, key, value):
        try:
            self.data[key] = value
        except NameError as e:
            self.data = dict()
            self.data[key] = value
        with open(self.configFile, 'w') as conf:
            json.dump(self.data, conf)
