# -*- coding: utf-8 -*-
import os
import sys

def join(a, *p):
    """Join two or more pathname components, inserting "\\" as needed.
    If any component is an absolute path, all previous path components
    will be discarded."""
    path = a
    for b in p:
        b_wins = 0  # set to 1 iff b makes path irrelevant
        if path == "":
            b_wins = 1

        elif os.path.isabs(b):
            # This probably wipes out path so far.  However, it's more
            # complicated if path begins with a drive letter:
            #     1. join('c:', '/a') == 'c:/a'
            #     2. join('c:/', '/a') == 'c:/a'
            # But
            #     3. join('c:/a', '/b') == '/b'
            #     4. join('c:', 'd:/') = 'd:/'
            #     5. join('c:/', 'd:/') = 'd:/'
            if path[1:2] != ":" or b[1:2] == ":":
                # Path doesn't start with a drive letter, or cases 4 and 5.
                b_wins = 1

            # Else path has a drive letter, and b doesn't but is absolute.
            elif len(path) > 3 or (len(path) == 3 and
                                   path[-1] not in "/\\"):
                # case 3
                b_wins = 1

        if b_wins:
            path = b
        else:
            # Join, and ensure there's a separator.
            assert len(path) > 0
            if path[-1] in "/\\":
                if b and b[0] in "/\\":
                    path += b[1:]
                else:
                    path += b
            elif path[-1] == ":":
                path += b
            elif b:
                if b[0] in "/\\":
                    path += b
                else:
                    path += "\\" + b
            else:
                # path is not empty and does not end with a backslash,
                # but b is empty; since, e.g., split('a/') produces
                # ('a', ''), it's best if join() adds a backslash in
                # this case.
                path += '\\'

    return os.path.normpath(path)
#支持windows和linux各系统文件路径分隔符
_names = sys.builtin_module_names
if 'nt' in _names:
    os.path.join = join