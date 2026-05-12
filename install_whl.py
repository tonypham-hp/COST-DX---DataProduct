import os
import glob
import subprocess

whl_folder = '.\wheels'

whl_files = glob.glob(os.path.join(whl_folder, '*.whl'))

for whl_file in whl_files:
    subprocess.check_call(['pip', 'install', '--no-index', '--find-links',whl_folder, whl_file])