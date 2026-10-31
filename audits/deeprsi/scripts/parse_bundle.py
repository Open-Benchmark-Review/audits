import sys, json, re
def parse_obj(src, start):
    """Tokenize a JS object literal (backtick/quote strings, unquoted keys, !0/!1, null, numbers) into Python."""
    i = start
    def ws():
        nonlocal i
        while src[i] in ' \n\t\r': i += 1
    def val():
        nonlocal i
        ws(); c = src[i]
        if c == '{':
            i += 1; o = {}
            while True:
                ws()
                if src[i] == '}': i += 1; return o
                if src[i] in '`"\'': k = string()
                else:
                    m = re.match(r'[A-Za-z_$0-9]+', src[i:]); k = m.group(0); i += len(k)
                ws(); assert src[i] == ':', src[i-50:i+50]; i += 1
                o[k] = val(); ws()
                if src[i] == ',': i += 1
        if c == '[':
            i += 1; a = []
            while True:
                ws()
                if src[i] == ']': i += 1; return a
                a.append(val()); ws()
                if src[i] == ',': i += 1
        if c in '`"\'': return string()
        if src.startswith('JSON.parse(', i):
            i += len('JSON.parse('); ws(); sv = string(); ws(); assert src[i] == ')'; i += 1
            return json.loads(sv)
        if src.startswith('!0', i): i += 2; return True
        if src.startswith('!1', i): i += 2; return False
        for lit, v in (('null', None), ('true', True), ('false', False), ('void 0', None)):
            if src.startswith(lit, i): i += len(lit); return v
        m = re.match(r'-?[0-9.]+(e[-+]?\d+)?', src[i:])
        if m: i += len(m.group(0)); return float(m.group(0)) if any(x in m.group(0) for x in '.e') else int(m.group(0))
        raise ValueError(src[i-80:i+80])
    def string():
        nonlocal i
        q = src[i]; i += 1; out = []
        while src[i] != q:
            if src[i] == '\\':
                n = src[i+1]
                out.append({'n':'\n','t':'\t','`':'`','"':'"',"'":"'",'\\':'\\'}.get(n, '\\'+n)); i += 2
            else:
                if q == '`' and src.startswith('${', i): raise ValueError('template interp')
                out.append(src[i]); i += 1
        i += 1; return ''.join(out)
    return val(), i
if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    start = src.index(sys.argv[2]) + len(sys.argv[2]) - 1
    obj, _ = parse_obj(src, start)
    json.dump(obj, open(sys.argv[3], 'w'), indent=1)
