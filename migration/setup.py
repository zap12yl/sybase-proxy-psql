from setuptools import setup, find_packages

setup(
    name="db_migration",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "psycopg2-binary>=2.9.6",
        "python_tds>=1.16.0",
        "sqlglot>=10.6.2",
        "html.parser>=0.2",
        "python-dotenv>=0.19.2",
        "migrator>=0.0.8", 
        "sqlalchemy>=2.0.38",
        "typing-extensions>=4.12.2"
    ],
    python_requires=">=3.12",
)