from django.test import TestCase

from feincms_cleanse import cleanse_html


class CleanseTestCase(TestCase):
    def run_tests(self, entries, **kwargs):
        for before, after in entries:
            after = before if after is None else after
            result = cleanse_html(before, **kwargs)
            self.assertEqual(result, after, "Cleaning '%s', expected '%s' but got '%s'" % (before, after, result))

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
                    ('<a href="/foo" target="some" name="bar" title="baz" cookies="yesplease">foo</a>', '<a href="/foo" target="some" name="bar" title="baz">foo</a>'),
                    ('<a href="http://somewhere.else">foo</a>', None),
                    ('<a href="https://somewhere.else">foo</a>', None),
                    ('<a href="javascript:alert()">foo</a>', '<a href="">foo</a>'),
#                    ('<a href="javascript%2Dalert()">foo</a>', '<a href="">foo</a>'),
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
#                   ('<li>foo<p>bar</p>baz</li>', '<li>foo bar baz</li>'),
                  )

        self.run_tests(entries)

    def test_05_p_in_p(self):
        entries = (
                   ('<p><p><p>&nbsp;</p> </p><p><br /></p></p>', ' '),
#                   ('<p>foo<p>bar</p>baz</p>', '<p>foo bar baz</p>'),
                  )

        self.run_tests(entries)

    def test_06_whitelist(self):
        entries = (
                   ('<script src="http://abc">foo</script>', ''),
                   ('<script type="text/javascript">foo</script>', ''),
                  )

        self.run_tests(entries)

    def test_07_configuration(self):
        entries = (
                   ('<h1>foo</h1>', None),
                   ('<h1>foo</h1><h2>bar</h2><h3>baz</h3>', '<h1>foo</h1><h2>bar</h2>baz'),
                  )

        allowed_tags = { 'h1': (), 'h2': () }

        self.run_tests(entries, allowed_tags=allowed_tags)

    def test_span_allowed(self):
        entries = (
                   ('<p><span>foo</span></p>', None),
                  )

        self.run_tests(entries)

    def test_span_style_allowed(self):
        entries = (
                   ('<span style="color: #00ffff;">est</span>', None),
                  )

        allowed_tags = { 'html': (), 'body': (), 'p': (), 'span': ('style',) }

        self.run_tests(entries, allowed_tags=allowed_tags)

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

        allowed_tags = { 'table': (), 'tbody': (), 'tr': (), 'td': (), }

        self.run_tests(entries_no_strip, allowed_tags=allowed_tags, strip_whitespace_tags=False)
        self.run_tests(entries_strip, allowed_tags=allowed_tags)
