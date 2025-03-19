from setuptools import setup, find_packages

setup(
    name="db_migration",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "psycopg2-binary>=2.9.10",
        "python_tds>=1.16.0",
        "sqlglot>=26.11.1",
        "python-dotenv>=1.0.1",
        "migrator>=0.0.8", 
        "sqlalchemy>=2.0.39",
        "typing-extensions>=4.12.2"
    ],
    python_requires=">=3.13",
)
