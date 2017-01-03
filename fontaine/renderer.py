import re


RE_ITALICS = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?\*(?P<text>.*[^\s\*])\*(?=[^a-zA-Z0-9\*]|$)")
RE_BOLD = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?\*\*(?P<text>.*[^\s])\*\*(?=[^a-zA-Z0-9]|$)")
RE_UNDERLINE = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?_(?P<text>.*[^\s])_(?=[^a-zA-Z0-9]|$)")


class BaseRenderer:
    def render_text(self, text):
        # Replace bold stuff to catch double asterisks.
        text = RE_BOLD.sub(self._do_write_bold, text)
        text = RE_ITALICS.sub(self._do_write_italics, text)
        text = RE_UNDERLINE.sub(self._do_write_underline, text)

        return text

    def _do_write_italics(self, m):
        if m.group('esc'):
            return m.group('before') + '*' + m.group('text') + '*'
        return (
            m.group('before') +
            self.write_italics(m.group('text')))

    def _do_write_bold(self, m):
        if m.group('esc'):
            return m.group('before') + '**' + m.group('text') + '**'
        return (
            m.group('before') +
            self.write_bold(m.group('text')))

    def _do_write_underline(self, m):
        if m.group('esc'):
            return m.group('before') + '_' + m.group('text') + '_'
        return (
            m.group('before') +
            self.write_underline(m.group('text')))

    def write_italics(self, text):
        raise NotImplementedError()

    def write_bold(self, text):
        raise NotImplementedError()

    def write_underline(self, text):
        raise NotImplementedError()
