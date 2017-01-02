import re
import logging


logger = logging.getLogger(__name__)


class FontaineState:
    can_merge = False

    def match(self, fp, ctx):
        return False

    def consume(self, fp, ctx):
        raise NotImplementedError()

    def exit(self, ctx):
        pass


class FontaineParserError(Exception):
    def __init__(self, line_no, message):
        super().__init__("Error line %d: %s" % (line_no, message))


ANY_STATE = object()
EOF_STATE = object()


RE_EMPTY_LINE = re.compile(r"^$", re.M)
RE_BLANK_LINE = re.compile(r"^\s*$", re.M)

RE_TITLE_KEY_VALUE = re.compile(r"^(?P<key>[\w\s\-]+)\s*:")


class _TitlePageState(FontaineState):
    def __init__(self):
        super().__init__()
        self._cur_key = None
        self._cur_val = None

    def consume(self, fp, ctx):
        line = fp.readline()
        if not line:
            return EOF_STATE

        if RE_EMPTY_LINE.match(line):
            self._commit(ctx)
            # Finished with the page title, now move on to the first scene.
            # However, if we never had any page title, go back to the beginning
            # so we don't consume anybody else's empty lines.
            if len(ctx.document.title_values) == 0:
                fp.seek0()
            return ANY_STATE

        m = RE_TITLE_KEY_VALUE.match(line)
        if m:
            # Commit current value, start new one.
            self._commit(ctx)
            self._cur_key = m.group('key')
            self._cur_val = line[m.end():].strip()
        else:
            if self._cur_val is None:
                if len(ctx.document.title_values) == 0:
                    # Early exit because there's no title page.
                    # Go back to the beginning so we don't consume somebody's
                    # first line of text.
                    fp.seek0()
                    return ANY_STATE

                raise FontaineParserError(
                    fp.line_no,
                    "Page title needs to be followed by 2 empty lines.")

            # Keep accumulating the value of one of the title page's values.
            self._cur_val += line.strip()
        return True

    def exit(self, ctx):
        self._commit(ctx)

    def _commit(self, ctx):
        if self._cur_key is not None:
            ctx.document.title_values[self._cur_key] = self._cur_val
            self._cur_key = None
            self._cur_val = None


RE_SCENE_HEADER_PATTERN = re.compile(
    r"^(int|ext|est|int/ext|int./ext|i/e)[\s\.]", re.I)


class _SceneHeaderState(FontaineState):
    def match(self, fp, ctx):
        lines = fp.peeklines(2)
        return (
            RE_EMPTY_LINE.match(lines[0]) and
            RE_SCENE_HEADER_PATTERN.match(lines[1]))

    def consume(self, fp, ctx):
        fp.readline()  # Get past the blank line.
        line = fp.readline().rstrip('\r\n')
        line = line.lstrip('.')  # In case it was forced.
        ctx.document.addScene(line)
        return ANY_STATE


class _ActionState(FontaineState):
    can_merge = True

    def __init__(self):
        super().__init__()
        self.text = ''

    def match(self, fp, ctx):
        return True

    def consume(self, fp, ctx):
        is_first_line = True
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            if is_first_line:
                line = line.lstrip('!')
                is_first_line = False

            self.text += line

            if RE_EMPTY_LINE.match(fp.peekline()):
                break

        return ANY_STATE

    def exit(self, ctx):
        ctx.document.lastScene().addAction(self.text)


RE_CHARACTER_LINE = re.compile(r"^[A-Z\-]+\s*(\(.*\))?$", re.M)


