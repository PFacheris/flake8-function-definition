import ast
import collections
import optparse
import tokenize

from flake8_function_definition.__about__ import __version__
from flake8_function_definition import DEFAULT_FUNCTION_DEFINITON_STYLE

# Polyfill stdin loading/reading lines
# https://gitlab.com/pycqa/flake8-polyfill/blob/1.0.1/src/flake8_polyfill/stdin.py#L52-57
try:
    from flake8.engine import pep8
    stdin_get_value = pep8.stdin_get_value
    readlines = pep8.readlines
except ImportError:
    from flake8 import utils
    import pycodestyle as pep8
    stdin_get_value = utils.stdin_get_value
    readlines = pep8.readlines


Error = collections.namedtuple('Error', ['lnum', 'col', 'type', 'text'])


class FunctionDefinitionChecker(object):
    name = __name__
    version = __version__
    options = dict()

    def __init__(self, tree, filename):
        self.filename = filename
        self.tree = tree
        self.lines = None

    @staticmethod
    def _register_opt(parser, *args, **kwargs):
        """
        Handler to register an option for both Flake8 3.x and 2.x.
        This is based on:
        https://github.com/PyCQA/flake8/blob/3.0.0b2/docs/source/plugin-development/cross-compatibility.rst#option-handling-on-flake8-2-and-3
        It only supports `parse_from_config` from the original function and it
        uses the `Option` object returned to get the string.
        """
        try:
            # Flake8 3.x registration
            parser.add_option(*args, **kwargs)
        except (optparse.OptionError, TypeError):
            # Flake8 2.x registration
            parse_from_config = kwargs.pop('parse_from_config', False)
            option = parser.add_option(*args, **kwargs)
            if parse_from_config:
                parser.config_options.append(
                    option.get_opt_string().lstrip('-')
                )

    @classmethod
    def add_options(cls, parser):
        cls._register_opt(
            parser,
            '--function-definition-style',
            default=DEFAULT_FUNCTION_DEFINITON_STYLE,
            action='store',
            type='string',
            help=('Style to follow. Available: '
                  'google'),
            parse_from_config=True,
        )

    @classmethod
    def parse_options(cls, options):
        options_dict = dict(
            function_defintion_style=options.function_definition_style
        )
        cls.options = options_dict

    def load_file(self):
        if self.filename in ('stdin', '-', None):
            self.filename = 'stdin'
            self.lines = stdin_get_value().splitlines(True)
        else:
            self.lines = readlines(self.filename)

        if not self.tree:
            self.tree = ast.parse(''.join(self.lines))

    def run(self):
        for error in self.get_function_definition_errors():
            yield (
                error.lnum,
                error.col,
                "{0} {1}".format(error.type, error.text),
                self
            )

    def get_function_definition_errors(self):
        if not self.tree or not self.lines:
            self.load_file()

        style_option = self.options.get(
            'function_definition_style', DEFAULT_FUNCTION_DEFINITON_STYLE,
        )

        # Walk the tree getting FunctionDef instances and checking style from
        # the start to end line.
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if pep8.noqa(self.lines[node.lineno - 1]):
                continue
            check_with_style = getattr(
                self,
                '_check_function_definition_%s' % style_option
            )
            for error in check_with_style(node):
                yield error

    def _check_function_definition_google(self, node):
        """
        Check that a given FunctionDef node abides by the style:
        def foo(bar1, bar2, bar3, bar4
                bar5, bar6, bar7, bar8
                bar9):
        """
        # Calculate the node end line using the next node's start line,
        # this value may lead to blank lines being included when tokenize
        # is called, but that shouldn't be a problem.
        next_node = self._get_next_node(node)
        if next_node:
            node_end_lineno = next_node.lineno - 1
        else:
            node_end_lineno = len(self.lines)
        # Ensure first and last args on the same line as the beginning and
        # end of the function definition respectively.
        previous_tokens = []
        def_token = name_token = None
        start_token = start_arg_token = None
        end_token = end_arg_token = None
        for t in tokenize.generate_tokens(
            lambda L=iter(
                self.lines[node.lineno - 1:node_end_lineno - 1]
            ): next(L)
        ):
            token = Token(t)
            if not start_token:
                # Set tokens if unset and pattern detected.
                if token.string == 'def' and token.type == tokenize.NAME:
                    def_token = token
                if (
                    def_token and token.string == node.name and
                    token.type == tokenize.NAME
                ):
                    name_token = token
                if (
                    def_token and name_token and
                    token.string == '(' and token.type == tokenize.OP
                ):
                    start_token = token
                    # Make sure the start_token is on the same line the def and
                    # function name.
                    if any([
                        pt.start_row != token.start_row for
                        pt in (def_token, name_token)
                    ]):
                        yield Error(
                            node.lineno - 1 + token.start_row,
                            token.start_col,
                            'FD103',
                            'def and function name must appear on the same '
                            'line.'
                        )
            else:
                # Since the start_token was already encountered, these values
                # are variable in the function defintion.
                if token.type == tokenize.NAME:
                    if not start_arg_token:
                        start_arg_token = token
                        if start_token.start_row != start_arg_token.start_row:
                            yield Error(
                                node.lineno - 1 + token.start_row,
                                token.start_col,
                                'FD101',
                                'First argument must be on same line as '
                                'the function definition.'
                            )
                    end_arg_token = token
                elif (token.string == ':' and token.type == tokenize.OP and
                      previous_tokens[-1].string == ')' and
                      previous_tokens[-1].type == tokenize.OP):
                    end_token = token
                    if (
                        end_arg_token and
                        end_token.start_row != end_arg_token.start_row
                    ):
                        yield Error(
                                node.lineno - 1 + token.start_row,
                                token.start_col,
                                'FD102',
                                'Function definition must end on same line as '
                                'last argument.'
                            )
                    break
            previous_tokens.append(token)

    @classmethod
    def _get_parent_node(cls, node, root):
        if node is root or not hasattr(root, 'body'):
            return None
        if node in root.body:
            return root
        parent = None
        for child in root.body:
            parent = cls._get_parent_node(node, child)
            if parent:
                return parent

    def _get_next_node(self, node):
        if node == self.tree:
            return None
        parent = self.__class__._get_parent_node(node, self.tree)
        node_index = parent.body.index(node)
        if len(parent.body) < node_index + 2:
            # See if the parent has next sibling, otherwise return None
            return self._get_next_node(parent)
        else:
            return parent.body[node_index + 1]


class Token:
    '''Python 2 and 3 compatible token'''
    def __init__(self, token):
        self.token = token

    @property
    def type(self):
        return self.token[0]

    @property
    def string(self):
        return self.token[1]

    @property
    def start(self):
        return self.token[2]

    @property
    def start_row(self):
        return self.token[2][0]

    @property
    def start_col(self):
        return self.token[2][1]
