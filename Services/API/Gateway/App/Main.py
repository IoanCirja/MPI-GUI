from fastapi import FastAPI, HTTPException
import httpx
from starlette.requests import Request

app = FastAPI()




app = FastAPI()

AUTH_SERVICE_URL = "http://localhost:8000/api"
JOB_SERVICE_URL = "http://localhost:8001/api"

client = httpx.AsyncClient(follow_redirects=True)


@app.post("/auth")
async def proxy_auth_post_service(request: Request):

    url = f"http://localhost:8000/api/login"

    try:

        response = await client.request(
            method=request.method,
            url=url,  # Ensure the URL is correct
            headers=request.headers.raw,
            data=await request.body()
        )

        if response.content:
            return response.json()

        return {"message": "No content returned from AuthService"}

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error in communication with Auth service: {str(e)}")


@app.get("/job/{path:path}")
async def proxy_job_service(path: str, request: Request):

    url = f"{JOB_SERVICE_URL}/{path}"
    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            data=await request.body()
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Job service unavailable")

@app.post("/job/{path:path}")
async def proxy_job_post_service(path: str, request: Request):

    url = f"{JOB_SERVICE_URL}/{path}"
    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            data=await request.body()
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Job service unavailable")

