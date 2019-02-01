import subprocess
import re

class proc():
    def __init__(self, cmd):
        self.cmd = cmd
        self.handle = None
        
    def run(self):
        self.handle = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    def wait(self):
        self.handle.wait()
        
    def getoutput(self):
        tmpout = self.handle.stdout.read()
        tmpout = re.sub(r'\x1b\[.*?\d+m', '', tmpout)
        arrout = []
        for line in tmpout.strip('\r\n').split('\n'):
            if len(line) <= 5:
                continue
            if line[0] != '[':
                continue
            elif line[0:3] not in['[-]', '[+]', '[*]', '[!]']:
                continue
            arrout.append(line)
        return arrout
        
    def isend(self):
        return self.handle.poll() != None
        
        
