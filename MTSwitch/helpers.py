import json


def responseToJson(r):
    r = r.replace("'", '')
    r = r.replace('{', '{"').replace('}', '"}').replace('[', '["').replace(']', '"]').replace(':', '":"').replace(',', '","')
    r = r.replace(':"[', ':[').replace('["[', '[[').replace(']"]', ']]').replace('{"{', '{{').replace('}"}', '}}')
    r = r.replace('{"[', '{[').replace(']"}', ']}').replace('["{', '[{').replace('}"]', '}]')
    r = r.replace(']",', '],').replace(',"[', ',[').replace('}",', '},').replace(',"{', ',{')
    return json.loads(r)


def jsonToRequest(j):
    r = json.dumps(j).replace('\n', '').replace(' ', '').replace('"', '')
    return r


def asciiToStr(a):
    r = ''
    for idx in range(0, len(a), 2):
        r += chr(int(a[idx:idx + 2], 16))
    return r


def strToAscii(s):
    r = ''
    for o in [ord(c) for c in s]:
        h = hex(o).replace('0x', '')
        if len(h) == 1:
            h = '0' + h
        r += h
    return r
