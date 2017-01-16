import re
import logging
from .document import TYPE_ACTION


logger = logging.getLogger(__name__)


class JouvenceState:
    def __init__(self):
        pass

    def match(self, fp, ctx):
        return False

    def consume(self, fp, ctx):
        raise NotImplementedError()

    def exit(self, ctx, next_state):
        pass


class JouvenceParserError(Exception):
    def __init__(self, line_no, message):
        super().__init__("Error line %d: %s" % (line_no, message))


ANY_STATE = object()
EOF_STATE = object()


# Note how boneyard start/end patterns (/* */) by themselves are
# considered an empty line.
RE_EMPTY_LINE = re.compile(r"^(/\*|\*/)?$", re.M)

RE_TITLE_KEY_VALUE = re.compile(r"^(?P<key>[\w\s\-]+)\s*:\s*")


class _TitlePageState(JouvenceState):
    def __init__(self):
        super().__init__()
        self._cur_key = None
        self._cur_val = None

    def consume(self, fp, ctx):
        line = fp.peekline()
        is_match = RE_TITLE_KEY_VALUE.match(line)
        is_line1_empty = RE_EMPTY_LINE.match(line)
        if not is_match:
            logger.debug("No title page value found on line 1.")
            if not is_line1_empty:
                # Add a fake empty line at the beginning of the text if
                # there's not one already. This makes state matching easier.
                fp._addBlankAt0()
            return ANY_STATE

        while True:
            line = fp.readline()
            if not line:
                return EOF_STATE

            m = RE_TITLE_KEY_VALUE.match(line)
            if m:
                # Commit current value, start new one.
                self._commit(ctx)
                self._cur_key = m.group('key').lower()
                self._cur_val = line[m.end():]
            else:
                # Keep accumulating the value of one of the title page's
                # values.
                self._cur_val += line.lstrip()

            if RE_EMPTY_LINE.match(fp.peekline()):
                if (self._cur_key and
                        not self._cur_val and
                        not ctx.document.title_values):
                    # We thought there was a title page, but it turns out
                    # we probably mistakenly matched something like a
                    # transition.
                    logger.debug("Aborting title page parsing, resetting "
                                 "back to first line.")
                    fp.reset()
                    if not is_line1_empty:
                        fp._addBlankAt0()
                    break

                # Finished with the page title, now move on to the first scene.
                self._commit(ctx)
                break

        return ANY_STATE

    def exit(self, ctx, next_state):
        self._commit(ctx)

    def _commit(self, ctx):
        if self._cur_key is not None:
            val = self._cur_val.rstrip('\r\n')
            ctx.document.title_values[self._cur_key] = val
            self._cur_key = None
            self._cur_val = None


RE_SCENE_HEADER_PATTERN = re.compile(
    r"^(int|ext|est|int/ext|int./ext|i/e)[\s\.]", re.I)


class _SceneHeaderState(JouvenceState):
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
        return ANY_STATE


class _ActionState(JouvenceState):
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
                # Ignore the fake blank line at 0 if it's threre.
                if fp.line_no == 0:
                    continue

                line = line.lstrip('!')  # In case it was forced.
                is_first_line = False

            # If the next line is empty, strip the carriage return from
            # the line we just got because it's probably gonna be the
            # last one.
            if RE_EMPTY_LINE.match(fp.peekline()):
                self.text += line.rstrip("\r\n")
                break
            # ...otherwise, add the line with in full.
            self.text += line

        return ANY_STATE

    def exit(self, ctx, next_state):
        last_para = ctx.document.lastParagraph()
        if last_para and last_para.type == TYPE_ACTION:
            last_para.text += '\n' + self.text
        else:
            ctx.document.lastScene().addAction(self.text)


RE_CENTERED_LINE = re.compile(r"^\s*>\s*.*\s*<\s*$")


