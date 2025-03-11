import os
from fastapi import APIRouter
from proxy.src.sybase_converter import SybaseConverter

router = APIRouter()
converter = SybaseConverter()

@router.post("/convert")
async def convert_sql(request: dict):
    try:
        converted = converter.convert(request["sql"])
        return {
            "converted": converted,
            "warnings": get_conversion_warnings(request["sql"])
        }
    except Exception as e:
        return {"error": str(e)}

def get_conversion_warnings(sql: str) -> list:
    warnings = []
    if "RAISERROR" in sql.upper():
        warnings.append("RAISERROR converted to RAISE EXCEPTION - verify error codes")
    if "DECLARE" in sql.upper() and "CURSOR" in sql.upper():
        warnings.append("Cursor usage detected - verify transaction boundaries")
    if "XML" in sql.upper():
        warnings.append("XML functions converted - may require additional extensions")
    return warnings