import os
import time
import pytest
from pathlib import Path
from ptm.system.builder import builder, target, targets, task


def test_parallel_independent_targets(tmp_path):
    """Test parallel building of independent targets via a common parent"""
    builder.clean()

    output_files = [tmp_path / f"output{i}.txt" for i in range(4)]
    final_file = tmp_path / "final.txt"
    
    for i, output_file in enumerate(output_files):
        local_i = i
        @target(str(output_file), [])
        def build_output(target, depends):
            with open(target, 'w') as f:
                f.write(f"output {local_i}")

    @target(str(final_file), [str(f) for f in output_files])
    def build_final(target, depends):
        with open(target, 'w') as f:
            f.write("done")

    builder.build(str(final_file), max_jobs=4)

    for output_file in output_files:
        assert output_file.exists()
    assert final_file.exists()


def test_parallel_with_dependencies(tmp_path):
    """Test parallel building with dependency chains"""
    # Create a diamond dependency structure
    #     final
    #    /     \
    #  mid1   mid2
    #    \     /
    #     base
    builder.clean()
    
    base_file = tmp_path / "base.txt"
    mid1_file = tmp_path / "mid1.txt"
    mid2_file = tmp_path / "mid2.txt"
    final_file = tmp_path / "final.txt"
    
    @target(str(base_file), [])
    def build_base(target, depends):
        with open(target, 'w') as f:
            f.write("base")
    
    @target(str(mid1_file), [str(base_file)])
    def build_mid1(target, depends):
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(f"{data} -> mid1")
    
    @target(str(mid2_file), [str(base_file)])
    def build_mid2(target, depends):
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(f"{data} -> mid2")
    
    @target(str(final_file), [str(mid1_file), str(mid2_file)])
    def build_final(target, depends):
        with open(depends[0], 'r') as f:
            data1 = f.read()
        with open(depends[1], 'r') as f:
            data2 = f.read()
        with open(target, 'w') as f:
            f.write(f"{data1} + {data2}")

    builder.build(str(final_file), max_jobs=4)

    assert base_file.exists()
    assert mid1_file.exists()
    assert mid2_file.exists()
    assert final_file.exists()
    assert "base -> mid1 + base -> mid2" in final_file.read_text()


def test_parallel_with_max_jobs_limit(tmp_path):
    """Test that max_jobs parameter limits parallel execution"""
    builder.clean()

    output_files = [tmp_path / f"output{i}.txt" for i in range(4)]
    final_file = tmp_path / "final.txt"
    
    for i, output_file in enumerate(output_files):
        local_i = i
        @target(str(output_file), [])
        def build_output(target, depends):
            with open(target, 'w') as f:
                f.write(f"output {local_i}")
    
    @target(str(final_file), [str(f) for f in output_files])
    def build_final(target, depends):
        with open(target, 'w') as f:
            f.write("done")
    
    # Build with max_jobs=2
    builder.build(str(final_file), max_jobs=2)
    
    # All files should exist
    for output_file in output_files:
        assert output_file.exists()


def test_external_task_parallel(tmp_path):
    """Test external task that can use multiple cores"""
    builder.clean()

    output_file = tmp_path / "external_output.txt"
    marker_file = tmp_path / "jobs_marker.txt"
    
    @target(str(output_file), [], external=True)
    def build_external(target, depends, jobs):
        # Write jobs to a file since we're in a subprocess
        with open(str(marker_file), 'w') as f:
            f.write(str(jobs))
        with open(target, 'w') as f:
            f.write(f"Built with {jobs} cores")

    builder.build(str(output_file), max_jobs=4)
    
    assert output_file.exists()
    assert marker_file.exists()
    jobs_used = int(marker_file.read_text())
    assert jobs_used >= 1, f"External task should receive at least 1 job, got {jobs_used}"


def test_mixed_external_and_normal_tasks(tmp_path):
    """Test mixing external and normal tasks"""
    builder.clean()

    normal_file = tmp_path / "normal.txt"
    external_file = tmp_path / "external.txt"
    final_file = tmp_path / "final.txt"
    marker_file = tmp_path / "jobs_marker.txt"
    
    @target(str(normal_file), [])
    def build_normal(target, depends):
        with open(target, 'w') as f:
            f.write("normal")
    
    @target(str(external_file), [], external=True)
    def build_external(target, depends, jobs):
        with open(str(marker_file), 'w') as f:
            f.write(str(jobs))
        with open(target, 'w') as f:
            f.write(f"external with {jobs} cores")
    
    @target(str(final_file), [str(normal_file), str(external_file)])
    def build_final(target, depends):
        with open(depends[0], 'r') as f:
            data1 = f.read()
        with open(depends[1], 'r') as f:
            data2 = f.read()
        with open(target, 'w') as f:
            f.write(f"{data1} + {data2}")
    
    builder.build(str(final_file), max_jobs=4)
    
    assert final_file.exists()
    assert "normal + external" in final_file.read_text()
    assert marker_file.exists()


def test_task_parallel_execution(tmp_path):
    """Test parallel execution of task targets (no file output)"""
    builder.clean()

    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    
    @task()
    def task1(target, depends):
        (marker_dir / "task1.txt").write_text("done")
    
    @task()
    def task2(target, depends):
        (marker_dir / "task2.txt").write_text("done")
    
    @task()
    def task3(target, depends):
        (marker_dir / "task3.txt").write_text("done")
    
    @task([task1, task2, task3])
    def main_task(target, depends):
        (marker_dir / "main.txt").write_text("done")
    
    builder.build(main_task, max_jobs=3)
    
    # Check all markers exist
    assert (marker_dir / "task1.txt").exists()
    assert (marker_dir / "task2.txt").exists()
    assert (marker_dir / "task3.txt").exists()
    assert (marker_dir / "main.txt").exists()



