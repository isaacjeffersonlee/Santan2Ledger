from setuptools import setup, find_packages

setup(
    name="santan2ledger",
    version="0.1",
    scripts=["santan2ledger/main.py"],
    entry_points={
        "console_scripts": [
            "s2l = santan2ledger:main",
        ],
    },
    packages=find_packages(),
)