class _CharacterState(FontaineState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (RE_EMPTY_LINE.match(lines[0]) and
                RE_CHARACTER_LINE.match(lines[1]) and
                not RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()  # Get past the empty line.
        line = fp.readline().rstrip('\r\n')
        line = line.lstrip('@')  # In case it was forced.
        ctx.document.lastScene().addCharacter(line)
        return [_ParentheticalState, _DialogState]


RE_PARENTHETICAL_LINE = re.compile(r"^\s*\(.*\)\s*$", re.M)


class _ParentheticalState(FontaineState):
    def match(self, fp, ctx):
        # We only get here from a `_CharacterState` so we know the previous
        # one is already that.
        line = fp.peekline()
        return RE_PARENTHETICAL_LINE.match(line)

    def consume(self, fp, ctx):
        line = fp.readline().rstrip('\r\n')
        ctx.document.lastScene().addParenthetical(line)
        return [_DialogState, _CharacterState, _ActionState]


class _DialogState(FontaineState):
    def __init__(self):
        super().__init__()
        self.text = ''

    def match(self, fp, ctx):
        line = fp.peekline()
        return not RE_EMPTY_LINE.match(line)

    def consume(self, fp, ctx):
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE
            self.text += line
            if RE_EMPTY_LINE.match(fp.peekline()):
                break
        return ANY_STATE

    def exit(self, ctx):
        ctx.document.lastScene().addDialog(self.text.rstrip('\r\n'))


class _LyricsState(FontaineState):
    pass


class _TransitionState(FontaineState):
    pass


class _ForcedParagraphStates(FontaineState):
    STATE_SYMBOLS = {
        '.': _SceneHeaderState,
        '!': _ActionState,
        '@': _CharacterState,
        '~': _LyricsState,
        '>': _TransitionState
    }

    def __init__(self):
        super().__init__()
        self._state_cls = None

    def match(self, fp, ctx):
        lines = fp.peeklines(2)
        if (RE_EMPTY_LINE.match(lines[0]) and
                lines[1][:1] in self.STATE_SYMBOLS):
            self._state_cls = self.STATE_SYMBOLS[lines[1][:1]]
            return True
        return False

    def consume(self, fp, ctx):
        return self._state_cls()


STATES = [
    _ForcedParagraphStates,  # Must be first.
    _SceneHeaderState,
    _CharacterState,
    _TransitionState,
    _ActionState,  # Must be last.
]


class _PeekableFile:
    def __init__(self, fp):
        self.line_no = 1
        self._fp = fp

    def read(self, size=-1):
        return self._doRead(size, True)

    def read1(self):
        return self.read(1)

    def peek1(self):
        pos = self._fp.tell()
        c = self._doRead(1, False)
        self._fp.seek(pos)
        return c

    def readline(self, size=-1):
        data = self._fp.readline(size)
        self.line_no += 1
        return data

    def peekline(self):
        pos = self._fp.tell()
        line = self._fp.readline()
        self._fp.seek(pos)
        return line

    def peeklines(self, count):
        pos = self._fp.tell()
        lines = []
        for i in range(count):
            lines.append(self._fp.readline())
        self._fp.seek(pos)
        return lines

    def seek0(self):
        self._fp.seek(0)
        self.line_no = 1

    def _doRead(self, size, advance_line_no):
        data = self._fp.read(size)
        if advance_line_no:
            self.line_no += data.count('\n')
        return data


class _FontaineStateMachine:
    def __init__(self, fp, doc):
        self.fp = _PeekableFile(fp)
        self.state = None
        self.document = doc

    @property
    def line_no(self):
        return self.fp.line_no

    def run(self):
        self.state = _TitlePageState()
        while True:
            logger.debug("State '%s' consuming from '%s'..." %
                         (self.state.__class__.__name__, self.fp.peekline()))
            res = self.state.consume(self.fp, self)

            # See if we reached the end of the file.
            if not self.fp.peekline():
                logger.debug("Reached end of line... ending parsing.")
                res = EOF_STATE

            # Figure out what to do next...

            if res is None:
                raise Exception(
                    "States need to return `ANY_STATE`, one or more specific "
                    "states, or `EOF_STATE` if they reached the end of the "
                    "file.")

            if res is True:
                # State continues to consume.
                continue

            if res is ANY_STATE or isinstance(res, list):
                # State wants to exit, we need to figure out what is the
                # next state.
                pos = self.fp._fp.tell()
                next_states = res
                if next_states is ANY_STATE:
                    next_states = STATES
                logger.debug("Trying to match next state from: %s" %
                             [t.__name__ for t in next_states])
                for sc in next_states:
                    s = sc()
                    if s.match(self.fp, self):
                        logger.debug("Matched state %s" %
                                     s.__class__.__name__)
                        self.fp._fp.seek(pos)
                        res = s
                        break
                else:
                    raise Exception("Can't match following state after: %s" %
                                    self.state)
                if self.state:
                    if type(self.state) == type(res) and self.state.can_merge:
                        # Don't switch states if the next state is the same
                        # type and that type supports merging.
                        continue

                    self.state.exit(self)

                self.state = res
                continue

            if isinstance(res, FontaineState):
                # State wants to exit, wants a specific state to be next.
                if self.state:
                    self.state.exit(self)
                self.state = res
                continue

            if res is EOF_STATE:
                # Reached end of file.
                if self.state:
                    self.state.exit(self)
                break

            raise Exception("Unsupported state result: %s" % res)


class FontaineParser:
    def __init__(self):
        pass

    def parse(self, filein):
        if isinstance(filein, str):
            with open(filein, 'r') as fp:
                return self._doParse(fp)
        else:
            return self._doParse(fp)

    def parseString(self, text):
        import io
        with io.StringIO(text) as fp:
            return self._doParse(fp)

    def _doParse(self, fp):
        from .document import FontaineDocument
        doc = FontaineDocument()
        machine = _FontaineStateMachine(fp, doc)
        machine.run()
        return doc
