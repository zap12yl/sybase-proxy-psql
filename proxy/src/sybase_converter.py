import sqlglot
from sqlglot import exp

class SybaseConverter:
    def convert(self, sql: str) -> str:
        return sqlglot.transpile(sql, read="tsql", write="postgres", transforms={
            self._convert_raiserror,
            self._convert_temp_tables,
            self._convert_cursors,
            self._convert_xml
        })[0]

    def _convert_raiserror(self, expression):
        if isinstance(expression, exp.RaiseError):
            return exp.Raise(
                level='EXCEPTION',
                message=expression.args.get("msg")
            )
        return expression

    def _convert_temp_tables(self, expression):
        if isinstance(expression, exp.Create) and expression.args["this"].name.startswith("#"):
            return expression.this.set("temporary", True)
        return expression

    def _convert_cursors(self, expression):
        if isinstance(expression, exp.DeclareCursor):
            return exp.Declare(
                cursor=expression.args["cursor"],
                query=expression.args["query"]
            )
        return expression

    def _convert_xml(self, expression):
        if "FOR XML" in expression.sql():
            return exp.Tag(
                this=exp.Identifier(this="XMLAGG"),
                expressions=[
                    exp.Tag(
                        this=exp.Identifier(this="XMLELEMENT"),
                        expressions=[
                            exp.Identifier(this="row"),
                            expression.args["expressions"]
                        ]
                    )
                ]
            )
        return expression