import abc

class Singleton(abc.ABCMeta):
    _instances = {}
    def __call__(cls, *args, **kwds):
        if cls not in cls._instances:
            instance = super().__call__(*args,**kwds)
            cls._instances[cls] = instance
        return cls._instances[cls]