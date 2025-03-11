import sqlglot

class QueryHandler:
    def __init__(self):
        self.type_mappings = {
            'datetime': 'timestamp',
            'varchar': 'text',
            'money': 'numeric(19,4)'
        }

    def translate(self, query: str) -> str:
        try:
            return sqlglot.transpile(
                query, 
                read="tsql", 
                write="postgres",
                identify=True,
                mapping=self.type_mappings
            )[0]
        except Exception as e:
            raise ValueError(f"Translation error: {str(e)}")
