from config import ENABLE_FASTAPI


if ENABLE_FASTAPI:

    import uvicorn

    from api import app

    if __name__ == "__main__":

        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )

else:

    from cli import run_cli

    if __name__ == "__main__":

        run_cli()