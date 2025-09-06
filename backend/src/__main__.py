import uvicorn


def main():
    uvicorn.run("server.app:app", port=80, host='localhost', reload=True)


if __name__ == "__main__":
    main()