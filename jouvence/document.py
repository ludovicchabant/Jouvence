import sys


class JouvenceDocument:
    """Represents a Fountain screenplay in a structured way.

    A screenplay contains:

    * A title page (optional) with a key/value dictionary of settings.
    * A list of scenes.
    * Each scene contains a list of paragraphs of various types.
    """
    def __init__(self):
        self.title_values = {}
        self.scenes = []

    def addScene(self, header=None):
        """Adds a scene with the specified header."""
        s = JouvenceScene()
        if header:
            s.header = header
        self.scenes.append(s)
        return s

    def lastScene(self, auto_create=True):
        """Gets the last scene in the screenplay.

            `auto_create`
                If ``True``, and the screenplay has no scenes, create
                a scene with an empty header text. Otherwise, return
                ``None``.
        """
        try:
            return self.scenes[-1]
        except IndexError:
            if auto_create:
                s = self.addScene()
                return s
            return None

    def lastParagraph(self):
        """Gets the last paragraph of the last scene in the screenplay.

        If there's no scene in the screenplay, return ``None``.
        """
        s = self.lastScene(False)
        if s:
            return s.lastParagraph()
        return None


class JouvenceScene:
    """A scene in a screenplay."""
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
        """Adds a page break (paragraph with ``TYPE_PAGEBREAK`` type)."""
        self.paragraphs.append(JouvenceSceneElement(TYPE_PAGEBREAK, None))

    def addSection(self, depth, text):
        """Adds a section (a :class:`~JouvenceSceneSection` instance)."""
        self.paragraphs.append(JouvenceSceneSection(depth, text))

    def lastParagraph(self):
        try:
            return self.paragraphs[-1]
        except IndexError:
            return None


class JouvenceSceneElement:
    """An element of a screenplay scene, _e.g._ an action, a dialogue
    line, a parenthetical, etc.
    """
    def __init__(self, el_type, text):
        self.type = el_type
        self.text = text

    def __str__(self):
        return '%s: %s' % (
            _scene_element_type_str(self.type),
            _ellipsis(self.text, 15))


class JouvenceSceneSection(JouvenceSceneElement):
    def __init__(self, depth, text):
        super().__init__(TYPE_SECTION, text)
        self.depth = depth


TYPE_ACTION = 0
TYPE_CENTEREDACTION = 1
TYPE_CHARACTER = 2
TYPE_DIALOG = 3
TYPE_PARENTHETICAL = 4
TYPE_TRANSITION = 5
TYPE_LYRICS = 6
TYPE_PAGEBREAK = 7
TYPE_SECTION = 8
TYPE_SYNOPSIS = 9


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
    if t == TYPE_SECTION:
        return 'SECTION'
    if t == TYPE_SYNOPSIS:
        return 'SYNOPSIS'
    raise NotImplementedError()


def _ellipsis(text, length):
    if len(text) > length:
        return text[:length - 3] + '...'
    return text
