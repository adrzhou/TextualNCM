import sys
from cx_Freeze import setup, Executable


sys.path.append('/home/adrzhou/Documents/TextualNCM/textualncm')
# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': [], 
                 'include_files': ['textualncm/downloads', 'textualncm/save', 'textualncm/app.css']}

base = 'console'

executables = [
    Executable('textualncm/app.py', base=base, target_name = 'TextualNCM')
]

setup(name='TextualNCM',
      version = '0.1',
      description = 'A Text User Interface for Netease Cloud Music',
      options = {'build_exe': build_options},
      executables = executables)
