from __future__ import unicode_literals

from unittest import TestCase

from feincms_cleanse import Cleanse


class CleanseTestCase(TestCase):
    def run_tests(self, entries, klass=Cleanse, strip_whitespace_tags=True):
        for before, after in entries:
            after = before if after is None else after
            result = klass(strip_whitespace_tags).cleanse(before)
            self.assertEqual(
                result,
                after,
                "Cleaning '%s', expected '%s' but got '%s'" % (
                    before, after, result))

    def test_01_cleanse(self):
        entries = [
            ('<p>&nbsp;</p>', ''),
            ('<p>           </p>', ''),
            ('<span style="font-weight: bold;">Something</span><p></p>',
                '<strong>Something</strong>'),
            ('<p>abc <span>def <em>ghi</em> jkl</span> mno</p>', None),
            ('<span style="font-style: italic;">Something</span><p></p>',
                '<em>Something</em>'),
            ('<p>abc<br />def</p>', '<p>abc<br />def</p>'),
            ]

        self.run_tests(entries)

    def test_02_a_tag(self):
        entries = (
            ('<a href="/foo">foo</a>', None),
            (
                '<a href="/foo" name="bar" target="some" title="baz"'
                ' cookies="yesplease">foo</a>',
                '<a href="/foo" name="bar" target="some" title="baz">foo</a>'
            ),
            ('<a href="http://somewhere.else">foo</a>', None),
            ('<a href="https://somewhere.else">foo</a>', None),
            ('<a href="javascript:alert()">foo</a>', '<a href="">foo</a>'),
            ('<a href="javascript%3Aalert()">foo</a>', '<a href="">foo</a>'),
            ('<a href="mailto:foo@bar.com">foo</a>', None),
            ('<a href="tel:1-234-567-890">foo</a>', None),
        )

        self.run_tests(entries)

    def test_03_merge(self):
        entries = (
            ('<h2>foo</h2><h2>bar</h2>', '<h2>foo bar</h2>'),
            ('<h2>foo  </h2>   <h2>   bar</h2>', '<h2>foo bar</h2>'),
        )

        self.run_tests(entries)

    def test_04_p_in_li(self):
        entries = (
            ('<li><p>foo</p></li>', '<li>foo</li>'),
            ('<li>&nbsp;<p>foo</p> &#160; </li>', '<li>foo</li>'),
            # ('<li>foo<p>bar</p>baz</li>', '<li>foo bar baz</li>'),
        )

        self.run_tests(entries)

    def test_05_p_in_p(self):
        entries = (
            ('<p><p>foo</p></p>', '<p>foo</p>'),
            ('<p><p><p>&nbsp;</p> </p><p><br /></p></p>', ' '),
            # This is actually correct as the second <p> implicitely
            # closes the first paragraph, and the trailing </p> is
            # deleted because it has no matching opening <p>
            ('<p>foo<p>bar</p>baz</p>', '<p>foo</p><p>bar</p>baz'),
        )
        self.run_tests(entries)

    def test_06_whitelist(self):
        entries = (
            ('<script src="http://abc">foo</script>', ''),
            ('<script type="text/javascript">foo</script>', ''),
        )

        self.run_tests(entries)

    def test_07_configuration(self):
        class MyCleanse(Cleanse):
            allowed_tags = {'h1': (), 'h2': ()}

        entries = (
            ('<h1>foo</h1>', None),
            (
                '<h1>foo</h1><h2>bar</h2><h3>baz</h3>',
                '<h1>foo</h1><h2>bar</h2>baz'
            ),
        )

        self.run_tests(entries, klass=MyCleanse)

    def test_08_li_with_marker(self):
        entries = (
            ('<li> - foo</li>', '<li>foo</li>'),
            ('<li>* foo</li>', '<li>foo</li>'),
        )

        self.run_tests(entries)

    def test_09_empty_p_text_in_li(self):
        # this results in an empty p.text
        entries = (
            (
                '<li><p><strong>foo</strong></p></li>',
                '<li><strong>foo</strong></li>',
            ),
            (
                '<li><p><em>foo</em></p></li>',
                '<li><em>foo</em></li>',
            ),
        )

        self.run_tests(entries)

    def test_span_allowed(self):
        entries = (
            ('<p><span>foo</span></p>', None),
        )

        self.run_tests(entries)

    def test_span_style_allowed(self):
        entries = (
            ('<span style="color: #00ffff;">est</span>', None),
        )

        _allowed_tags = { 'html': (), 'body': (), 'p': (), 'span': ('style',) }

        class NewCleanse(Cleanse):
            allowed_tags = _allowed_tags

        self.run_tests(entries, NewCleanse)

    def test_only_whitespace_elements(self):
        entries_no_strip = (
            ('<table><tbody><tr><td>One</td><td> </td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>', None),
            ('<table><tbody><tr><td>One</td><td>&#160;</td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>', None),
        )
        entries_strip = (
            ('<table><tbody><tr><td>One</td><td> </td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>',
             '<table><tbody><tr><td>One</td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>'),
            ('<table><tbody><tr><td>One</td><td>&#160;</td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>',
             '<table><tbody><tr><td>One</td></tr><tr><td>Two</td><td>Three</td></tr></tbody></table>'),
        )

        _allowed_tags = { 'table': (), 'tbody': (), 'tr': (), 'td': (), }

        class NewCleanse(Cleanse):
            allowed_tags = _allowed_tags

        self.run_tests(entries_no_strip, NewCleanse, strip_whitespace_tags=False)
        self.run_tests(entries_strip, NewCleanse)
