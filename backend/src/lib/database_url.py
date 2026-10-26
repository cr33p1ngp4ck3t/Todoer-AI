from sqlalchemy.engine import make_url


def use_installed_postgres_driver(database_url):
    url = make_url(database_url)
    # SQLAlchemy 2.1 defaults to psycopg, while our lockfile installs psycopg2.
    if url.drivername == "postgresql":
        return url.set(drivername="postgresql+psycopg2")
    return url
