import os
from ptm.loader import *

def iter_lines(code):
    return iter(code.splitlines(True)).__next__

def test_shell_simple():
    """Test shell command syntax."""
    # Basic command execution
    code = 'result = $"ls"'
    expected = 'result = ptm.exec_cmd(f"ls")'
    assert PTMLexer(iter_lines(code)) == expected

    # Standard output capture
    code = 'output = $>"ls"'
    expected = 'output = ptm.exec_cmd_stdout(f"ls")'
    assert PTMLexer(iter_lines(code)) == expected

    # Standard error capture
    code = 'error = $>>"ls"'
    expected = 'error = ptm.exec_cmd_stderr(f"ls")'
    assert PTMLexer(iter_lines(code)) == expected

    # Combined output
    code = 'all = $&"ls"'
    expected = 'all = ptm.exec_cmd_stdout_stderr(f"ls")'
    assert PTMLexer(iter_lines(code)) == expected

    # Command with environment variable
    code = 'result = $"echo ${USER}"'
    expected = 'result = ptm.exec_cmd(f"echo ${USER}")'
    assert PTMLexer(iter_lines(code)) == expected

def test_shell_nested():
    # Command in f-string
    code = "result = f\"Output: {$>'ls'}\""
    expected = 'result = f"Output: {ptm.exec_cmd_stdout(f\'ls\')}"'
    assert PTMLexer(iter_lines(code)) == expected

def test_shell_multiline():
    """Test multi-line shell commands."""
    code = '''
result = $"ls -l;
grep test"'''
    expected = '\nresult = ptm.exec_cmd(f"ls -l;\ngrep test")'
    assert PTMLexer(iter_lines(code)) == expected

    code = '''
result = f"Output:
{$>"ls -l; grep test"}"'''
    expected = '\nresult = f"Output:\n{ptm.exec_cmd_stdout(f"ls -l; grep test")}"'
    assert PTMLexer(iter_lines(code)) == expected

def test_shell_in_multiline_cmd():
    """Test shell commands in multi-line strings."""
    code = '''
result = $>"""ls -l;
sleep 10"""'''
    expected = '\nresult = ptm.exec_cmd_stdout(f"""ls -l;\nsleep 10""")'
    assert PTMLexer(iter_lines(code)) == expected

    code = '''
result = f"""Output:
{
$>"ls -l"
}"""'''
    expected = '\nresult = f"""Output:\n{\nptm.exec_cmd_stdout(f"ls -l")\n}"""'''
    assert PTMLexer(iter_lines(code)) == expected
