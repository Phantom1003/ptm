"""
Module for enabling string division operator in Python.
"""

import ctypes

# from forbidden fruit

Py_ssize_t = ctypes.c_int64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_int32

class PyObject(ctypes.Structure):
    def incref(self):
        self.ob_refcnt += 1

    def decref(self):
        self.ob_refcnt -= 1

class PyFile(ctypes.Structure):
    pass

PyObject_p = ctypes.py_object
Inquiry_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p)
# return type is void* to allow ctypes to convert python integers to
# plain PyObject*
UnaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p)
BinaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, PyObject_p)
TernaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, PyObject_p, PyObject_p)
LenFunc_p = ctypes.CFUNCTYPE(Py_ssize_t, PyObject_p)
SSizeArgFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, Py_ssize_t)
SSizeObjArgProc_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, Py_ssize_t, PyObject_p)
ObjObjProc_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, PyObject_p)

FILE_p = ctypes.POINTER(PyFile)

# https://docs.python.org/3/c-api/typeobj.html#number-object-structures
# https://docs.python.org/3/c-api/typeobj.html#pytypeobject-definition
class PyNumberMethods(ctypes.Structure):
    _fields_ = [
    ('nb_add', BinaryFunc_p),
    ('nb_subtract', BinaryFunc_p),
    ('nb_multiply', BinaryFunc_p),
    ('nb_remainder', BinaryFunc_p),
    ('nb_divmod', BinaryFunc_p),
    ('nb_power', BinaryFunc_p),
    ('nb_negative', UnaryFunc_p),
    ('nb_positive', UnaryFunc_p),
    ('nb_absolute', UnaryFunc_p),
    ('nb_bool', Inquiry_p),
    ('nb_invert', UnaryFunc_p),
    ('nb_lshift', BinaryFunc_p),
    ('nb_rshift', BinaryFunc_p),
    ('nb_and', BinaryFunc_p),
    ('nb_xor', BinaryFunc_p),
    ('nb_or', BinaryFunc_p),
    ('nb_int', UnaryFunc_p),
    ('nb_reserved', ctypes.c_void_p),
    ('nb_float', UnaryFunc_p),

    ('nb_inplace_add', BinaryFunc_p),
    ('nb_inplace_subtract', BinaryFunc_p),
    ('nb_inplace_multiply', BinaryFunc_p),
    ('nb_inplace_remainder', BinaryFunc_p),
    ('nb_inplace_power', TernaryFunc_p),
    ('nb_inplace_lshift', BinaryFunc_p),
    ('nb_inplace_rshift', BinaryFunc_p),
    ('nb_inplace_and', BinaryFunc_p),
    ('nb_inplace_xor', BinaryFunc_p),
    ('nb_inplace_or', BinaryFunc_p),

    ('nb_floor_divide', BinaryFunc_p),
    ('nb_true_divide', BinaryFunc_p),
    ('nb_inplace_floor_divide', BinaryFunc_p),
    ('nb_inplace_true_divide', BinaryFunc_p),

    ('nb_index', BinaryFunc_p),

    ('nb_matrix_multiply', BinaryFunc_p),
    ('nb_inplace_matrix_multiply', BinaryFunc_p),
    ]

class PySequenceMethods(ctypes.Structure):
    _fields_ = [
        ('sq_length', LenFunc_p),
        ('sq_concat', BinaryFunc_p),
        ('sq_repeat', SSizeArgFunc_p),
        ('sq_item', SSizeArgFunc_p),
        ('was_sq_slice', ctypes.c_void_p),
        ('sq_ass_item', SSizeObjArgProc_p),
        ('was_sq_ass_slice', ctypes.c_void_p),
        ('sq_contains', ObjObjProc_p),
        ('sq_inplace_concat', BinaryFunc_p),
        ('sq_inplace_repeat', SSizeArgFunc_p),
    ]

class PyMappingMethods(ctypes.Structure):
    pass

class PyTypeObject(ctypes.Structure):
    pass

class PyAsyncMethods(ctypes.Structure):
    pass


