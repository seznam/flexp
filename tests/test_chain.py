from __future__ import print_function

import unittest

from flexp.flow import Chain
from .utils import Add, RequiresNonsense, Result, Mult


class TestChain(unittest.TestCase):
    def test_chain(self):
        data = {"input": 10}
        c = Chain([
            Add(13),
        ])
        c.process(data)
        c.close()

        self.assertEqual(data, {"input": 10, "output": 23})
        assert str(c) == "Chain[Add]"
        c.add(Mult(2))
        assert str(c) == "Chain[Add-Mult]"
        c.process(data)
        self.assertEqual(data, {"input": 10, "output": 20})

    def test_chain_names(self):
        assert str(Chain()) == "Chain[]"
        assert str(Chain(name="ML-pipeline")) == "ML-pipeline[]"

    def test_chain_from_object(self):
        data = {"input": 10}
        c = Chain(Add(13))
        c.process(data)
        self.assertEqual(data, {"input": 10, "output": 23})
        assert str(c) == "Chain[Add]"

    def test_chain_from_fuction(self):
        data = {"input": 10}

        def add(x):
            x["output"] = x["input"] + 13

        c = Chain(add)
        c.process(data)
        self.assertEqual(data, {"input": 10, "output": 23})
        assert str(c) == "Chain[add]"

    def test_with(self):
        c = Chain([
            Add(13),
        ])
        data = {"input": 10}
        with c:
            c.process(data)
        assert data == {"input": 10, "output": 23}

    def test_time(self):
        data = {"input": 10}
        c = Chain([
            Add(13),
        ])
        c.process(data)
        c.close()
        assert len(c.times) == 1
        assert c.iterations == 1
        c.process(data)
        assert c.iterations == 2

    def test_chain_requires(self):
        self.assertRaises(KeyError,
                          lambda: Chain([
                              Add(13),
                              RequiresNonsense()
                          ], check=True))

    def test_chain_requires_first(self):
        self.assertRaises(KeyError,
                          lambda: Chain([
                              Add(13),
                          ],
                              check=True,
                              ignore_first_module_requirements=False))

    def test_chain_inherits_provides_requires(self):
        data = {"input": 20}
        Chain([
            Chain([
                Add(10)
            ], check=True),
            Result()], check=True).process(data)
        assert data["output"] == 30


