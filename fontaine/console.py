import os
import colorama
from .renderer import BaseDocumentRenderer, BaseTextRenderer


def _w(out, style, text, reset_all=False):
    f = out.write
    f(style)
    f(text)
    if not reset_all:
        f(colorama.Style.NORMAL)
    else:
        f(colorama.Style.RESET_ALL)
    f(os.linesep)


class ConsoleDocumentRenderer(BaseDocumentRenderer):
    def __init__(self, width=80):
        super().__init__(ConsoleTextRenderer())
        self.width = width
        colorama.init()

    def write_title_heading(self, text, out):
        print("", file=out)
        for line in text.split('\n'):
            print(line.center(self.width), file=out)
        print("", file=out)
        print("", file=out)

    def write_title_footer(self, text, out):
        _w(out, colorama.Style.DIM, text)
        print("", file=out)
        _w(out, colorama.Style.DIM, 80 * '=')

    def write_scene_heading(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.WHITE + colorama.Style.BRIGHT, text, True)

    def write_action(self, text, out):
        print(text, file=out)

    def write_centeredaction(self, text, out):
        print("", file=out)
        for line in text.split('\n'):
            print(line.center(self.width), file=out)

    def write_character(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.WHITE, "\t\t\t" + text, True)

    def write_dialog(self, text, out):
        for line in text.split('\n'):
            print("\t" + line, file=out)

    def write_parenthetical(self, text, out):
        for line in text.split('\n'):
            print("\t\t" + line, file=out)

    def write_transition(self, text, out):
        print("", file=out)
        print("\t\t\t\t" + text, file=out)

    def write_lyrics(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.MAGENTA, text, True)

    def write_pagebreak(self, out):
        print("", file=out)
        _w(out, colorama.Style.DIM, 80 * '=')


class ConsoleTextRenderer(BaseTextRenderer):
    def _writeStyled(self, style, text):
        return style + text + colorama.Style.NORMAL

    def make_italics(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_bold(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_underline(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)