class _CenteredActionState(JouvenceState):
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
                self._aborted = True
                return _ActionState()
            else:
                # Remove wrapping `>`/`<`, and spaces.
                clean_line = clean_line[1:-1].strip()

            if RE_EMPTY_LINE.match(fp.peekline()):
                self.text += clean_line
                break
            self.text += clean_line + eol

        return ANY_STATE

    def exit(self, ctx, next_state):
        if not self._aborted:
            ctx.document.lastScene().addCenteredAction(self.text)


RE_CHARACTER_LINE = re.compile(r"^\s*[A-Z][A-Z\-\._\s]+\s*(\(.*\))?$")


class _CharacterState(JouvenceState):
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


RE_PARENTHETICAL_LINE = re.compile(r"^\s*\(.*\)\s*$")


class _ParentheticalState(JouvenceState):
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

        return ANY_STATE


class _DialogState(JouvenceState):
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
                break
            self.text += line

        return ANY_STATE

    def exit(self, ctx, next_state):
        ctx.document.lastScene().addDialog(self.text.rstrip('\r\n'))


class _LyricsState(JouvenceState):
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
                self._aborted = True
                return _ActionState()

            if RE_EMPTY_LINE.match(fp.peekline()):
                self.text += line.rstrip('\r\n')
                break
            self.text += line

        return ANY_STATE

    def exit(self, ctx, next_state):
        if not self._aborted:
            ctx.document.lastScene().addLyrics(self.text)


RE_TRANSITION_LINE = re.compile(r"^\s*[^a-z]+TO\:$")


class _TransitionState(JouvenceState):
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
        return ANY_STATE


RE_PAGE_BREAK_LINE = re.compile(r"^\=\=\=+$")


class _PageBreakState(JouvenceState):
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
        return ANY_STATE


class _ForcedParagraphStates(JouvenceState):
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


RE_BONEYARD_START = re.compile(r"^/\*")
RE_BONEYARD_END = re.compile(r"\*/\s*$")


class _BoneyardState(JouvenceState):
    def match(self, fp, ctx):
        return RE_BONEYARD_START.match(fp.peekline())

    def consume(self, fp, ctx):
        while True:
            fp.readline()
            if RE_BONEYARD_END.match(fp.peekline()):
                break
        return ANY_STATE


RE_SECTION_LINE = re.compile(r"^(?P<depth>#+)\s*")


