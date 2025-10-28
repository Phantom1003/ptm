import os
import time
import pytest
from ptm.system.builder import builder, target, targets, task

def test_basic_file_target(tmp_path):
    """Test basic file target with dependencies"""
    builder.clean()

    target_file = tmp_path / "output.txt"
    dep_file = tmp_path / "input.txt"
    
    # Create dependency file
    dep_file.write_text("input data")
    
    @target(str(target_file), [str(dep_file)])
    def build_output(target, depends):
        with open(depends[0], 'r') as f:
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
    builder.clean()

    target1 = tmp_path / "output1.txt"
    target2 = tmp_path / "output2.txt"
    dep_file = tmp_path / "input.txt"
    
    dep_file.write_text("input data")
    
    @targets([str(target1), str(target2)], [str(dep_file)])
    def build_outputs(target, depends):
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())

    builder.build(str(target1))
    builder.build(str(target2))
    assert target1.read_text() == "INPUT DATA"
    assert target2.read_text() == "INPUT DATA"

def test_task_target():
    """Test task target (no file output)"""
    builder.clean()

    @task()
    def task1(target, depends):
        pass
    
    @task()
    def task2(target, depends):
        pass
    
    @task()
    def task3(target, depends):
        pass
    
    @task([task1, task2, task3])
    def task4(target, depends):
        pass

    builder.build(task4)

def test_circular_dependency():
    """Test circular dependency detection"""
    builder.clean()

    @target('task1', ['task2'])
    def task1(target, depends):
        pass

    @target('task2', ['task1'])
    def task2(target, depends):
        pass

    builder.build(os.path.abspath("task1"))

def test_not_found_dependency():
    """Test not found dependency detection"""
    builder.clean()

    with pytest.raises(ValueError, match="not found"):
        @task(["some_nonexistent_task"])
        def task1(target, depends):
            pass

        builder.list_targets()
        builder.build(task1)


def test_mixed_dependencies(tmp_path):
    """Test mixing file and function dependencies"""
    builder.clean()

    target_file = tmp_path / "output.txt"
    
    @task()
    def func1(target, depends):
        pass
    
    @target(str(target_file), [func1])
    def build_output(target, depends):
        with open(target, 'w') as f:
            f.write("output")
    
    builder.build(str(target_file))
    assert target_file.read_text() == "output"

def test_dynamic_dependency(tmp_path):
    """Test dynamic dependency resolution"""
    builder.clean()

    input_file = tmp_path / "input.txt"
    target_file = tmp_path / "output.txt"

    @target(input_file)
    def build_input(target, depends):
        with open(target, 'w') as f:
            f.write("phantom-make")

    @target(str(target_file), lambda target: [input_file] if "output" in target else [])
    def build_output(target, depends):
        # read input and write to output
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())
    
    builder.build(str(target_file))
    assert target_file.read_text() == "PHANTOM-MAKE"
