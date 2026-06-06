import re
import httpx
from fastapi import HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM

PUBLIC_URL_PATTERNS = [
    (r"^/auth/login$", ["POST"]),
    (r"^/auth/register$", ["POST"]),
    
    # /auctions , /auctions/{id}
    (r"^/auctions(/.*)?$", ["GET"]),
    
    # /bids/{id}
    (r"^/bids/[^/]+$", ["GET"]),
    
    (r"^/docs(/.*)?$", ["GET"]),
    (r"^/openapi\.json$", ["GET"]),
]

def verify_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        return HTTPException(status_code=401, detail="Expired token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
def is_public_endpoint(path: str, method: str) -> bool:
    return any(
        re.match(pattern, path) and method.upper() in methods
        for pattern, methods in PUBLIC_URL_PATTERNS
    )

async def fetch_schema(client, name, url):
    try:
        res = await client.get(f"{url}/openapi.json")
        return name, res.json()
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return name, {}
    
    
async def forward_request(service_url: str, path: str, method: str, body=None, headers=None):
    async with httpx.AsyncClient() as client:
        url = f"{service_url}/{path}"
        print(url)
        response = await client.request(method, url, content=body, headers=headers)
        return response