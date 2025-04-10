from ptm.loader import *

def iter_lines(code):
    return iter(code.splitlines(True)).__next__
 
def test_lexer_env_single_line_code():
    """Test environment variables in single line code."""
    assert PTMLexer(iter_lines("user = ${USER}")) == "user = ptm.environ.USER"
    assert PTMLexer(iter_lines("user = ${ USER }")) == "user = ptm.environ.USER"

def test_lexer_env_single_line_const_string():
    """Test environment variables in single line constant strings."""
    assert PTMLexer(iter_lines('user = "${USER} ${HOME}"')) == 'user = "${USER} ${HOME}"'
    assert PTMLexer(iter_lines('user = "${ USER }"')) == 'user = "${ USER }"'

def test_lexer_env_single_line_fstring():
    """Test environment variables in single line f-strings."""
    assert PTMLexer(iter_lines('user = f"{${USER}}"')) == 'user = f"{ptm.environ.USER}"'
    assert PTMLexer(iter_lines('user = f"${{USER}}"')) == 'user = f"${{USER}}"'
    assert PTMLexer(iter_lines('user = f"{${USER}}" + f"${HOME}"')) == 'user = f"{ptm.environ.USER}" + f"${HOME}"'

def test_lexer_env_multiple_line_const_string():
    """Test environment variables in multi-line constant strings."""
    code = 'f\"\"\"${USER} ${HOME}\n${USER}\"\"\"'
    done = 'f\"\"\"${USER} ${HOME}\n${USER}\"\"\"'
    assert PTMLexer(iter_lines(code)) == done


def test_lexer_env_multiple_line_const_fstring():
    """Test environment variables in multi-line f-strings."""
    code = 'f\"\"\"{${USER}} {${HOME}}\n${USER}\"\"\"'
    done = 'f\"\"\"{ptm.environ.USER} {ptm.environ.HOME}\n${USER}\"\"\"'
    assert PTMLexer(iter_lines(code)) == done

def test_lexer_env_nested_fstring():
    """Test environment variables in nested f-strings."""
    code = 'f\"${USER} {f\'{${HOME}}\'}\"'
    done = 'f\"${USER} {f\'{ptm.environ.HOME}\'}\"'
    assert PTMLexer(iter_lines(code)) == done

