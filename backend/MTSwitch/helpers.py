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
    if a is None:
        return ''
    r = ''
    for idx in range(0, len(a), 2):
        r += chr(int(a[idx:idx + 2], 16))
    return r


def strToAscii(s):
    if s is None:
        return ''
    r = ''
    for o in [ord(c) for c in s]:
        h = hex(o).replace('0x', '')
        if len(h) == 1:
            h = '0' + h
        r += h
    return r


def translateKeys(j, tmap, ommit_surplus=False):
    """
    takes a json and translates all keys found in tmap-keys to tmap-value (replaces key names)
    if ommit_surplus is set, only translated keys find their way into the resulting dict
    """
    if isinstance(j, list):
        r = list()
        for e in j:
            r.append(translateKeys(e, tmap, ommit_surplus))
        return r
    elif isinstance(j, dict):
        r = dict()
        for k, v in j.items():
            translated = False
            if k in tmap:
                k = tmap[k]
                translated = True
            if not ommit_surplus or translated:
                r[k] = translateKeys(v, tmap, ommit_surplus)
        return r
    else:
        return j


def jsonAllAsciiToStr(j):
    """
    Helper for development to just try to convert everything in a json from ascii to str
    (to find interesting ascii coded variables)
    """
    r = dict()
    for k, v in j.items():
        if isinstance(v, str):
            try:
                r[k] = asciiToStr(v)
            except Exception:
                r[k] = v
        else:
            r[k] = v
    return r
