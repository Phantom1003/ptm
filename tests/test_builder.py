import os
import time
from pathlib import Path
import pytest
from ptm.builder import builder, target, targets, task

def test_basic_file_target(tmp_path):
    """Test basic file target with dependencies"""
    target_file = tmp_path / "output.txt"
    dep_file = tmp_path / "input.txt"
    
    # Create dependency file
    dep_file.write_text("input data")
    
    @target(str(target_file), [str(dep_file)])
    def build_output(target, deps):
        with open(deps[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())
    
    # First build
    builder.build(str(target_file))
    assert target_file.exists()
    assert target_file.read_text() == "INPUT DATA"
    
    # Second build should be up to date
    builder.build(str(target_file))
    
    # Modify dependency should trigger rebuild
    time.sleep(0.1)  # Ensure different timestamp
    dep_file.write_text("new data")
    builder.build(str(target_file))
    assert target_file.read_text() == "NEW DATA"

def test_multiple_targets(tmp_path):
    """Test multiple targets from single function"""
    target1 = tmp_path / "output1.txt"
    target2 = tmp_path / "output2.txt"
    dep_file = tmp_path / "input.txt"
    
    dep_file.write_text("input data")
    
    @targets([str(target1), str(target2)], [str(dep_file)])
    def build_outputs(target, deps):
        with open(deps[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())
    
    builder.build(str(target1))
    builder.build(str(target2))
    assert target1.read_text() == "INPUT DATA"
    assert target2.read_text() == "INPUT DATA"

def test_task_target():
    """Test task target (no file output)"""
    results = []
    
    @task()
    def task1(target, deps):
        results.append(1)
    
    @task([task1])
    def task2(target, deps):
        results.append(2)
    
    builder.build(task2)
    assert results == [1, 2]

def test_circular_dependency():
    """Test circular dependency detection"""
    with pytest.raises(ValueError, match="Circular dependency"):
        @target('task1', ['task2'])
        def task1(target, deps):
            pass
            
        @target('task2', ['task1'])
        def task2(target, deps):
            pass
        
        builder.list_targets()
        builder.build('task1')


def test_mixed_dependencies(tmp_path):
    """Test mixing file and function dependencies"""
    target_file = tmp_path / "output.txt"
    results = []
    
    @task()
    def func1(target, deps):
        results.append(1)
    
    @target(str(target_file), [func1])
    def build_output(target, deps):
        results.append(2)
        with open(target, 'w') as f:
            f.write("output")
    
    builder.build(str(target_file))
    assert results == [1, 2]
    assert target_file.read_text() == "output"
