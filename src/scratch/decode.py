#!/usr/bin/python

import sys
import re
import codecs

# remove annoying characters
chars = {
    '\xc2\x82' : ',',        # High code comma
    '\xc2\x84' : ',,',       # High code double comma
    '\xc2\x85' : '...',      # Tripple dot
    '\xc2\x88' : '^',        # High carat
    '\xc2\x91' : '\x27',     # Forward single quote
    '\xc2\x92' : '\x27',     # Reverse single quote
    '\xc2\x93' : '\x22',     # Forward double quote
    '\xc2\x94' : '\x22',     # Reverse double quote
    '\xc2\x95' : '-',	     # What the heck is this?
    '\xc2\x96' : '-',        # High hyphen
    '\xc2\x97' : '--',       # Double hyphen
    '\xc2\x99' : '-',
    '\xc2\xa0' : ' ',
    '\xc2\xa6' : '|',        # Split vertical bar
    '\xc2\xab' : '<<',       # Double less than
    '\xc2\xbb' : '>>',       # Double greater than
    '\xc2\xbc' : '1/4',      # one quarter
    '\xc2\xbd' : '1/2',      # one half
    '\xc2\xbe' : '3/4',      # three quarters
    '\xca\xbf' : '\x27',     # c-single quote
    '\xcc\xa8' : '',         # modifier - under curve
    '\xcc\xb1' : '',         # modifier - under line
    '\xc3\x95' : '\'',	     # chaileon : tilde
    '\xc3\x92' : '`',	     # chaileon : grave
    '\xc3\x93' : '\'',       # chaileon : acute
    '\xc3\x94' : '^',        # chaileon : circumflex
    '\xc3\xbb' : '\xb0'
}


def replace_chars(match):
    char = match.group(0)
    return chars[char]


infile = open(sys.argv[1], 'r').readlines()
for line in infile:
    line = line.rstrip()
    line2 = line.decode('latin1').encode('utf8')
    print(re.sub('(' + '|'.join(chars.keys()) + ')', replace_chars, line2))
