import os

from sqlalchemy import (
    create_engine
)

from sqlalchemy.orm import (
    sessionmaker,
    declarative_base
)

from dotenv import (
    load_dotenv
)


load_dotenv()


# ==================================================
# DATABASE
# ==================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./ingrelens.db"
)


if DATABASE_URL.startswith(
    "postgres://"
):

    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


connect_args = {}


if DATABASE_URL.startswith(
    "sqlite"
):

    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(

    DATABASE_URL,

    connect_args=connect_args,

    pool_pre_ping=True

)


SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine

)


Base = declarative_base()


# ==================================================
# SUPABASE
# ==================================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


supabase_client = None


if SUPABASE_URL and SUPABASE_KEY:

    try:

        from supabase import (
            create_client
        )

        supabase_client = create_client(

            SUPABASE_URL,

            SUPABASE_KEY

        )

    except Exception as e:

        print(
            "Failed to initialize "
            f"Supabase client: {e}"
        )


def get_supabase():

    return supabase_client