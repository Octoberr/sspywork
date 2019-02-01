import string
import random
import re

def get_iport_from_url(url):
    #m = re.match('http[s]*://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[^:]*?.*',url)
    m = re.match('http[s]*://([^/:]+)(:\d*)?',url)
    if m:
        target = m.groups()[0]
        port = m.groups()[1]
        if port is None:
            return (target,80)
        return (target,port)

    return None

def random_text(length, alph=string.ascii_letters + string.digits):
    """ Random text generator. NOT crypto safe.

    Generates random text with specified length and alphabet.
    """
    return ''.join(random.choice(alph) for _ in range(length))

def random_port(length, alph=string.digits):
    """ Random text generator. NOT crypto safe.

    Generates random text with specified length and alphabet.
    """
    port = ''.join(random.choice(alph) for _ in range(length))
    if port.startswith('0'):
        port = '1'+port[1:]
    return port

def ascii_to_hex(ascii_data, max_print=100):
    hex_result = []
    count = 1
    hex_ring = ''
    for ch in iter(ascii_data):
        if count % (max_print+1) == 0:
            hex_result.append(hex_ring)
            count = 1
            hex_ring = ''
        count += 1
        hex_ring += '\\\\x%x' % ord(ch)
    if len(hex_ring) > 0:
        hex_result.append(hex_ring)
    return hex_result