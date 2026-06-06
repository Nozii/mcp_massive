import os
from dotenv import load_dotenv

from . import configure_credentials, run


def main():
    load_dotenv()

    configure_credentials(
        api_key=os.environ.get("MASSIVE_API_KEY", ""),
        base_url=os.environ.get(
            "MASSIVE_API_BASE_URL",
            "https://api.massive.com",
        ).rstrip("/"),
        llms_txt_url=os.environ.get("MASSIVE_LLMS_TXT_URL"),
        max_tables=(
            int(os.environ["MASSIVE_MAX_TABLES"])
            if os.environ.get("MASSIVE_MAX_TABLES")
            else None
        ),
        max_rows=(
            int(os.environ["MASSIVE_MAX_ROWS"])
            if os.environ.get("MASSIVE_MAX_ROWS")
            else None
        ),
    )

    run("streamable-http")


if __name__ == "__main__":
    main()
