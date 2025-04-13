"""
Module for loading and processing PTM files with environment variable support.
"""

import os
import re
from importlib.abc import SourceLoader
from itertools import product
from types import ModuleType
from typing import Callable, Pattern, List, Optional

from .logger import plog


def re_group(*sub: str) -> str:
    """
    Create a regex group from multiple subpatterns.
    
    Args:
        *sub: Variable number of subpatterns to combine
        
    Returns:
        str: A regex group containing all subpatterns
    """
    return '(' + '|'.join(sub) + ')'


shell_prefix_map = {
    "$": "ptm.exec_cmd",
    "$>": "ptm.exec_cmd_stdout",
    "$>>": "ptm.exec_cmd_stderr",
    "$&": "ptm.exec_cmd_stdout_stderr",
}

def _string_prefixes() -> set[str]:
    """
    Generate all valid string prefixes for Python strings.
    
    Returns:
        set[str]: Set of all valid string prefixes
    """
    valid_prefixes = ['b', 'r', 'u', 'f', 'br', 'fr']
    result = {''}
    for prefix in valid_prefixes:
        result.update(''.join(p) for p in product(*[[c, c.upper()] for c in prefix]))
        result.update(''.join(p) for p in product(*[[c, c.upper()] for c in prefix[::-1]]))
    return list(result) + list(f"\\{prefix}" for prefix in shell_prefix_map.keys())


# Regular expression patterns for lexing
lr_space = r'[ \f\t]*'
lr_env_var = r'\${' + lr_space + r'(\w+)' + lr_space + r'}'
lr_str_start = re_group(*_string_prefixes()) + r"('''|\"\"\"|'|\")"
lr_fvar_start = r'[^\${]*(({{)*{(?!{))'

# Compiled regex patterns
env_var_pattern: Pattern = re.compile(lr_env_var)
str_start_pattern: Pattern = re.compile(lr_str_start)
fvar_start_pattern: Pattern = re.compile(lr_fvar_start)


def replace_env_var(code: str) -> str:
    """
    Replace environment variable references in code with os.environ lookups.
    
    Args:
        code: The code string to process
        
    Returns:
        str: The processed code with environment variables replaced
    """
    return env_var_pattern.sub(lambda m: f"ptm.environ.{m.group(1).strip()}", code)


class LexerState:
    """State for a string being processed."""
    def __init__(self, type: str, open: str):
        self.type = type
        self.open = open

    @property
    def close(self) -> str:
        if "'" in self.open:
            return "'" * len(self.open)
        elif '"' in self.open:
            return '"' * len(self.open)
        elif "{" in self.open:
            return "}" * len(self.open)
        else:
            assert False, f"Invalid open delimiter: {repr(self.open)}"


class LexerMachine:
    """State machine for the lexer."""
    def __init__(self):
        self.result_lines: List[str] = []
        self.state_stack: List[LexerState] = [LexerState("code", "")]

    def process_line(self, line: str) -> None:
        """Process a single line of input."""
        pos = 0
        while pos < len(line):
            current_state = self.state_stack[-1]
            if current_state.type == "code":
                pos += self._process_code(line[pos:])
            elif current_state.type == "string":
                pos += self._process_const_string(line[pos:], current_state.close)
            elif current_state.type == "fstring":
                pos += self._process_fstring(line[pos:], current_state.close)
            elif current_state.type == "fstring_code":
                pos += self._process_fstring_code(line[pos:], current_state.close)
            elif current_state.type == "shell":
                pos += self._process_fstring(line[pos:], current_state.close, ")")
            else:
                assert False, f"Invalid state: {current_state.type}"


    def _process_code(self, text: str) -> int:
        match_str_start = str_start_pattern.search(text)

        if match_str_start:
            self.result_lines.append(replace_env_var(text[:match_str_start.start()]))

            prefix_type = match_str_start.group(1)
            quote_type = match_str_start.group(2)
            is_fstring = any(c in prefix_type for c in ['f', 'F', '$'])
            is_shell_cmd = prefix_type in shell_prefix_map

            if is_shell_cmd:
                self.result_lines.append(shell_prefix_map[prefix_type] + "(")
                self.result_lines.append("f" + quote_type)
                self.state_stack.append(LexerState("shell", quote_type))
            else:
                self.result_lines.append(prefix_type)
                self.result_lines.append(quote_type)
                self.state_stack.append(LexerState("fstring" if is_fstring else "string", quote_type))

            return match_str_start.end()
        else:
            self.result_lines.append(replace_env_var(text))
            return len(text)

    def _process_const_string(self, text: str, close: str) -> int:
        match_str_close = re.search(close, text)

        if match_str_close:
            self.result_lines.append(text[:match_str_close.end()])
            self.state_stack.pop()
            return match_str_close.end()
        else:
            self.result_lines.append(text)
            return len(text)


    def _process_fstring(self, text: str, close: str, suffix: Optional[str] = None) -> int:
        match_fstr_close = re.search(close, text)
        match_fvar_start = re.search(fvar_start_pattern, text[:match_fstr_close.end()]) if match_fstr_close else re.search(fvar_start_pattern, text)

        if match_fvar_start:
            self.result_lines.append(text[:match_fvar_start.end()])
            self.state_stack.append(LexerState("fstring_code", match_fvar_start.group(1)))
            return match_fvar_start.end()
        else:
            if match_fstr_close:
                self.result_lines.append(text[:match_fstr_close.end()])
                self.state_stack.pop()
                if suffix:
                    self.result_lines.append(suffix)
                return match_fstr_close.end()
            else:
                self.result_lines.append(text)
                return len(text)
    
    def _process_fstring_code(self, text: str, close: str) -> int:
        match_fstr_close = re.search(fr"({lr_env_var})*{close}", text)
        match_sub_str_start = re.search(str_start_pattern, text[:match_fstr_close.end()]) if match_fstr_close else re.search(str_start_pattern, text)

        if match_sub_str_start:
            return self._process_code(text)
        else:
            if match_fstr_close:
                self.result_lines.append(replace_env_var(text[:match_fstr_close.end()]))
                self.state_stack.pop()
                return match_fstr_close.end()
            else:
                self.result_lines.append(replace_env_var(text))
                return len(text)

