"""Alembic environment. Migrations are plain SQL (see versions/*.sql), run as the owner role."""

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
url = config.get_main_option("sqlalchemy.url")
if not url:
    from driplytics_api.db.migrate import to_sqlalchemy_url
    from driplytics_api.settings import get_settings

    url = to_sqlalchemy_url(get_settings().migration_database_url)


def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
