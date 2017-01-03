import re
import logging


logger = logging.getLogger(__name__)


class FontaineState:
    can_merge = False
    needs_pending_empty_lines = True

    def __init__(self):
        self.has_pending_empty_line = False

    def match(self, fp, ctx):
        return False

    def consume(self, fp, ctx):
        raise NotImplementedError()

    def merge(self):
        pass

    def exit(self, ctx):
        pass


class _PassThroughState(FontaineState):
    def consume(self, fp, ctx):
        return ANY_STATE


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

    def match(self, fp, ctx):
        line = fp.peekline()
        return RE_TITLE_KEY_VALUE.match(line)

    def consume(self, fp, ctx):
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            m = RE_TITLE_KEY_VALUE.match(line)
            if m:
                # Commit current value, start new one.
                self._commit(ctx)
                self._cur_key = m.group('key')
                self._cur_val = line[m.end():].strip()
            else:
                # Keep accumulating the value of one of the title page's
                # values.
                self._cur_val += line.strip()

            if RE_EMPTY_LINE.match(fp.peekline()):
                self._commit(ctx)
                # Finished with the page title, now move on to the first scene.
                self.has_pending_empty_line = True
                break

        return ANY_STATE

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
        lines = fp.peeklines(3)
        return (
            RE_EMPTY_LINE.match(lines[0]) and
            RE_SCENE_HEADER_PATTERN.match(lines[1]) and
            RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()  # Get past the blank line.
        line = fp.readline().rstrip('\r\n')
        line = line.lstrip('.')  # In case it was forced.
        ctx.document.addScene(line)
        self.has_pending_empty_line = True
        return ANY_STATE


class _ActionState(FontaineState):
    can_merge = True
    needs_pending_empty_lines = False

    def __init__(self):
        super().__init__()
        self.text = ''
        self._to_merge = None
        self._was_merged = False

    def match(self, fp, ctx):
        return True

    def consume(self, fp, ctx):
        is_first_line = True
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            if is_first_line:
                line = line.lstrip('!')  # In case it was forced.
                is_first_line = False

            # If the next line is empty, strip the carriage return from
            # the line we just got because it's probably gonna be the
            # last one.
            if RE_EMPTY_LINE.match(fp.peekline()):
                stripped_line = line.rstrip("\r\n")
                self.text += stripped_line
                self._to_merge = line[len(stripped_line):]
                break
            # ...otherwise, add the line with in full.
            self.text += line

        return ANY_STATE

    def merge(self):
        # Put back the stuff we stripped from what we thought was the
        # last line.
        self.text += self._to_merge
        self._was_merged = True

    def exit(self, ctx):
        ctx.document.lastScene().addAction(self.text)


RE_CENTERED_LINE = re.compile(r"^\s*>\s*.*\s*<\s*$", re.M)


class _CenteredActionState(FontaineState):
    def __init__(self):
        super().__init__()
        self.text = ''
        self._aborted = False

    def match(self, fp, ctx):
        lines = fp.peeklines(2)
        return (
            RE_EMPTY_LINE.match(lines[0]) and
            RE_CENTERED_LINE.match(lines[1]))

    def consume(self, fp, ctx):
        snapshot = fp.snapshot()
        fp.readline()  # Get past the empty line.
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            clean_line = line.rstrip('\r\n')
            eol = line[len(clean_line):]

            clean_line = clean_line.strip()
            if clean_line[0] != '>' or clean_line[-1] != '<':
                # The whole paragraph must have `>` and `<` wrappers, so
                # if we detect a line that doesn't have them, we make this
                # paragraph be a normal action instead.
                fp.restore(snapshot)
                self.has_pending_empty_line = True
                self._aborted = True
                return _ActionState()
            else:
                # Remove wrapping `>`/`<`, and spaces.
                clean_line = clean_line[1:-1].strip()

            if RE_EMPTY_LINE.match(fp.peekline()):
                self.text += clean_line
                self.has_pending_empty_line = True
                break
            self.text += clean_line + eol

        return ANY_STATE

    def exit(self, ctx):
        if not self._aborted:
            ctx.document.lastScene().addCenteredAction(self.text)


RE_CHARACTER_LINE = re.compile(r"^\s*[A-Z\-]+\s*(\(.*\))?$", re.M)


class _CharacterState(FontaineState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (RE_EMPTY_LINE.match(lines[0]) and
                RE_CHARACTER_LINE.match(lines[1]) and
                not RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()  # Get past the empty line.
        line = fp.readline().rstrip('\r\n')
        line = line.lstrip()  # Remove indenting.
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
        line = fp.readline().lstrip().rstrip('\r\n')
        ctx.document.lastScene().addParenthetical(line)

        next_line = fp.peekline()
        if not RE_EMPTY_LINE.match(next_line):
            return _DialogState()

        self.has_pending_empty_line = True
        return ANY_STATE


class _DialogState(FontaineState):
    def __init__(self):
        super().__init__()
        self.text = ''

    def match(self, fp, ctx):
        # We only get here from a `_CharacterState` or `_ParentheticalState`
        # so we just need to check there's some text.
        line = fp.peekline()
        return not RE_EMPTY_LINE.match(line)

    def consume(self, fp, ctx):
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            line = line.lstrip()  # Remove indenting.

            # Next we could be either continuing the dialog line, going to
            # a parenthetical, or exiting dialog altogether.
            next_line = fp.peekline()

            if RE_PARENTHETICAL_LINE.match(next_line):
                self.text += line.rstrip('\r\n')
                return _ParentheticalState()

            if RE_EMPTY_LINE.match(next_line):
                self.text += line.rstrip('\r\n')
                self.has_pending_empty_line = True
                break
            self.text += line

        return ANY_STATE

    def exit(self, ctx):
        ctx.document.lastScene().addDialog(self.text.rstrip('\r\n'))


class _LyricsState(FontaineState):
    def __init__(self):
        super().__init__()
        self.text = ''
        self._aborted = False

    # No `match` method, this can only be forced.
    # (see `_ForcedParagraphStates`)

    def consume(self, fp, ctx):
        snapshot = fp.snapshot()
        fp.readline()  # Get past the empty line.
        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            if line.startswith('~'):
                line = line.lstrip('~')
            else:
                logger.debug("Rolling back lyrics into action paragraph.")
                fp.restore(snapshot)
                self.has_pending_empty_line = True
                self._aborted = True
                return _ActionState()

            if RE_EMPTY_LINE.match(fp.peekline()):
                self.text += line.rstrip('\r\n')
                self.has_pending_empty_line = True
                break
            self.text += line

        return ANY_STATE

    def exit(self, ctx):
        if not self._aborted:
            ctx.document.lastScene().addLyrics(self.text)


RE_TRANSITION_LINE = re.compile(r"^\s*[^a-z]+TO\:$", re.M)


class _TransitionState(FontaineState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (
            RE_EMPTY_LINE.match(lines[0]) and
            RE_TRANSITION_LINE.match(lines[1]) and
            RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()  # Get past the empty line.
        line = fp.readline().lstrip().rstrip('\r\n')
        line = line.lstrip('>')  # In case it was forced.
        ctx.document.lastScene().addTransition(line)
        self.has_pending_empty_line = True


RE_PAGE_BREAK_LINE = re.compile(r"^\=\=\=+$", re.M)


class _PageBreakState(FontaineState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (
            RE_EMPTY_LINE.match(lines[0]) and
            RE_PAGE_BREAK_LINE.match(lines[1]) and
            RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()
        fp.readline()
        ctx.document.lastScene().addPageBreak()
        self.has_pending_empty_line = True
        return ANY_STATE


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
        self._consume_empty_line = False

    def match(self, fp, ctx):
        lines = fp.peeklines(2)
        symbol = lines[1][:1]
        if (RE_EMPTY_LINE.match(lines[0]) and
                symbol in self.STATE_SYMBOLS):
            # Special case: don't force a transition state if it's
            # really some centered text.
            if symbol == '>' and RE_CENTERED_LINE.match(lines[1]):
                return False

            self._state_cls = self.STATE_SYMBOLS[symbol]

            # Special case: for forced action paragraphs, don't leave
            # the blank line there.
            if symbol == '!':
                self._consume_empty_line = True

            return True
        return False

    def consume(self, fp, ctx):
        if self._consume_empty_line:
            fp.readline()
        return self._state_cls()


ROOT_STATES = [
    _ForcedParagraphStates,  # Must be first.
    _SceneHeaderState,
    _CharacterState,
    _TransitionState,
    _PageBreakState,
    _CenteredActionState,
    _ActionState,  # Must be last.
]


class _PeekableFile:
    def __init__(self, fp):
        self.line_no = 1
        self._fp = fp
        self._blankAt0 = False

    def readline(self, size=-1):
        if self._blankAt0:
            self._blankAt0 = False
            return '\n'

        data = self._fp.readline(size)
        self.line_no += 1
        return data

    def peekline(self):
        if self._blankAt0:
            return '\n'

        pos = self._fp.tell()
        line = self._fp.readline()
        self._fp.seek(pos)
        return line

    def peeklines(self, count):
        pos = self._fp.tell()
        lines = []
        if self._blankAt0:
            lines.append('\n')
            count -= 1
        for i in range(count):
            lines.append(self._fp.readline())
        self._fp.seek(pos)
        return lines

    def snapshot(self):
        return (self._fp.tell(), self._blankAt0, self.line_no)

    def restore(self, snapshot):
        self._fp.seek(snapshot[0])
        self._blankAt0 = snapshot[1]
        self.line_no = snapshot[2]

    def _addBlankAt0(self):
        if self._fp.tell() != 0:
            raise Exception(
                "Can't add blank line at 0 if reading has started.")
        self._blankAt0 = True

    def _read(self, size, advance_line_no):
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
        # Start with the page title... unless it doesn't match, in which
        # case we start with a "pass through" state that will just return
        # `ANY_STATE` so we can start matching stuff.
        self.state = _TitlePageState()
        if not self.state.match(self.fp, self):
            logger.debug("No title page value found on line 1, "
                         "using pass-through state with added blank line.")
            self.state = _PassThroughState()
            if not RE_EMPTY_LINE.match(self.fp.peekline()):
                # Add a fake empty line at the beginning of the text if
                # there's not one already. This makes state matching easier.
                self.fp._addBlankAt0()
                # Make this added empty line "pending" so if the first line
                # is an action paragraph, it doesn't include it.
                self.state.has_pending_empty_line = True

        # Start parsing! Here we try to do a mostly-forward-only parser with
        # non overlapping regexes to make it decently fast.
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

            elif res is ANY_STATE or isinstance(res, list):
                # State wants to exit, we need to figure out what is the
                # next state.
                pos = self.fp._fp.tell()
                next_states = res
                if next_states is ANY_STATE:
                    next_states = ROOT_STATES
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

                # Handle the current state before we move on to the new one.
                if self.state:
                    if type(self.state) == type(res) and self.state.can_merge:
                        # Don't switch states if the next state is the same
                        # type and that type supports merging.
                        self.state.merge()
                        continue

                    self.state.exit(self)
                    if (self.state.has_pending_empty_line and
                            not res.needs_pending_empty_lines):
                        logger.debug("Skipping pending blank line from %s" %
                                     self.state.__class__.__name__)
                        self.fp.readline()

                self.state = res

            elif isinstance(res, FontaineState):
                # State wants to exit, wants a specific state to be next.
                if self.state:
                    self.state.exit(self)
                    if (self.state.has_pending_empty_line and
                            not res.needs_pending_empty_lines):
                        logger.debug("Skipping pending blank line from %s" %
                                     self.state.__class__.__name__)
                        self.fp.readline()
                self.state = res

            elif res is EOF_STATE:
                # Reached end of file.
                if self.state:
                    self.state.exit(self)
                break

            else:
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
