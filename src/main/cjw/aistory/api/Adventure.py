from fastapi import APIRouter


class Adventure:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route("/adventure/persona", self.setPersona, methods=["GET"])

    async def setPersona(self):
        print("here")
        return {"message": "Set persona"}
