from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.exc import JWTError
from server.routes.accounts.route import route as account_router
from server.routes.auth.route import route as auth_router
from server.routes.backtests.route import route as backtests_router
from server.routes.deployments.route import route as deployment_router
from server.routes.strategy import strategies_router, versions_router


app = FastAPI(title="Strategy Builder API", version="0.0.0")

app.include_router(account_router)
app.include_router(auth_router)
app.include_router(backtests_router)
app.include_router(deployment_router)
strategies_router.include_router(versions_router)
app.include_router(strategies_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(req: Request, e: RequestValidationError):
    if e.errors():
        content = {"error": e.errors()[0]["msg"]}
    else:
        content = {"msg": "Unknown error."}
    return JSONResponse(status_code=400, content=content)


@app.exception_handler(JWTError)
async def http_exception_handler(req: Request, exc: JWTError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(HTTPException)
async def http_exception_handler(req: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
