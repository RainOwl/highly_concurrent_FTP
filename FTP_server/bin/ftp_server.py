#_author_ : duany_000
#_date_ : 2018/3/5
import os, sys
BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core import main

if __name__ == '__main__':
    main.ArgvHandler()
