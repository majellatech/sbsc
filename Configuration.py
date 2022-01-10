import json


class Dict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Configuration(object):
    def __init__(self, path="./config.json"):
        self.data = Dict()
        self.path = path

    @staticmethod
    def __load__(data):
        if data is None or data == "":
            raise ValueError("data cannot be empty")
        if type(data) is dict:
            return Configuration.load_dict(data)
        else:
            return data

    @staticmethod
    def load_dict(data: dict):
        result = Dict()
        for key, value in data["sbsc configuration"].items():
            result[key] = Configuration.__load__(value)
        return result

    def load_json(self, path):
        self.path = path
        with open(path, "r") as f:
            self.data = Configuration.__load__(json.loads(f.read()))

    def save_json(self):
        with open(self.path, "w") as f:
            return f.write(json.loads(str(self.data)))
    def get(self, key):
        print(self.data.keys())
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value
        self.save_json()
