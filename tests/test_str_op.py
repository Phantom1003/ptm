import ptm

def test_str_div():
    # Test basic path concatenation
    assert "path" / "to" / "file" == "path/to/file"
    
    # Test empty string
    assert "" / "test" == "/test"
    assert "test" / "" == "test/"
    
    # Test special characters
    assert "path with spaces" / "file.txt" == "path with spaces/file.txt"
    
    # Test multi-level path
    assert "root" / "dir1" / "dir2" / "file.txt" == "root/dir1/dir2/file.txt"
    
    # Test numeric string
    assert "123" / "456" == "123/456"
    
    # Test Chinese path
    assert "目录" / "文件.txt" == "目录/文件.txt"
