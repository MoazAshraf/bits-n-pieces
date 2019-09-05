import unittest
from unittest import TestCase

from bitsnpieces.bencode import decoder
from collections import OrderedDict


class TestDecodeInt(TestCase):
    def test_decode_int_123(self):
        self.assertEqual(decoder.decode_int(b'i123e'), 123)
    
    def test_decode_int_zero(self):
        self.assertEqual(decoder.decode_int(b'i0e'), 0)
    
    def test_decode_int_neg123(self):
        self.assertEqual(decoder.decode_int(b'i-123e'), -123)
    
    def test_decode_int_negzero_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i-0e')
    
    def test_decode_int_leadingzero_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i03e')
    
    def test_decode_int_2leadingzeros_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i003e')
    
    def test_decode_int_negleadingzero_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i-03e')
    
    def test_decode_int_2negleadingzeros_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i-003e')
    
    def test_decode_int_empty_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'ie')
    
    def test_decode_int_emptyneg_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_int(b'i-e')

class TestDecodeStr(TestCase):
    def test_decode_str_helloworld(self):
        self.assertEqual(decoder.decode_str(b'11:hello world'), b'hello world')
    
    def test_decode_str_helloworldlonglength_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_str(b'11:hello')
    
    def test_decode_str_helloworldshortlength(self):
        self.assertEqual(decoder.decode_str(b'5:hello world'), b'hello')

    def test_decode_str_empty(self):
        self.assertEqual(decoder.decode_str(b'0:'), b'')
    
    def test_decode_str_emptylonglength_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_str(b'4:')
    
    def test_decode_str_emptyshortlength(self):
        self.assertEqual(decoder.decode_str(b'0:hello'), b'')

class TestDecodeList(TestCase):
    def test_decode_list_spam(self):
        self.assertEqual(decoder.decode_list(b'l4:spame'), [b'spam'])
    
    def test_decode_list_spameggs123(self):
        self.assertEqual(decoder.decode_list(b'l4:spam4:eggsi123ee'), [b'spam', b'eggs', 123])
    
    def test_decode_list_empty(self):
        self.assertEqual(decoder.decode_list(b'le'), [])
    
    def test_decode_list_nestedlist(self):
        self.assertEqual(decoder.decode_list(b'll4:spam4:eggsi123eee'), [[b'spam', b'eggs', 123]])
    
    def test_decode_list_nestedlistswint(self):
        self.assertEqual(decoder.decode_list(b'll4:spam4:eggsei123ee'), [[b'spam', b'eggs'], 123])
    
    def test_decode_list_nestedlistwdict(self):
        self.assertEqual(decoder.decode_list(b'ld4:spam4:eggsei123ee'), [OrderedDict([(b'spam', b'eggs')]), 123])

class TestDecodeDict(TestCase):
    def test_decode_dict_cowmoospameggs(self):
        self.assertEqual(decoder.decode_dict(b'd3:cow3:moo4:spam4:eggse'), OrderedDict([(b'cow', b'moo'), (b'spam', b'eggs')]))
    
    def test_decode_dict_empty(self):
        self.assertEqual(decoder.decode_dict(b'de'), OrderedDict())

    def test_decode_dict_noval_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_dict(b'd3:cowe')
    
    def test_decode_dict_intkey_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_dict(b'di12e3:mooe')
    
    def test_decode_dict_listkey_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_dict(b'dli123ee3:mooe')
    
    def test_decode_dict_dictkey_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_dict(b'dd3:cowi123ee3:mooe')
    
    def test_decode_dict_nestedlist(self):
        self.assertEqual(decoder.decode_dict(b'd3:cowli123eee'), OrderedDict([(b'cow', [123])]))
    
    def test_decode_dict_nesteddict(self):
        self.assertEqual(decoder.decode_dict(b'd3:cowd3:cowli123eeee'), OrderedDict([(b'cow', OrderedDict([(b'cow', [123])]))]))

    def test_decode_dict_duplicatekey_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_dict(b'd3:cowi123e3:cow4:spame')

class TestDecode(TestCase):
    def test_decode_123(self):
        self.assertEqual(decoder.decode(b'i123e'), 123)
    
    def test_decode_helloworld(self):
        self.assertEqual(decoder.decode(b'11:hello world'), b'hello world')
    
    def test_decode_spameggs123(self):
        self.assertEqual(decoder.decode(b'l4:spam4:eggsi123ee'), [b'spam', b'eggs', 123])
    
    def test_decode_cowmoospameggs(self):
        self.assertEqual(decoder.decode(b'd3:cow3:moo4:spam4:eggse'), OrderedDict([(b'cow', b'moo'), (b'spam', b'eggs')]))
    
    def test_decode_intnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'i123')
    
    def test_decode_emptyintnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'i')
    
    def test_decode_intnostart_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'123e')

    def test_decode_listnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'l3:cowi123e')
    
    def test_decode_emptylistnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'l')
    
    def test_decode_endnostart_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'e')

    def test_decode_dictnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'd3:cowi123e')
    
    def test_decode_emptydictnoend_err(self):
        with self.assertRaises(decoder.DecodeError):
            decoder.decode(b'd')

if __name__ == '__main__':
    unittest.main()