import sqlglot
import logging

logger = logging.getLogger("sp-converter")

class SPConverter:
    def convert(self, proc_name: str, sybase_definition: list) -> str:
        try:
            # Combine the stored procedure lines into a single string for processing
            full_definition = "\n".join([row[0] for row in sybase_definition])

            # Log the stored procedure definition before transpiling
            logger.debug(f"Converting stored procedure {proc_name} with definition:\n{full_definition}")
            
            # Transpile the T-SQL to PostgreSQL syntax
            translated = sqlglot.transpile(
                full_definition,
                read="tsql",
                write="postgres",
                pretty=True
            )[0]
            
            # Log the transpiled SQL before wrapping
            logger.debug(f"Transpiled PostgreSQL function for {proc_name}:\n{translated}")
            
            # Return the wrapped function
            return self._wrap_as_function(proc_name, translated)
        except sqlglot.errors.SqlGlotError as e:
            logger.error(f"SQLGlot transpiling error for stored procedure {proc_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"SP conversion failed for {proc_name}: {str(e)}")
            raise

    def _wrap_as_function(self, name: str, body: str) -> str:
        """Wrap the converted body into a PostgreSQL function definition."""
        try:
            function_definition = f"""
            CREATE OR REPLACE FUNCTION {name}()
            RETURNS VOID
            LANGUAGE plpgsql
            AS $$
            BEGIN
                {body}
            END;
            $$;
            """
            logger.info(f"Successfully wrapped stored procedure {name} into PostgreSQL function")
            return function_definition
        except Exception as e:
            logger.error(f"Error wrapping stored procedure {name} into PostgreSQL function: {str(e)}")
            raise
