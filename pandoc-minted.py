#!/usr/bin/env python
''' A pandoc filter that has the LaTeX writer use minted for typesetting code.

Usage:
    pandoc --filter ./minted.py -o myfile.tex myfile.md
'''

from string import Template
from pandocfilters import toJSONFilter, RawBlock, RawInline
import warnings

special_attributes = ["caption", "label"]

def unpack_code(value, language):
    ''' Unpack the body and language of a pandoc code element.

    Args:
        value       contents of pandoc object
        language    default language
    '''
    [[_, classes, attributes], contents] = value

    if len(classes) > 0:
        language = classes[0]

    extras = {}
    for key in special_attributes:
        if attributes:
            if dict(attributes).get(key):
                d = dict(attributes)
                extras[key] = d[key]
                d.pop(key)
                attributes = list(map(list, d.items()))
    attributes = ', '.join('='.join(x) for x in attributes)

    return dict(list({'contents': contents, 'language': language,
            'attributes': attributes}.items()) + list(extras.items()))


def unpack_metadata(meta):
    ''' Unpack the metadata to get pandoc-minted settings.

    Args:
        meta    document metadata
    '''
    settings = meta.get('pandoc-minted', {})
    if settings.get('t', '') == 'MetaMap':
        settings = settings['c']

        # Get language.
        language = settings.get('language', {})
        if language.get('t', '') == 'MetaInlines':
            language = language['c'][0]['c']
        else:
            language = None

        return {'language': language}

    else:
        # Return default settings.
        return {'language': 'text'}


def minted(key, value, format, meta):
    ''' Use minted for code in LaTeX.

    Args:
        key     type of pandoc object
        value   contents of pandoc object
        format  target output format
        meta    document metadata
    '''
    if format != 'latex':
        return

    # Determine what kind of code object this is.
    if key == 'CodeBlock':
        template = Template(
            '\\begin{listing}[!ht]\n\\begin{minted}[$attributes]{$language}\n$contents\n\end{minted}\n$extra\\end{listing}'
        )
        Element = RawBlock
    elif key == 'Code':
        template = Template('\\mintinline[$attributes]{$language}{$contents}')
        Element = RawInline
    else:
        return

    settings = unpack_metadata(meta)

    code = unpack_code(value, settings['language'])
    extras = []
    for a_key in special_attributes:
        if code.get(a_key):
            extras += f"\\{a_key}{{{code.pop(a_key)}}}\n"
    return [Element(format, template.substitute(code | {"extra": ''.join(extras)}))]


if __name__ == '__main__':
    toJSONFilter(minted)

