import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from app.config import SERVICES
from app.dependencies import verify_jwt, is_public_endpoint, fetch_schema, forward_request

RESERVED = {"docs", "openapi.json", "redoc"}

app = FastAPI(
    title="Gateway Service",
    openapi_url=None,
    docs_url=None,
    redoc_url=None
)

merged_openapi = {}

def _rewrite_refs(obj, ref_map):
    """Recursively rewrite $ref values in an OpenAPI structure."""
    if isinstance(obj, dict):
        if "$ref" in obj and obj["$ref"] in ref_map:
            obj["$ref"] = ref_map[obj["$ref"]]
        return {k: _rewrite_refs(v, ref_map) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_rewrite_refs(item, ref_map) for item in obj]
    return obj

@app.on_event("startup")
async def build_openapi():
    global merged_openapi

    paths = {}
    components = {
        "schemas": {},
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    }

    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_schema(client, name, url)
            for name, url in SERVICES.items()
        ]
        results = await asyncio.gather(*tasks)

    
    for service_name, schema in results: # type: ignore[reportGeneralTypeIssues]
        if not schema:
            continue

        # Build a mapping of original $ref → prefixed $ref for this service
        schema_names = list(schema.get("components", {}).get("schemas", {}).keys())
        ref_map = {
            f"#/components/schemas/{name}": f"#/components/schemas/{service_name}_{name}"
            for name in schema_names
        }

        for path, methods in schema.get("paths", {}).items():
            new_path = f"/{service_name}{path}"

            new_methods = {}

            # Carry over path-level parameters (e.g. shared {id} param)
            if "parameters" in methods:
                new_methods["parameters"] = _rewrite_refs(methods["parameters"], ref_map)

            for method, details in methods.items():
                if method == "parameters":
                    continue  # already handled above

                # Tag by service for Swagger grouping
                details["tags"] = [service_name]

                # Unique operationId to avoid collisions across services
                op_id_suffix = path.strip("/").replace("/", "_").replace("{", "").replace("}", "") or "root"
                details["operationId"] = f"{service_name}_{method}_{op_id_suffix}"

                # /{service_name}/path eg. /auth/login
                path = f"/{service_name}{path}"
                
                if is_public_endpoint(path, method):
                    details["security"] = []
                else:
                    details["security"] = [{"BearerAuth": []}]
                
                new_methods[method] = _rewrite_refs(details, ref_map)

            paths[new_path] = new_methods

        # Merge component schemas, prefixing names to avoid collisions
        for schema_name, schema_def in schema.get("components", {}).get("schemas", {}).items():
            prefixed = f"{service_name}_{schema_name}"
            components["schemas"][prefixed] = _rewrite_refs(schema_def, ref_map)

    merged_openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "API Gateway (Aggregated Docs)",
            "version": "1.0.0",
        },
        "paths": paths,
        "components": components,
    }
    
@app.get("/openapi.json", include_in_schema=False)
def openapi():
    return JSONResponse(merged_openapi)

@app.get("/docs", include_in_schema=False)
def docs():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Gateway Docs</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({ url: "/openapi.json", dom_id: '#swagger-ui' })
        </script>
    </body>
    </html>
    """)

@app.api_route(
    "/{service}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def gateway_root(service: str, request: Request):
    if service in RESERVED:
        raise HTTPException(status_code=404, detail="Not found")
    return await gateway(service, "", request)

@app.api_route(
    '/{service}/{path:path}', 
    methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
)
async def gateway(service: str, path: str, request: Request):
    if service in RESERVED:
        raise HTTPException(status_code=404, detail="Not found")
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail='Service not found')
    
    full_path = f"/{service}/{path}".rstrip("/") if path else f"/{service}"
    requires_auth = not is_public_endpoint(full_path, request.method)
    
    user = None
    
    if requires_auth:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise HTTPException(status_code=401, detail='Missing token')
        
        token = auth_header.replace('Bearer ', '')
        user = verify_jwt(token)
        
    body = await request.body()
    headers = dict(request.headers)
    
    headers.pop("host", None)
    
    if user:
        headers['X-User-Id'] = str(user.get("sub"))
        headers['X-User-Role'] = str(user.get("role"))
        
    response = await forward_request(
                    service_url=SERVICES[service], 
                    path=path, 
                    method=request.method,
                    body=body,
                    headers=headers
                )
    
    try:
        data = response.json()
    except Exception:
        data = response.text
        
    return JSONResponse(
        status_code=response.status_code,
        content=data,
        headers=response.headers
    )

@app.get('/')
async def root():
    return {'message': 'Hello World'}   
