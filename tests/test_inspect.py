import unittest

from testfixtures import LogCapture


from flexp.flow import Chain
from flexp.flow import inspector
from .utils import Add, DummyModule


class TestChain(unittest.TestCase):
    def test_chain_inspect(self):
        data = {"input": 20}
        with LogCapture() as l:
            c = Chain([
                inspector.inspect(Add(10), stream=True)])
            c.process(data)
            c.close()
            l.check(
                ('flexp.flow.flow', 'DEBUG', 'Add.process()'),
                ('flexp.flow.inspector', 'INFO', 'Data flow structure'),
                ('flexp.flow.inspector', 'INFO', "{'input': 20, 'output': 30}"),
                ('flexp.flow.inspector', 'INFO', 'End of data flow structure'),
                ('flexp.flow.flow', 'INFO', 'Add average execution time 0.00 sec')
            )

    def test_chain_inspect_deep(self):
        data = {"input": {i: i for i in range(11)}}
        with LogCapture() as l:
            c = Chain([
                inspector.inspect(DummyModule(), stream=True)])
            c.process(data)
            c.close()
            l.check(
                ('flexp.flow.flow', 'DEBUG', 'DummyModule.process()'),
                ('flexp.flow.inspector', 'INFO', 'Data flow structure'),
                ('flexp.flow.inspector', 'INFO', "{\'input\': {\"<class \'int\'>#11 times (0)\": 0}}"),
                ('flexp.flow.inspector', 'INFO', 'End of data flow structure'),
                ('flexp.flow.flow', 'INFO', 'DummyModule average execution time 0.00 sec')
            )
