import types
import pytest


def test_top_level_index_exports_presence():
    import qdb

    # Presence at module level
    assert hasattr(qdb, "get_index_data")
    assert hasattr(qdb, "get_index_realtime")
    assert hasattr(qdb, "get_index_list")


@pytest.mark.skip(reason="Requires pandas/akshare environment; presence is sufficient for unit scope")
def test_index_calls_noop_import_only():
    # This is a placeholder to be extended in integration tests with dependencies installed
    import qdb
    funcs = [qdb.get_index_data, qdb.get_index_realtime, qdb.get_index_list]
    assert all(isinstance(f, (types.FunctionType, types.BuiltinFunctionType)) for f in funcs)

