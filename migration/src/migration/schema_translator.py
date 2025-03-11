import sqlglot
import logging

logger = logging.getLogger("schema-translator")

class SchemaTranslator:
    TYPE_MAP = {
        'int': 'integer',
        'varchar': 'text',
        'datetime': 'timestamp',
        'decimal': 'numeric',
        'money': 'numeric(19,4)',
        'text': 'text',
        'image': 'bytea',
        'bit': 'boolean'
    }

    def convert_schema(self, table_name: str, sybase_schema: list) -> str:
        try:
            columns = []
            for col in sybase_schema:
                col_name = col['Column_name']
                col_type = self._map_type(col['Type'])
                nullable = 'NOT NULL' if col['Nullable'] == 'NO' else ''
                default = f"DEFAULT {col['Default']}" if col['Default'] else ''
                
                column_def = f"{col_name} {col_type} {nullable} {default}".strip()
                columns.append(column_def)
            
            pk = self._extract_primary_key(sybase_schema)
            return self._build_create_table(table_name, columns, pk)
        except Exception as e:
            logger.error(f"Schema conversion failed: {str(e)}")
            raise

    def _map_type(self, sybase_type: str) -> str:
        return self.TYPE_MAP.get(sybase_type.lower(), 'text')

    def _extract_primary_key(self, schema: list) -> str:
        pk_cols = [col['Column_name'] for col in schema if col['Key'] == 1]
        return f"PRIMARY KEY ({', '.join(pk_cols)})" if pk_cols else ""

    def _build_create_table(self, name: str, columns: list, pk: str) -> str:
        ddl = f"CREATE TABLE IF NOT EXISTS {name} (\n  "
        ddl += ",\n  ".join(columns)
        if pk:
            ddl += f",\n  {pk}"
        ddl += "\n);"
        return ddl