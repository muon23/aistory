import unittest
from asyncio import sleep

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


class ServerTest(unittest.TestCase):

    def test_basic(self):
        app = FastAPI()

        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        sleep(300)

        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
