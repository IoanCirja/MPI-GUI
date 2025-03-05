import httpx
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


async def forward_request(request: Request, target_url: str):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        method = request.method

        try:
            response = await client.request(
                method, target_url, content=body, headers=headers
            )

            return JSONResponse(content=response.json(), status_code=response.status_code)

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with service: {str(e)}")