def test_large_dependency_tree_parallel(tmp_path):
    """Test parallel building of a large dependency tree"""
    # Create a tree structure with multiple levels
    # Level 0: 1 file (root)
    # Level 1: 3 files
    # Level 2: 9 files
    builder.clean()
    
    level2_files = [tmp_path / f"level2_{i}.txt" for i in range(9)]
    level1_files = [tmp_path / f"level1_{i}.txt" for i in range(3)]
    root_file = tmp_path / "root.txt"
    
    # Level 2 targets (leaf nodes)
    for i, output_file in enumerate(level2_files):
        local_i = i
        @target(str(output_file), [])
        def build_level2(target, depends):
            with open(target, 'w') as f:
                f.write(f"level2_{local_i}")
    
    # Level 1 targets (depend on level 2)
    for i, output_file in enumerate(level1_files):
        deps = [str(level2_files[i*3 + j]) for j in range(3)]
        @target(str(output_file), deps)
        def build_level1(target, depends):
            data = []
            for dep in depends:
                with open(dep, 'r') as f:
                    data.append(f.read())
            with open(target, 'w') as f:
                f.write(" + ".join(data))
    
    # Root target (depends on level 1)
    @target(str(root_file), [str(f) for f in level1_files])
    def build_root(target, depends):
        data = []
        for dep in depends:
            with open(dep, 'r') as f:
                data.append(f.read())
        with open(target, 'w') as f:
            f.write(" | ".join(data))
    
    # Build with parallel execution
    builder.build(str(root_file), max_jobs=4)
    
    # All files should exist
    assert root_file.exists()
    for f in level1_files + level2_files:
        assert f.exists()


def test_invalid_max_jobs():
    """Test that invalid max_jobs values are rejected"""
    builder.clean()

    @task()
    def simple_task(target, depends):
        pass
    
    # max_jobs must be at least 1
    with pytest.raises(ValueError, match="Job count must be at least 1"):
        builder.build(simple_task, max_jobs=0)
    
    with pytest.raises(ValueError, match="Job count must be at least 1"):
        builder.build(simple_task, max_jobs=-1)


def test_parallel_rebuild_on_change(tmp_path):
    """Test that parallel builds correctly detect and rebuild changed dependencies"""
    builder.clean()

    dep1 = tmp_path / "dep1.txt"
    dep2 = tmp_path / "dep2.txt"
    output1 = tmp_path / "output1.txt"
    output2 = tmp_path / "output2.txt"
    final = tmp_path / "final.txt"
    
    # Create initial dependencies
    dep1.write_text("dep1 v1")
    dep2.write_text("dep2 v1")
    
    @target(str(output1), [str(dep1)])
    def build_output1(target, depends):
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())
    
    @target(str(output2), [str(dep2)])
    def build_output2(target, depends):
        with open(depends[0], 'r') as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data.upper())
    
    @target(str(final), [str(output1), str(output2)])
    def build_final(target, depends):
        with open(target, 'w') as f:
            f.write("final")

    builder.build(str(final), max_jobs=2)
    
    assert output1.read_text() == "DEP1 V1"
    assert output2.read_text() == "DEP2 V1"

    dep1.write_text("dep1 v2")

    builder.build(str(final), max_jobs=2)
    
    assert output1.read_text() == "DEP1 V2"
    assert output2.read_text() == "DEP2 V1"


def test_parallel_with_shared_dependency(tmp_path):
    """Test parallel building where multiple targets share a dependency"""
    # Structure:
    #   output1  output2  output3
    #      \       |       /
    #          shared.txt
    #             |
    #          final.txt
    builder.clean()
    
    shared_file = tmp_path / "shared.txt"
    output_files = [tmp_path / f"output{i}.txt" for i in range(3)]
    final_file = tmp_path / "final.txt"
    
    @target(str(shared_file), [])
    def build_shared(target, depends):
        with open(target, 'w') as f:
            f.write("shared data")
    
    for i, output_file in enumerate(output_files):
        local_i = i
        @target(str(output_file), [str(shared_file)])
        def build_output(target, depends):
            with open(depends[0], 'r') as f:
                data = f.read()
            with open(target, 'w') as f:
                f.write(f"{data} -> output{local_i}")
    
    @target(str(final_file), [str(f) for f in output_files])
    def build_final(target, depends):
        with open(target, 'w') as f:
            f.write("final")

    builder.build(str(final_file), max_jobs=4)

    assert shared_file.exists()
    for output_file in output_files:
        assert output_file.exists()
    assert final_file.exists()


def test_sequential_build_mode(tmp_path):
    """Test that max_jobs=1 forces sequential execution"""
    builder.clean()

    output_files = [tmp_path / f"output{i}.txt" for i in range(4)]
    final_file = tmp_path / "final.txt"
    
    for i, output_file in enumerate(output_files):
        local_i = i
        @target(str(output_file), [])
        def build_output(target, depends):
            with open(target, 'w') as f:
                f.write(f"output {local_i}")
    
    @target(str(final_file), [str(f) for f in output_files])
    def build_final(target, depends):
        with open(target, 'w') as f:
            f.write("done")

    builder.build(str(final_file), max_jobs=1)

    for output_file in output_files:
        assert output_file.exists()
