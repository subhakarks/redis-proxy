# this singleton is bit different.
# get_instance() will not create the first instance.
# it will just return the previously created instances.
# clients need to first instantiate an instance


class SingletonMeta(type):
    def __init__(cls, cls_name, cls_bases_tuple, cls_attr_dict):
        cls._instance = None
        super(SingletonMeta, cls).__init__(cls_name, cls_bases_tuple, cls_attr_dict)

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instance


class SingletonMixin(metaclass=SingletonMeta):
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # this should never happen
            raise Exception('SINGLETON-FATAL:: {} is not instantiated'.format(cls))
        return cls._instance
