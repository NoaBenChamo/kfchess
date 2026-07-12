from texttests.script_parser import ScriptParser



def test_parse_click():

    lines = [
        "click 50 100"
    ]


    result = ScriptParser.parse(lines)


    assert result == [
        (
            "click",
            50,
            100
        )
    ]



def test_parse_multiple_commands():

    lines = [
        "click 50 50",
        "wait 1000",
        "print"
    ]


    result = ScriptParser.parse(lines)


    assert result == [
        (
            "click",
            50,
            50
        ),
        (
            "wait",
            1000
        ),
        (
            "print",
        )
    ]