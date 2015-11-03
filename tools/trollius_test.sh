#!/bin/bash
cat zmq/tests/_test_asyncio.py | sed 's@yield from \(.*\)@yield From(\1)@g' > zmq/tests/_test_trollius.py
