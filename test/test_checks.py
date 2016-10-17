import ast
import os

import pytest
try:
    from flake8.engine import pep8
except ImportError:
    import pycodestyle as pep8

from flake8_function_definition.checker import FunctionDefinitionChecker
from test.utils import extract_expected_errors


def load_test_cases():
    base_path = os.path.dirname(__file__)
    test_case_path = os.path.join(base_path, 'test_cases')
    test_case_files = os.listdir(test_case_path)

    test_cases = []

    for fname in test_case_files:
        if not fname.endswith('.py'):
            continue

        fullpath = os.path.join(test_case_path, fname)
        data = open(fullpath).read()
        tree = ast.parse(data, fullpath)
        codes, messages = extract_expected_errors(data)

        test_cases.append((tree, fullpath, codes, messages))

    return test_cases


@pytest.mark.parametrize(
    'tree, filename, expected_codes, expected_messages',
    load_test_cases()
)
def test_expected_error(tree, filename, expected_codes, expected_messages):
    argv = []

    for style in ['google']:
        if style in filename:
            argv.append('--function-definition-style=' + style)
            break

    parser = pep8.get_parser('', '')
    FunctionDefinitionChecker.add_options(parser)
    options, args = parser.parse_args(argv)
    FunctionDefinitionChecker.parse_options(options)

    checker = FunctionDefinitionChecker(tree, filename)
    codes = []
    messages = []
    for lineno, col_offset, msg, instance in checker.run():
        code, message = msg.split(' ', 1)
        codes.append(code)
        messages.append(message)
    assert codes == expected_codes
    assert set(messages) >= set(expected_messages)
