import pytest
import os
import sys
import platform
from ptm import include

if platform.system().lower() == 'windows':
    user = 'phantom'
    path = '/bin'
    home = '/home/phantom'
    os.environ['USER'] = user
    os.environ['PATH'] = path
    os.environ['HOME'] = home

@pytest.fixture
def simple_ptm_file(tmp_path):
    module_name = "simple"
    tmp_content = """
# Environment variables in this file will be automatically replaced during import
print("wow, ptm file:", __file__)
message = f"Hello {${USER}}!"
path = ${PATH}
home = ${HOME}
"""

    tmp_file = tmp_path / f"{module_name}.ptm"
    tmp_file.write_text(tmp_content)
    return tmp_file

def test_include_simple(simple_ptm_file):
    """Test basic functionality of include function"""
    module = include(str(simple_ptm_file))

    assert module.message == f"Hello {os.environ['USER']}!"
    assert module.path == os.environ['PATH']
    assert module.home == os.environ['HOME']
    assert module.__file__ == str(simple_ptm_file)

def test_include_nonexistent_file():
    """Test importing a non-existent file"""
    with pytest.raises(FileNotFoundError):
        include("/nonexistent/file.ptm")

def test_include_relative(simple_ptm_file):
    """Test using relative path"""
    original_cwd = os.getcwd()
    os.chdir(simple_ptm_file.parent)

    try:
        module = include(simple_ptm_file.name)

        assert module.message == f"Hello {os.environ['USER']}!"
        assert module.path == os.environ['PATH']
        assert module.home == os.environ['HOME']
        assert module.__file__ == str(simple_ptm_file)
    finally:
        os.chdir(original_cwd)

def test_include_nested_relative_path(simple_ptm_file):
    """Test using nested relative path"""
    nested_dir = simple_ptm_file.parent / "sub" / "dir"
    nested_dir.mkdir(parents=True)
    
    # Create the PTM file
    ptm_content = "simple = include('../../simple.ptm')"
    ptm_file = nested_dir / "nested.ptm"
    ptm_file.write_text(ptm_content)

    module = include(str(ptm_file))
    sub_module = module.simple

    assert sub_module.message == f"Hello {os.environ['USER']}!"
    assert sub_module.path == os.environ['PATH']
    assert sub_module.home == os.environ['HOME']
    assert sub_module.__file__ == str(simple_ptm_file)

def test_include_subdirectory_relative_path(tmp_path):
    """Test using subdirectory relative path"""
    first_level_ptm = tmp_path / "build.ptm"
    second_level_ptm = tmp_path / "sub1" / "build.ptm"
    third_level_ptm = tmp_path / "sub1" / "sub2" / "build.ptm"
    third_level_ptm.parent.mkdir(parents=True)

    first_level_ptm.write_text("second = include('sub1/build.ptm')")
    second_level_ptm.write_text("third = include('sub2/build.ptm')")
    third_level_ptm.write_text("USER = ${USER}")

    first = include(str(first_level_ptm))
    assert first.second.third.__file__ == str(third_level_ptm)
    assert first.second.third.USER == os.environ['USER']

def test_include_subdirectory_relative_path2(tmp_path):
    """Test using subdirectory relative path"""
    second_level_ptm = tmp_path / "sub1" / "build.ptm"
    third_level_ptm = tmp_path / "sub1" / "sub2" / "build.ptm"
    third_level_ptm.parent.mkdir(parents=True)

    second_level_ptm.write_text("third = include('sub2/build.ptm')")
    third_level_ptm.write_text("USER = ${USER}")

    second = include(str(second_level_ptm))
    assert second.third.__file__ == str(third_level_ptm)
    assert second.third.USER == os.environ['USER']
