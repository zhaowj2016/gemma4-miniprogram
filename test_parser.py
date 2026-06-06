import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import parser
from parser import parse_triple

raw = open('raw.txt', 'r', encoding='utf-8').read()
page_files = parse_triple(raw)
print(page_files.keys())
