# import time
# from unittest import mock

# import pytest
# from click.testing import CliRunner

# from bonfo.cli import cli


# @pytest.mark.parametrize("use_mock, min_time, max_time", ((True, 2.5, 3.5), (False, 1.0, 2.0)))
# def xtest_async_cli(use_mock, min_time, max_time):
#     def test_hook(delay):
#         return AsyncContext(delay + 0.5)

#     runner = CliRunner()
#     start = time.time()
#     if use_mock:
#         with mock.patch("test_code.TestAsyncContext", test_hook):
#             result = runner.invoke(cli)
#     else:
#         result = runner.invoke(cli)
#     stop = time.time()
#     assert result.exit_code == 0
#     assert result.stdout == "hello\n"
#     assert min_time < stop - start < max_time
