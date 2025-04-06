"""
Module for loading and processing PTM files with environment variable support.
"""

import os
import re
from importlib.abc import SourceLoader
from itertools import product
from types import ModuleType
from typing import Callable, Pattern

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
    return result


# Regular expression patterns for lexing
lr_space = r'[ \f\t]*'
lr_env_var = r'\${' + lr_space + r'(\w+)' + lr_space + r'}'
lr_str_start = re_group(*_string_prefixes()) + r"('''|\"\"\"|'|\")"
lr_fstr_var = r'{' + lr_space + r'\$({+)' + lr_space + r'(\w+)' + lr_space + r'(}+)' + lr_space + r'}'

# Compiled regex patterns
env_var_pattern: Pattern = re.compile(lr_env_var)
str_start_pattern: Pattern = re.compile(lr_str_start)
fstr_var_pattern: Pattern = re.compile(lr_fstr_var)


def replace_env_var(code: str) -> str:
    """
    Replace environment variable references in code with os.environ lookups.
    
    Args:
        code: The code string to process
        
    Returns:
        str: The processed code with environment variables replaced
    """
    return env_var_pattern.sub(lambda m: f"ptm.environ['{m.group(1).strip()}']", code)


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
    result_lines = []
    lnum = 0

    # State variables for string processing
    in_const_string = False
    in_fstring = False
    string_type = ''
    
    while True:
        try:
            line = readline()
            if not line:
                break
            plog.debug(line)
        except StopIteration:
            break

        lnum += 1
        pos, max = 0, len(line)

        while pos < max:
            plog.debug(pos, max, line[pos:])

            if in_const_string or in_fstring:
                match_string_end = re.search(string_type, line[pos:])

                if in_const_string:
                    if match_string_end:
                        string_body = line[pos:pos+match_string_end.end()]
                        plog.debug(f"handle string body, from {pos} to {pos+match_string_end.end()}:", string_body)
                        result_lines.append(line[pos:pos+match_string_end.end()])
                        pos += len(string_body)
                        in_const_string = False
                        continue
                    else:
                        result_lines.append(line[pos:])
                        break
                
                if in_fstring:
                    match_fstr_var = fstr_var_pattern.search(line[pos:])

                    def paired_braces(match: re.Match) -> bool:
                        """
                        Check if the number of opening and closing braces match.
                        
                        Args:
                            match: The regex match object
                            
                        Returns:
                            bool: True if braces are properly paired
                        """
                        left_braces = len(match.group(1))
                        right_braces = len(match.group(3))
                        return left_braces == right_braces and left_braces % 2 == 1

                    valid_fstr_var = (paired_braces(match_fstr_var) if match_fstr_var else False) and \
                                     (match_string_end.start() > match_fstr_var.start() if match_string_end and match_fstr_var else True)

                    plog.debug(f"match_fstr_var: {match_fstr_var}, valid_fstr_var: {valid_fstr_var}")
                    # 1. string not end, no valid fstr_var
                    if not match_string_end and not valid_fstr_var:
                        result_lines.append(line[pos:])
                        break
                    # 2. string end, no valid fstr_var
                    elif match_string_end and not valid_fstr_var:
                        str_tail = line[pos:pos+match_string_end.end()]
                        result_lines.append(str_tail)
                        pos += len(str_tail)
                        in_fstring = False
                        continue
                    # 3/4. string end, valid fstr_var, string not end, valid fstr_var
                    else: # match_string_end and valid_fstr_var, not match_string_end and valid_fstr_var
                        before_fstr_var = line[pos:pos+match_fstr_var.start()]
                        fstr_var_body = line[pos+match_fstr_var.start():pos+match_fstr_var.end()]
                        plog.debug(f"handle fstring var, from {pos} to {pos+match_fstr_var.end()}:", before_fstr_var + fstr_var_body)
                        result_lines.append(before_fstr_var)
                        result_lines.append(replace_env_var(fstr_var_body))
                        pos += len(line[pos:pos+match_fstr_var.end()])
                        continue

            match_string_start = str_start_pattern.search(line[pos:])

            if match_string_start:
                # Process code before string
                before_string = line[pos:pos+match_string_start.end()]
                plog.debug(f"process code before string, from {pos} to {pos+match_string_start.end()}:", before_string)
                result_lines.append(replace_env_var(before_string))
                pos += len(before_string)

                # Determine string type
                prefix_type = match_string_start.group(1)
                in_fstring = True if 'f' in prefix_type or 'F' in prefix_type else False
                in_const_string = not in_fstring

                string_type = match_string_start.group(2)

                plog.debug(before_string, string_type, in_fstring, in_const_string)
                continue

            else:
                result_lines.append(replace_env_var(line[pos:]))
                break

    plog.debug("PTMLexer done:", result_lines)
    return ''.join(map(str, result_lines))


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
