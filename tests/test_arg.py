from ptm import ArgList

def test_arg_string_default_separator():
    arg = ArgList("alpha", "beta", "gamma")
    assert str(arg) == "alpha beta gamma"

def test_arg_join_with_custom_separator():
    arg = ArgList("core", "dut", "config")
    assert arg.concat(".") == "core.dut.config"
    assert arg.concat("-") == "core-dut-config"

def test_arg_accepts_iterable_input():
    parts = ["one", "two", "three"]
    arg = ArgList(parts)
    assert str(arg) == "one two three"
    assert arg.concat(",") == "one,two,three"

def test_arg_string_inline():
    arg = ArgList("phantom", "make").concat("-")
    assert arg == "phantom-make"

def test_arg_add_preserves_type():
    include = ArgList(["+incdir+a", "+incdir+b"])
    flags = ArgList(["+base"]) + include
    assert isinstance(flags, ArgList)
    flags.extend(["-quiet"])
    flags += ["-full64"]
    assert str(flags) == "+base +incdir+a +incdir+b -quiet -full64"

def test_extend_with_string_treats_as_single_token():
    args = ArgList("foo")
    args.extend("bar")
    assert str(args) == "foo bar"
