def test_package_imports():
    import quark
    from quark import config

    assert config.ANN_FACTOR == 252
    assert config.PURGE_DAYS >= config.TARGET_HORIZON
