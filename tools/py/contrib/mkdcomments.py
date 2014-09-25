"""
A Python-Markdown preprocessor extension to ignore html comments opened by
three dashes (<!---comment-->) and any whitespace prior to them. I believe
pandoc has similar functionality.

Note: This extension does not work with the markdownfromFile function or
the convertFile method. They raise a UnicodeDecodeError.

Note: If using multiple extensions, mkdcomments probably should be last in
the list. Markdown extensions are loaded into the OrderedDict from which they
are executed in the order of the extension list. If a different extension is
loaded after mkdcomments, it may insert itself before mkdcomments in the
OrderedDict. Undesirable results may ensue. If, for instance, the 'meta'
extension is executed before mkdcomments, any comments in the meta-data will be
included in meta's dictionary.
"""

import re
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class CommentsExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add("comments", CommentsProcessor(md), "_begin")


class CommentsProcessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        multi = False
        for line in lines:
            if not multi:
                multi = self._uncommenter(line)[1]
                new_lines.append(self._uncommenter(line)[0])
            else:
                multi = self._unmultiliner(line)[1]
                new_lines.append(self._unmultiliner(line)[0])
        return new_lines

    def _uncommenter(self, line):
        if re.match(r'.*<!---.*-->', line):     # inline(could start multiline)
            return self._uncommenter(re.sub(r'\s*<!---.*?-->', '', line))
        elif re.match(r'.*<!---', line):        # start multiline
            return [re.sub(r'\s*<!---.*', '', line), True]
        else:                                   # no comment
            return [line, False]

    def _unmultiliner(self, line):
        if re.match(r'.*-->', line):    # end multiline (could start comment)
            return self._uncommenter(re.sub(r'.*?-->', '', line, count=1))
        else:
            return ['', True]                   # continue multiline
