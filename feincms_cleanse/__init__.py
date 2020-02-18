from __future__ import unicode_literals

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

import lxml.html
import lxml.html.clean
import lxml.html.defs
import re
import unicodedata


def _all_allowed_attrs(allowed_tags):
    all_allowed_attrs = set()
    for attr_seq in list(allowed_tags.values()):
        all_allowed_attrs.update(attr_seq)
    return all_allowed_attrs

# ------------------------------------------------------------------------

VERSION = (8,)
__version__ = '.'.join(map(str, VERSION))

__all__ = ('cleanse_html', 'Cleanse')


class Cleanse(object):
    def __init__(self, strip_whitespace_tags=True):
        self.strip_whitespace_tags = strip_whitespace_tags

    allowed_tags = {
        'a': ('href', 'name', 'target', 'title'),
        'h2': (),
        'h3': (),
        'strong': (),
        'em': (),
        'p': (),
        'ul': (),
        'ol': (),
        'li': (),
        'span': (),
        'br': (),
        'sub': (),
        'sup': (),
    }

    empty_tags = ('br',)

    merge_tags = ('h2', 'h3', 'strong', 'em', 'ul', 'ol', 'sub', 'sup')

    def validate_href(self, href):
        """
        Verify that a given href is benign and allowed.

        This is a stupid check, which probably should be much more elaborate
        to be safe.
        """
        return True

    def clean(self, element):
        """ Hook for your own clean methods. """
        return element

    def cleanse(self, html):
        """
        Clean HTML code from ugly copy-pasted CSS and empty elements
        Removes everything not explicitly allowed in ``cleanse_html_allowed``.
        Requires ``lxml`` and ``beautifulsoup``.
        """
        html = '<anything>%s</anything>' % html
        doc = lxml.html.fromstring(html)
        try:
            lxml.html.tostring(doc, encoding='utf-8')
        except UnicodeDecodeError:
            # fall back to slower BeautifulSoup if parsing failed
            from lxml.html import soupparser
            doc = soupparser.fromstring(html)

        cleaner = lxml.html.clean.Cleaner(
            allow_tags=list(self.allowed_tags.keys()) + ['style', 'anything'],
            remove_unknown_tags=False, # preserve surrounding 'anything' tag
            style=False, safe_attrs_only=False, # do not strip out style
            # attributes; we still need
            # the style information to
            # convert spans into em/strong
            # tags
        )

        cleaner(doc)

        # walk the tree recursively, because we want to be able to remove
        # previously emptied elements completely
        for element in reversed(list(doc.iterdescendants())):
            if element.tag == 'style':
                element.drop_tree()
                continue

            # convert span elements into em/strong if a matching style rule
            # has been found. strong has precedence, strong & em at the same
            # time is not supported
            elif element.tag == 'span':
                style = element.attrib.get('style')
                if style:
                    if 'bold' in style:
                        element.tag = 'strong'
                    elif 'italic' in style:
                        element.tag = 'em'

            # remove empty tags if they are not <br />
            elif (not element.text and element.tag not in self.empty_tags and not len(element)):
                element.drop_tag()
                continue

            # remove all attributes which are not explicitly allowed
            allowed = self.allowed_tags.get(element.tag, [])
            for key in list(element.attrib.keys()):
                if key not in allowed:
                    del element.attrib[key]

            # Clean hrefs so that they are benign
            href = element.attrib.get('href', None)
            if href is not None and not self.validate_href(href):
                del element.attrib['href']

        # just to be sure, run cleaner again, but this time with even more
        # strict settings
        safe_attrs = set(lxml.html.defs.safe_attrs)
        safe_attrs.update(_all_allowed_attrs(self.allowed_tags))
        cleaner = lxml.html.clean.Cleaner(
            allow_tags=list(self.allowed_tags.keys()) + ['anything'],
            remove_unknown_tags=False, # preserve surrounding 'anything' tag
            style=False, safe_attrs_only=True, safe_attrs=safe_attrs
        )

        cleaner(doc)

        html = lxml.html.tostring(doc, method='xml').decode('utf-8')

        # remove wrapping tag needed by XML parser
        html = re.sub(r'</?anything/? *>', '', html)

        # remove all sorts of newline characters
        html = html.replace('\n', ' ').replace('\r', ' ')
        html = html.replace('&#10;', ' ').replace('&#13;', ' ')
        html = html.replace('&#xa;', ' ').replace('&#xd;', ' ')

        if self.strip_whitespace_tags:
            # remove elements containing only whitespace or linebreaks
            whitespace_re = re.compile(r'<([a-z0-9]+)>(<br\s*/>|\&nbsp;|\&#160;|\s)*</\1>')
            while True:
                new = whitespace_re.sub('', html)
                if new == html:
                    break
                html = new

        # merge tags
        for tag in self.merge_tags:
            merge_str = '\s*</%s>\s*<%s>\s*' % (tag, tag)
            while True:
                new = re.sub(merge_str, ' ', html)
                if new == html:
                    break
                html = new

        # fix p-in-p tags
        p_in_p_start_re = re.compile(r'<p>(\&nbsp;|\&#160;|\s)*<p>')
        p_in_p_end_re = re.compile('</p>(\&nbsp;|\&#160;|\s)*</p>')

        for tag in self.merge_tags:
            merge_start_re = re.compile('<p>(\\&nbsp;|\\&#160;|\\s)*<%s>(\\&nbsp;|\\&#160;|\\s)*<p>' % tag)
            merge_end_re = re.compile('</p>(\\&nbsp;|\\&#160;|\\s)*</%s>(\\&nbsp;|\\&#160;|\\s)*</p>' % tag)

            while True:
                new = merge_start_re.sub('<p>', html)
                new = merge_end_re.sub('</p>', new)
                new = p_in_p_start_re.sub('<p>', new)
                new = p_in_p_end_re.sub('</p>', new)

                if new == html:
                    break
                html = new

        # remove list markers with <li> tags before them
        html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*(-|\*|&#183;)(\&nbsp;|\&#160;|\s)*', '<li>', html)

        # remove p-in-li tags
        html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*<p>', '<li>', html)
        html = re.sub(r'</p>(\&nbsp;|\&#160;|\s)*</li>', '</li>', html)

        # add a space before the closing slash in empty tags
        html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

        return html


def cleanse_html(html):
    """
    Compat shim for older cleanse API
    """
    return Cleanse().cleanse(html)

