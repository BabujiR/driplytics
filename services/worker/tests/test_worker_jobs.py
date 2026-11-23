from driplytics_worker import main


async def test_ping_returns_pong() -> None:
    assert await main.ping({}) == "pong"


async def test_ping_echoes_message() -> None:
    assert await main.ping({}, "hello") == "hello"


def test_worker_settings_registers_ping() -> None:
    assert main.ping in main.WorkerSettings.functions
    assert main.WorkerSettings.health_check_interval > 0


def test_engine_is_importable_from_worker() -> None:
    assert main.engine_version()
