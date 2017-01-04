import sys


class JouvenceDocument:
    def __init__(self):
        self.title_values = {}
        self.scenes = []

    def addScene(self, header=None):
        s = JouvenceScene()
        if header:
            s.header = header
        self.scenes.append(s)
        return s

    def lastScene(self, auto_create=True):
        try:
            return self.scenes[-1]
        except IndexError:
            if auto_create:
                s = self.addScene()
                return s
            return None

    def lastParagraph(self):
        s = self.lastScene(False)
        if s:
            return s.lastParagraph()
        return None


class JouvenceScene:
    def __init__(self):
        self.header = None
        self.paragraphs = []
        self._adders = {}

    def __getattr__(self, name):
        if name.startswith('add'):
            add_type_name = name[3:]
            try:
                adder = self._adders[add_type_name]
            except KeyError:
                module = sys.modules[__name__]
                add_type = getattr(module,
                                   'TYPE_%s' % add_type_name.upper())

                def _type_adder(_text):
                    new_p = JouvenceSceneElement(add_type, _text)
                    self.paragraphs.append(new_p)
                    return new_p

                adder = _type_adder
                self._adders[add_type_name] = adder
            return adder
        else:
            raise AttributeError

    def addPageBreak(self):
        self.paragraphs.append(JouvenceSceneElement(TYPE_PAGEBREAK, None))

    def lastParagraph(self):
        try:
            return self.paragraphs[-1]
        except IndexError:
            return None


class JouvenceSceneElement:
    def __init__(self, el_type, text):
        self.type = el_type
        self.text = text

    def __str__(self):
        return '%s: %s' % (
            _scene_element_type_str(self.type),
            _ellipsis(self.text, 15))


TYPE_ACTION = 0
TYPE_CENTEREDACTION = 1
TYPE_CHARACTER = 2
TYPE_DIALOG = 3
TYPE_PARENTHETICAL = 4
TYPE_TRANSITION = 5
TYPE_LYRICS = 6
TYPE_PAGEBREAK = 7
TYPE_EMPTYLINES = 8


def _scene_element_type_str(t):
    if t == TYPE_ACTION:
        return 'ACTION'
    if t == TYPE_CENTEREDACTION:
        return 'CENTEREDACTION'
    if t == TYPE_CHARACTER:
        return 'CHARACTER'
    if t == TYPE_DIALOG:
        return 'DIALOG'
    if t == TYPE_PARENTHETICAL:
        return 'PARENTHETICAL'
    if t == TYPE_TRANSITION:
        return 'TRANSITION'
    if t == TYPE_LYRICS:
        return 'LYRICS'
    if t == TYPE_PAGEBREAK:
        return 'PAGEBREAK'
    if t == TYPE_EMPTYLINES:
        return 'EMPTYLINES'
    raise NotImplementedError()


def _ellipsis(text, length):
    if len(text) > length:
        return text[:length - 3] + '...'
    return text