PyObject._fields_ = [
    ('ob_refcnt', Py_ssize_t),
    ('ob_type', ctypes.POINTER(PyTypeObject)),
]

PyTypeObject._fields_ = [
    # varhead
    ('ob_base', PyObject),
    ('ob_size', Py_ssize_t),
    # declaration
    ('tp_name', ctypes.c_char_p),
    ('tp_basicsize', Py_ssize_t),
    ('tp_itemsize', Py_ssize_t),
    ('tp_dealloc', ctypes.CFUNCTYPE(None, PyObject_p)),
    ('printfunc', ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, FILE_p, ctypes.c_int)),
    ('getattrfunc', ctypes.CFUNCTYPE(PyObject_p, PyObject_p, ctypes.c_char_p)),
    ('setattrfunc', ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, ctypes.c_char_p, PyObject_p)),
    ('tp_as_async', ctypes.CFUNCTYPE(PyAsyncMethods)),
    ('tp_repr', ctypes.CFUNCTYPE(PyObject_p, PyObject_p)),
    ('tp_as_number', ctypes.POINTER(PyNumberMethods)),
    ('tp_as_sequence', ctypes.POINTER(PySequenceMethods)),
    ('tp_as_mapping', ctypes.POINTER(PyMappingMethods)),
    ('tp_hash', ctypes.CFUNCTYPE(ctypes.c_int64, PyObject_p)),
    ('tp_call', ctypes.CFUNCTYPE(PyObject_p, PyObject_p, PyObject_p, PyObject_p)),
    ('tp_str', ctypes.CFUNCTYPE(PyObject_p, PyObject_p)),
    ('tp_getattro', ctypes.c_void_p),  # Type not declared yet
    ('tp_setattro', ctypes.c_void_p),  # Type not declared yet
    ('tp_as_buffer', ctypes.c_void_p),  # Type not declared yet
    ('tp_flags', ctypes.c_void_p),  # Type not declared yet
    ('tp_doc', ctypes.c_void_p),  # Type not declared yet
    ('tp_traverse', ctypes.c_void_p),  # Type not declared yet
    ('tp_clear', ctypes.c_void_p),  # Type not declared yet
    ('tp_richcompare', ctypes.c_void_p),  # Type not declared yet
    ('tp_weaklistoffset', ctypes.c_void_p),  # Type not declared yet
    ('tp_iter', ctypes.c_void_p),  # Type not declared yet
    ('iternextfunc', ctypes.c_void_p),  # Type not declared yet
    ('tp_methods', ctypes.c_void_p),  # Type not declared yet
    ('tp_members', ctypes.c_void_p),  # Type not declared yet
    ('tp_getset', ctypes.c_void_p),  # Type not declared yet
    ('tp_base', ctypes.c_void_p),  # Type not declared yet
    ('tp_dict', ctypes.c_void_p),  # Type not declared yet
    ('tp_descr_get', ctypes.c_void_p),  # Type not declared yet
    ('tp_descr_set', ctypes.c_void_p),  # Type not declared yet
    ('tp_dictoffset', ctypes.c_void_p),  # Type not declared yet
    ('tp_init', ctypes.c_void_p),  # Type not declared yet
    ('tp_alloc', ctypes.c_void_p),  # Type not declared yet
    ('tp_new', ctypes.CFUNCTYPE(PyObject_p, PyObject_p, PyObject_p, ctypes.c_void_p)),
    # More struct fields follow but aren't declared here yet ...
]


# redundant dict of pointee types, because ctypes doesn't allow us
# to extract the pointee type from the pointer
PyTypeObject_as_types_dict = {
    'tp_as_async': PyAsyncMethods,
    'tp_as_number': PyNumberMethods,
    'tp_as_sequence': PySequenceMethods,
    'tp_as_mapping': PyMappingMethods,
}

_str_truediv = ctypes.CFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object)(lambda self, other: self + '/' + other)

def enable_str_truediv():
    tyobj = PyTypeObject.from_address(id(str))
    tp_as = getattr(tyobj, 'tp_as_number')[0]
    setattr(tp_as, "nb_true_divide", _str_truediv)
