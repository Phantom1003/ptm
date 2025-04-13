# Phantom Make (PTM)

A Python-based traceable make system that provides enhanced build automation capabilities with improved traceability and programmability.
It's designed to help developers maintain complex multi-configuration build processes while ensuring reliable and reproducible builds.

## Features

- Python-based syntax
- Enhanced build traceability
- Programmable parameter system

## Installation

```bash
pip install phantom-make
```

## Requirements

- Python 3.10 or higher

## Usage

### Syntax Sugar Features

PTM provides powerful syntax sugar to make build scripts more concise and readable:

1. **Shell Command Execution**
   ```python
   # Traditional Python
   exec("gcc -o main main.c")
   
   # PTM Syntax Sugar
   $"gcc -o main main.c"
   
   # Capture stdout
   output = $>"ls -l"
   
   # Capture stderr
   error = $>>"gcc -v"
   
   # Capture both stdout and stderr
   result = $&"make"
   ```

2. **Environment Variables**
   ```python
   # Traditional Python
   os.environ["PATH"]
   
   # PTM Syntax Sugar
   ${PATH}
   
   # In f-strings
   path = f"Current path: ${PATH}"
   ```

3. **String Division for Paths**
   ```python
   # Traditional Python
   os.path.join("src", "main", "file.c")
   
   # PTM Syntax Sugar
   "src" / "main" / "file.c"
   ```

### Basic Usage

PTM provides a Python-based interface for defining build rules and dependencies. Here's a basic example:

1. **File Targets**
   ```python
   from ptm import target
   
   @target("output.txt", ["input.txt"])
   def build_output(target, deps):
       with open(deps[0], 'r') as f:
           data = f.read()
       with open(target, 'w') as f:
           f.write(data.upper())
   ```

2. **Multiple Targets**
   ```python
   from ptm import targets
   
   @targets(["output1.txt", "output2.txt"], ["input.txt"])
   def build_outputs(target, deps):
       with open(deps[0], 'r') as f:
           data = f.read()
       with open(target, 'w') as f:
           f.write(data.upper())
   ```

3. **Task Targets**
   ```python
   from ptm import task
   
   @task()
   def setup_environment(target, deps):
       print("Setting up environment...")
   
   @task([setup_environment])
   def build_project(target, deps):
       print("Building project...")
   ```

4. **Mixed Dependencies**
   ```python
   from ptm import target, task
   
   @task()
   def prepare_data(target, deps):
       print("Preparing data...")
   
   @target("output.txt", [prepare_data, "input.txt"])
   def build_output(target, deps):
       print("Building output...")
   ```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
