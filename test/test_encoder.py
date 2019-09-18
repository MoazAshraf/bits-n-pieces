import unittest
from unittest import TestCase

from bitsnpieces.bencode import encoder
from collections import OrderedDict


class TestEncodeInt(TestCase):
    def test_encode_int_123(self):
        self.assertEqual(encoder.encode_int(123), b'i123e')
    
    def test_encode_int_zero(self):
        self.assertEqual(encoder.encode_int(0), b'i0e')
    
    def test_encode_int_neg123(self):
        self.assertEqual(encoder.encode_int(-123), b'i-123e')
    
    def test_encode_int_float_err(self):
        with self.assertRaises(encoder.EncodeError):
            encoder.encode_int(12.0)

class TestEncodeStr(TestCase):
    def test_encode_str_bhelloworld(self):
        self.assertEqual(encoder.encode_str(b'hello world'), b'11:hello world')

    def test_encode_str_bempty(self):
        self.assertEqual(encoder.encode_str(b''), b'0:')
    
    def test_encode_str_asciihelloworld(self):
        self.assertEqual(encoder.encode_str('hello world', 'ascii'), b'11:hello world')
    
    def test_encode_str_asciiempty(self):
        self.assertEqual(encoder.encode_str('', 'ascii'), b'0:')
    
    def test_encode_str_noenchelloworld_err(self):
        with self.assertRaises(encoder.EncodeError):
            encoder.encode_str('hello world')
    
    def test_encode_str_badenchelloworld_err(self):
        with self.assertRaises(LookupError):
            encoder.encode_str('hello world', 'scii')

class TestEncodeList(TestCase):
    def test_encode_list_spam(self):
        self.assertEqual(encoder.encode_list([b'spam']), b'l4:spame')
    
    def test_encode_list_spameggs123(self):
        self.assertEqual(encoder.encode_list([b'spam', b'eggs', 123]), b'l4:spam4:eggsi123ee')
    
    def test_encode_list_empty(self):
        self.assertEqual(encoder.encode_list([]), b'le')
    
    def test_encode_list_nestedlist(self):
        self.assertEqual(encoder.encode_list([[b'spam', b'eggs', 123]]), b'll4:spam4:eggsi123eee')
    
    def test_encode_list_nestedlistswint(self):
        self.assertEqual(encoder.encode_list([[b'spam', b'eggs'], 123]), b'll4:spam4:eggsei123ee')
    
    def test_encode_list_nestedlistwdict(self):
        self.assertEqual(encoder.encode_list([OrderedDict([(b'spam', b'eggs')]), 123]), b'ld4:spam4:eggsei123ee')
    
    def test_encode_list_asciistr(self):
        self.assertEqual(encoder.encode_list(['hello', 'world'], 'ascii'), b'l5:hello5:worlde')
    
    def test_encode_list_noencstr(self):
        with self.assertRaises(encoder.EncodeError):
            encoder.encode_list(['hello', 'world'])
    
    def test_encode_list_mixedstr(self):
        self.assertEqual(encoder.encode_list([b'hello', 'world'], 'ascii'), b'l5:hello5:worlde')
    
    def test_encode_list_tuple(self):
        self.assertEqual(encoder.encode_list((1,b'stuff')), b'li1e5:stuffe')

class TestEncodeDict(TestCase):
    def test_encode_dict_cowmoospameggs(self):
        self.assertEqual(encoder.encode_dict(OrderedDict([(b'cow', b'moo'), (b'spam', b'eggs')])), b'd3:cow3:moo4:spam4:eggse')
    
    def test_encode_dict_empty(self):
        self.assertEqual(encoder.encode_dict(OrderedDict()), b'de')
    
    def test_encode_dict_nestedlist(self):
        self.assertEqual(encoder.encode_dict(OrderedDict([(b'cow', [123])])), b'd3:cowli123eee')
    
    def test_encode_dict_nesteddict(self):
        self.assertEqual(encoder.encode_dict(OrderedDict([(b'cow', OrderedDict([(b'cow', [123])]))])),
                                             b'd3:cowd3:cowli123eeee')
    
    def test_encode_dict_pydict(self):
        self.assertEqual(encoder.encode_dict({b'cow': b'moo', b'spam': b'eggs'}), b'd3:cow3:moo4:spam4:eggse')
    
    def test_encode_dict_asciistrkeys(self):
        self.assertEqual(encoder.encode_dict({'cow': b'moo', 'spam': b'eggs'}, 'ascii'), b'd3:cow3:moo4:spam4:eggse')
    
    def test_encode_dict_mixedkeys(self):
        self.assertEqual(encoder.encode_dict({'cow': b'moo', b'spam': b'eggs'}, 'ascii'), b'd3:cow3:moo4:spam4:eggse')
    
    def test_encode_dict_noencstrkeys(self):
        with self.assertRaises(encoder.EncodeError):
            encoder.encode_dict({'cow': b'moo', 'spam': b'eggs'})

class TestEncode(TestCase):
    def test_encode_123(self):
        self.assertEqual(encoder.encode(123), b'i123e')
    
    def test_encode_helloworld(self):
        self.assertEqual(encoder.encode(b'hello world'), b'11:hello world')
    
    def test_encode_spameggs123(self):
        self.assertEqual(encoder.encode([b'spam', b'eggs', 123]), b'l4:spam4:eggsi123ee')
    
    def test_encode_cowmoospameggs(self):
        self.assertEqual(encoder.encode(OrderedDict([(b'cow', b'moo'), (b'spam', b'eggs')])), b'd3:cow3:moo4:spam4:eggse')
    
    def test_encode_badtype_err(self):
        with self.assertRaises(encoder.EncodeError):
            encoder.encode(12.0)

if __name__ == '__main__':
    unittest.main()