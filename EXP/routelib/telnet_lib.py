import telnetlib
import socket

class TelnetSession:
    def __init__(self,prompt='# ', timeout=5):
        self.tn = None
        self.prompt = prompt
        self.timeout = timeout
    def connect(self,host, port ):
        try:
            self.tn = telnetlib.Telnet(host,port,timeout=self.timeout)
            return True
        except:
            return False

    def sendone(self,cmd):
        if self.tn is None:
            return None
        new_cmd = cmd + '\n'
        try:
            self.tn.write(new_cmd)
            return self.tn.read_until(self.prompt)
        except:
            return None

    def raw_sendone(self,cmd):
        if self.tn is None:
            return None
        new_cmd = cmd + '\n'
        try:
            self.tn.write(new_cmd)
            return True
        except:
            return None

    def read_until(self):
        if self.tn is None:
            return None

    def raw_read_until(self,until_str='# '):
        if self.tn is None:
            return None
        readed = ''
        try:
            s = self.tn.get_socket()
        except:
            return None
        for i in range(0,1024):
            try:
                readed += s.recv(1)
            except socket.timeout,e:
                break
            if readed.endswith('# '):
                break
        return readed

    def close(self):
        if self.tn is None:
            return None
        self.tn.close()