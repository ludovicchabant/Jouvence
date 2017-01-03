import os
import sys
import colorama
from .renderer import BaseDocumentRenderer, BaseTextRenderer


def _w(style, text, reset_all=False):
    f = sys.stdout.write
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

    def write_title_heading(self, text):
        print("")
        for line in text.split('\n'):
            print(line.center(self.width))
        print("")
        print("")

    def write_title_footer(self, text):
        _w(colorama.Style.DIM, text)
        print("")
        _w(colorama.Style.DIM, 80 * '=')

    def write_scene_heading(self, text):
        print("")
        _w(colorama.Fore.WHITE + colorama.Style.BRIGHT, text, True)

    def write_action(self, text):
        print(text)

    def write_centeredaction(self, text):
        print("")
        for line in text.split('\n'):
            print(line.center(self.width))

    def write_character(self, text):
        print("")
        _w(colorama.Fore.WHITE, "\t\t\t" + text, True)

    def write_dialog(self, text):
        for line in text.split('\n'):
            print("\t" + line)

    def write_parenthetical(self, text):
        for line in text.split('\n'):
            print("\t\t" + line)

    def write_transition(self, text):
        print("")
        print("\t\t\t\t" + text)

    def write_lyrics(self, text):
        print("")
        _w(colorama.Fore.MAGENTA, text, True)

    def write_pagebreak(self):
        print("")
        _w(colorama.Style.DIM, 80 * '=')


class ConsoleTextRenderer(BaseTextRenderer):
    def _writeStyled(self, style, text):
        return style + text + colorama.Style.NORMAL

    def make_italics(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_bold(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_underline(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)
