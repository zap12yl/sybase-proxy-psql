import sqlglot
import logging

logger = logging.getLogger("sp-converter")

class SPConverter:
    def convert(self, proc_name: str, sybase_definition: list) -> str:
        try:
            full_definition = "\n".join([row[0] for row in sybase_definition])
            translated = sqlglot.transpile(
                full_definition,
                read="tsql",
                write="postgres",
                pretty=True
            )[0]
            
            return self._wrap_as_function(proc_name, translated)
        except Exception as e:
            logger.error(f"SP conversion failed for {proc_name}: {str(e)}")
            raise

    def _wrap_as_function(self, name: str, body: str) -> str:
        return f"""
        CREATE OR REPLACE FUNCTION {name}()
        RETURNS VOID
        LANGUAGE plpgsql
        AS $$
        BEGIN
            {body}
        END;
        $$;
        """