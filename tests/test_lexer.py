import os
from ptm.loader import *

def iter_lines(code):
    return iter(code.splitlines(True)).__next__

def test_single_line_code():
    assert PTMLexer(iter_lines("user = ${USER}")) == "user = os.environ['USER']"
    assert PTMLexer(iter_lines("user = ${ USER }")) == "user = os.environ['USER']"

def test_lexer_single_line_const_string():
    assert PTMLexer(iter_lines('user = "${USER} ${HOME}"')) == 'user = "${USER} ${HOME}"'
    assert PTMLexer(iter_lines('user = "${ USER }"')) == 'user = "${ USER }"'

def test_lexer_single_line_fstring():
    assert PTMLexer(iter_lines('user = f"{${USER}}"')) == 'user = f"{os.environ[\'USER\']}"'
    assert PTMLexer(iter_lines('user = f"${{USER}}"')) == 'user = f"${{USER}}"'
    assert PTMLexer(iter_lines('user = f"{${USER}}" + f"${HOME}"')) == 'user = f"{os.environ[\'USER\']}" + f"${HOME}"'

def test_lexer_multiple_line_const_string():
    code = 'f\"\"\"${USER} ${HOME}\n${USER}\"\"\"'
    done = 'f\"\"\"${USER} ${HOME}\n${USER}\"\"\"'
    assert PTMLexer(iter_lines(code)) == done

def test_lexer_multiple_line_const_fstring():
    code = 'f\"\"\"{${USER}} {${HOME}}\n${USER}\"\"\"'
    done = 'f\"\"\"{os.environ[\'USER\']} {os.environ[\'HOME\']}\n${USER}\"\"\"'
    assert PTMLexer(iter_lines(code)) == done
