import uvicorn
from fastapi import FastAPI, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from cjw.aistory.api.Adventure import Adventure

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


def get_x():
    return 10


app = FastAPI()
router = InferringRouter()  # Step 1: Create a router


@cbv(router)  # Step 2: Create and decorate a class to hold the endpoints
class Foo:
    # Step 3: Add dependencies as class attributes
    x: int = Depends(get_x)

    @router.get("/somewhere")
    def bar(self) -> int:
        # Step 4: Use `self.<dependency_name>` to access shared dependencies
        return self.x


app.include_router(router)

if __name__ == '__main__':
    adventure = Adventure()
    uvicorn.run(app, host="0.0.0.0", port=8000)
