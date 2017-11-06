from functools import partial

# class Philosopher():
#     __slots__ = ['a', 'b', 'c']
#     def __init__(self, **kwargs):
#         for k, v in kwargs.items():
#             setattr(self, k, v)

    # def __init_subclass__(cls, default_name, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     cls.default_name = default_name

    # setattr(self, 't', property(get_url))
    # t = property(get_url)

# class AustralianPhilosopher(Philosopher, default_name="Bruce"):
#     pass

# class FrozenStructMixin:
#     __slots__ = ('_data',)
#     def __init_subclass__(cls, fields, **kwargs):
#         cls.FIELDS = tuple(fields)
#         for i, field in enumerate(fields):
#             setattr(cls, field, property(fget=partial(lambda idx, self: self._data[idx], i)))
#
#     def __new__(cls, *args, **kwargs):
#         super_kwargs = {k: v for k, v in kwargs.items() if k not in cls.FIELDS}
#         print('--------new parent class----')
#         return super().__new__(cls, *args, **super_kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super_kwargs = {k: v for k, v in kwargs.items() if k not in self.FIELDS}
#         super().__init__(*args, **super_kwargs)
#         if hasattr(self, '_data'):
#             return
#         self._data = tuple(kwargs.get(f) for f in self.FIELDS)
#
#
# class Sample(FrozenStructMixin, fields=['surface', 'lexeme', 'pos']):
#     __slots__ = ()
#
# class TestProperty:
#     def get_el(self):
#         return 'el'
#     def __init__(self, **kwargs):
#         # property(fget=None, fset=None, fdel=None, doc=None)
#         setattr(self, 'field', 'value')
        # self._data = ('中日ドラゴンズ', '中日ドラゴンズ', '名詞')

if __name__ == '__main__':
    # sample = Sample(**dict(surface='中日ドラゴンズ', lexeme='中日ドラゴンズ', pos='名詞'))
    # print(sample.surface)
    te = TestProperty()