def PTMLexer(readline: Callable[[], str]) -> str:
    """
    Lexer for processing PTM files with environment variable support.
    
    This lexer handles string literals and f-strings, replacing environment
    variable references with appropriate os.environ lookups.
    
    Args:
        readline: A callable that returns the next line of the file
        
    Returns:
        str: The processed code with environment variables replaced
    """
    m = LexerMachine()

    while True:
        try:
            line = readline()
            if not line:
                break
            plog.debug(line)
        except StopIteration:
            break

        m.process_line(line)

    plog.debug("PTMLexer done:", m.result_lines)
    return ''.join(map(str, m.result_lines))


class PTMLoader(SourceLoader):
    """
    Custom loader for PTM files that processes environment variables.
    """
    
    def __init__(self, fullname: str, path: str):
        """
        Initialize the PTM loader.
        
        Args:
            fullname: The full name of the module
            path: The path to the module file
        """
        self.fullname = fullname
        self.path = path
        self.cache = None
        self.type = "ptm" if path.endswith(".ptm") else "py"

        # generate de-sugared cache file
        if self.type == "ptm":
            self.cache = os.path.join(os.path.dirname(self.path), f".{os.path.basename(self.path)}.py")
            if not self._is_cache_valid():
                plog.info(f"Generating de-sugared PTM file: {self.cache}")
                with open(self.path, "r", encoding="utf-8") as f:
                        content = PTMLexer(f.readline)
                with open(self.cache, "w", encoding="utf-8") as f:
                    f.write(content)

    def _is_cache_valid(self) -> bool:
        """
        Check if the cached file is still valid.
            
        Returns:
            bool: True if cache is valid
        """
        if not os.path.exists(self.cache):
            return False
        
        ptm_mtime = os.path.getmtime(self.path)
        cache_mtime = os.path.getmtime(self.cache)
        
        return cache_mtime >= ptm_mtime

    def get_filename(self, fullname: str) -> str:
        """
        Get the filename for the module.
        
        Args:
            fullname: The full name of the module
            
        Returns:
            str: The path to the module file
        """
        if self.type == "ptm":
            return self.cache
        else:
            return self.path

    def get_data(self, path: str) -> bytes:
        """
        Get the processed data from the PTM file.
        
        Args:
            path: The path to the module file

        Returns:
            bytes: The processed module data
        """
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return content.encode("utf-8")

    def exec_module(self, module: ModuleType):
        """
        Execute the module.
        """
        try:
            exec(compile(self.get_data(self.get_filename("")), "<PTM>", "exec"), module.__dict__)
        except Exception as e:
            if self.type == "ptm":
                print(f"Failed to execute the translated PTM file: {self.cache}, please check the original PTM file: {self.path}")
            raise e