class _SectionState(JouvenceState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (RE_EMPTY_LINE.match(lines[0]) and
                RE_SECTION_LINE.match(lines[1]) and
                RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()
        line = fp.readline()
        m = RE_SECTION_LINE.match(line)
        depth = len(m.group('depth'))
        line = line[m.end():].rstrip('\r\n')
        ctx.document.lastScene().addSection(depth, line)
        return ANY_STATE


RE_SYNOPSIS_LINE = re.compile(r"^=[^=]")


class _SynopsisState(JouvenceState):
    def match(self, fp, ctx):
        lines = fp.peeklines(3)
        return (RE_EMPTY_LINE.match(lines[0]) and
                RE_SYNOPSIS_LINE.match(lines[1]) and
                RE_EMPTY_LINE.match(lines[2]))

    def consume(self, fp, ctx):
        fp.readline()
        line = fp.readline()
        line = line[1:].lstrip()  # Remove the `#`, and the following spaces.
        line = line.rstrip('\r\n')
        ctx.document.lastScene().addSynopsis(line)
        return ANY_STATE


class _EmptyLineState(JouvenceState):
    def __init__(self):
        super().__init__()
        self.line_count = 0

    def match(self, fp, ctx):
        return RE_EMPTY_LINE.match(fp.peekline())

    def consume(self, fp, ctx):
        line = fp.readline()
        # Increment the number of empty lines to add to the current action,
        # but:
        # - don't take into account the fake blank at 0
        # - don't take into account boneyard endings
        if (fp.line_no > 1 and
                not RE_BONEYARD_END.match(line)):
            self.line_count += 1
        return ANY_STATE

    def exit(self, ctx, next_state):
        if self.line_count > 0:
            text = self.line_count * '\n'
            last_para = ctx.document.lastParagraph()
            if last_para and last_para.type == TYPE_ACTION:
                last_para.text += text
            else:
                ctx.document.lastScene().addAction(text[1:])


ROOT_STATES = [
    _ForcedParagraphStates,  # Must be first.
    _SceneHeaderState,
    _CharacterState,
    _TransitionState,
    _PageBreakState,
    _CenteredActionState,
    _SectionState,
    _SynopsisState,
    _BoneyardState,
    _EmptyLineState,   # Must be second to last.
    _ActionState,  # Must be last.
]


class _PeekableFile:
    def __init__(self, fp):
        self.line_no = 1
        self._fp = fp
        # This is for adding a "fake" blank line at the beginning of the
        # file, to help with match things on the first line.
        # (has blank line, is blank line unread)
        self._blankAt0 = (False, False)

    def readline(self):
        if self._blankAt0[1]:
            self._blankAt0 = (True, False)
            self.line_no = 0
            return '\n'

        data = self._fp.readline()
        self.line_no += 1
        return data

    def peekline(self):
        if self._blankAt0[1]:
            return '\n'

        pos = self._fp.tell()
        line = self._fp.readline()
        self._fp.seek(pos)
        return line

    def peeklines(self, count):
        pos = self._fp.tell()
        lines = []
        if self._blankAt0[1]:
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

    def reset(self):
        self._fp.seek(0)
        if self._blankAt0[0]:
            self._blankAt0 = (True, True)
            self.line_no = 0
        else:
            self._blankAt0 = (False, False)
            self.line_no = 1

    def _addBlankAt0(self):
        if self._fp.tell() != 0:
            raise Exception(
                "Can't add blank line at 0 if reading has started.")
        self._blankAt0 = (True, True)
        self.line_no = 0


class _JouvenceStateMachine:
    def __init__(self, fp, doc):
        self.fp = _PeekableFile(fp)
        self.state = None
        self.document = doc

    @property
    def line_no(self):
        return self.fp.line_no

    def run(self):
        # Start parsing! Here we try to do a mostly-forward-only parser with
        # non overlapping regexes to make it decently fast.
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
                raise JouvenceParserError(
                    self.line_no,
                    "State '%s' returned a `None` result. "
                    "States need to return `ANY_STATE`, one or more specific "
                    "states, or `EOF_STATE` if they reached the end of the "
                    "file." % self.state.__class__.__name__)

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
                    self.state.exit(self, res)
                self.state = res

            elif isinstance(res, JouvenceState):
                # State wants to exit, wants a specific state to be next.
                if self.state:
                    self.state.exit(self, res)
                self.state = res

            elif res is EOF_STATE:
                # Reached end of file.
                if self.state:
                    self.state.exit(self, res)
                break

            else:
                raise Exception("Unsupported state result: %s" % res)


class JouvenceParser:
    """ Parses a Fountain document and returns a
    :class:`~jouvence.document.JouvenceDocument` instance.
    """
    def __init__(self):
        pass

    def parse(self, filein):
        """Parses a file or stream. This must either be a Python file object,
        or the path to file on disk. Returns a
        :class:`~jouvence.document.JouvenceDocument` instance.
        """
        if isinstance(filein, str):
            with open(filein, 'r') as fp:
                return self._doParse(fp)
        else:
            return self._doParse(fp)

    def parseString(self, text):
        """Parses a string. Returns a
        :class:`~jouvence.document.JouvenceDocument` instance.
        """
        import io
        with io.StringIO(text) as fp:
            return self._doParse(fp)

    def _doParse(self, fp):
        from .document import JouvenceDocument
        doc = JouvenceDocument()
        machine = _JouvenceStateMachine(fp, doc)
        machine.run()
        return doc
