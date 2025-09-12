from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.exc import JWTError
from server.routes.accounts.route import route as account_router
from server.routes.auth.route import route as auth_router
from server.routes.deployments.route import route as deployment_router
from server.routes.strategy.route import route as strategy_router


app = FastAPI(title="Strategy Builder API", version="0.0.0")

app.include_router(account_router)
app.include_router(auth_router)
app.include_router(deployment_router)
app.include_router(strategy_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.exception_handler(JWTError)
async def http_exception_handler(request: Request, exc: JWTError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
