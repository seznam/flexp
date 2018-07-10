class Add:
    requires = ["input"]
    provides = ["output"]

    def __init__(self, val):
        self.val = val

    def process(self, data):
        data["output"] = data["input"] + self.val


class Mult:
    requires = ["input"]
    provides = ["output"]

    def __init__(self, val):
        self.val = val

    def process(self, data):
        data["output"] = data["input"] * self.val


class Result:
    requires = ["output"]
    provides = []

    def process(self, data):
        assert "output" in data


class RequiresNonsense:
    requires = ["nonsense"]
    provides = ["nothing"]

    def process(self, data):
        pass


class DummyModule:
    requires = ["input"]
    provides = []

    def process(self, data):
        pass



