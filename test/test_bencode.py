import unittest

from bitsnpieces import bencode
from collections import OrderedDict


class TestDecodeInt(unittest.TestCase):
    def test_decode_int_123(self):
        self.assertEqual(bencode.decode_int(b'i123e'), 123)
    
    def test_decode_int_zero(self):
        self.assertEqual(bencode.decode_int(b'i0e'), 0)
    
    def test_decode_int_neg123(self):
        self.assertEqual(bencode.decode_int(b'i-123e'), -123)
    
    def test_decode_int_negzero_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i-0e')
    
    def test_decode_int_leadingzero_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i03e')
    
    def test_decode_int_2leadingzeros_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i003e')
    
    def test_decode_int_negleadingzero_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i-03e')
    
    def test_decode_int_2negleadingzeros_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i-003e')
    
    def test_decode_int_empty_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'ie')
    
    def test_decode_int_emptyneg_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_int(b'i-e')

class TestDecodeStr(unittest.TestCase):
    def test_decode_str_helloworld(self):
        self.assertEqual(bencode.decode_str(b'11:hello world'), b'hello world')
    
    def test_decode_str_helloworldlonglength_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_str(b'11:hello')
    
    def test_decode_str_helloworldshortlength(self):
        self.assertEqual(bencode.decode_str(b'5:hello world'), b'hello')

    def test_decode_str_empty(self):
        self.assertEqual(bencode.decode_str(b'0:'), b'')
    
    def test_decode_str_emptylonglength_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_str(b'4:')
    
    def test_decode_str_emptyshortlength(self):
        self.assertEqual(bencode.decode_str(b'0:hello'), b'')

class TestDecodeList(unittest.TestCase):
    def test_decode_list_spam(self):
        self.assertEqual(bencode.decode_list(b'l4:spame'), [b'spam'])
    
    def test_decode_list_spameggs123(self):
        self.assertEqual(bencode.decode_list(b'l4:spam4:eggsi123ee'), [b'spam', b'eggs', 123])
    
    def test_decode_list_empty(self):
        self.assertEqual(bencode.decode_list(b'le'), [])
    
    def test_decode_list_nestedlist(self):
        self.assertEqual(bencode.decode_list(b'll4:spam4:eggsi123eee'), [[b'spam', b'eggs', 123]])
    
    def test_decode_list_nestedlistswint(self):
        self.assertEqual(bencode.decode_list(b'll4:spam4:eggsei123ee'), [[b'spam', b'eggs'], 123])
    
    def test_decode_list_nestedlistwdict(self):
        self.assertEqual(bencode.decode_list(b'ld4:spam4:eggsei123ee'), [OrderedDict([(b'spam', b'eggs')]), 123])

class TestDecodeDict(unittest.TestCase):
    def test_decode_dict_cowmoospameggs(self):
        self.assertEqual(bencode.decode_dict(b'd3:cow3:moo4:spam4:eggse'), OrderedDict([(b'cow', b'moo'), (b'spam', b'eggs')]))
    
    def test_decode_dict_empty(self):
        self.assertEqual(bencode.decode_dict(b'de'), OrderedDict())

    def test_decode_dict_noval_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_dict(b'd3:cowe')
    
    def test_decode_dict_intkey_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_dict(b'di12e3:mooe')
    
    def test_decode_dict_listkey_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_dict(b'dli123ee3:mooe')
    
    def test_decode_dict_dictkey_err(self):
        with self.assertRaises(bencode.DecodeError):
            bencode.decode_dict(b'dd3:cowi123ee3:mooe')
    
    def test_decode_dict_nestedlist(self):
        self.assertEqual(bencode.decode_dict(b'd3:cowli123eee'), OrderedDict([(b'cow', [123])]))
    
    def test_decode_dict_nesteddict(self):
        self.assertEqual(bencode.decode_dict(b'd3:cowd3:cowli123eeee'), OrderedDict([(b'cow', OrderedDict([(b'cow', [123])]))]))

if __name__ == '__main__':
    unittest.main()