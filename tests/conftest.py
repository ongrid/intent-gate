# pylint: disable=missing-module-docstring,missing-function-docstring,unused-argument
import warnings


def pytest_configure(config):
    # See: https://github.com/ethereum/web3.py/issues/3713
    # Related: https://github.com/ethereum/web3.py/issues/3679
    # Related: https://github.com/ethereum/web3.py/issues/3530
    warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"websockets\.legacy")
