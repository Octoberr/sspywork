from pathlib import Path
import time

dirpath = Path(r'D:\swmdata\traindata\onlycode\train_')

okimg = Path(r'D:\gitcode\cnn_captcha\sample\origin')

for child in dirpath.iterdir():
    getname = child.name.split('.')[0]
    target = okimg / (getname.upper() + '_' + str(time.time()).replace('.', '') + '.png')

    child.rename(target)
    print(target)
