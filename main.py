from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import socket

# Intentar importar pyodbc y fallar con explicación clara
try:
    import pyodbc
    PYODBC_OK = True
except Exception as e:
    pyodbc = None
    PYODBC_OK = False
    PYODBC_IMPORT_ERROR = str(e)

app = FastAPI(title="Railway + FastAPI + pyodbc demo")

# --- Utilidades de diagnóstico ---
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/diag/pyodbc")
def diag_pyodbc():
    if not PYODBC_OK:
        return {
            "pyodbc_imported": False,
            "error": PYODBC_IMPORT_ERROR
        }
    return {
        "pyodbc_imported": True,
        "pyodbc_version": getattr(pyodbc, "__version__", "unknown")
    }

@app.get("/diag/test-connection")
def test_connection(host: str, port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, port))
        return {"success": True, "message": f"Conexión exitosa a {host}:{port}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        s.close()

# --- Conexión a SQL Server ---

def get_connection_string() -> str:
    # Ajusta estas variables o usa variables de entorno reales
    server_sql   = '64.250.122.114,1450'  # IP pública, coma para puerto
    database_sql = 'PROSHOP-TEST'
    username_sql = 'sa'
    password_sql = 'P4ssw0rd'
    # Driver 18 instalado por Dockerfile. TrustServerCertificate para entornos sin CA pública.
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server_sql};DATABASE={database_sql};"
        f"UID={username_sql};PWD={password_sql};"
        "Encrypt=yes;TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )

def connect_db():
    if pyodbc is None:
        raise HTTPException(status_code=500, detail="pyodbc no está disponible en este entorno (falta driver ODBC en la imagen).")
    conn_str = get_connection_string()
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a SQL Server: {e}")

@app.get("/facturas")
def get_facturas(fecha: str = Query(..., description="YYYY-MM-DD")):
    query = "SELECT TOP 5 DocNum, DocDate, CardCode, CardName, DocTotal FROM OINV WHERE DocDate >= ? ORDER BY DocDate DESC"
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(query, (fecha,))
        rows = cur.fetchall()
        facturas = [{
            "DocNum": row.DocNum,
            "DocDate": row.DocDate.strftime("%Y-%m-%d") if row.DocDate else None,
            "CardCode": row.CardCode,
            "CardName": row.CardName,
            "DocTotal": float(row.DocTotal)
        } for row in rows]
        return {"success": True, "facturas": facturas}
    finally:
        try:
            cur.close()
        except:
            pass
        conn.close()

@app.get("/api/inventoryItems/{itemId}")
def get_inventory_item(itemId: str):
    conn = connect_db()
    try:
        cur = conn.cursor()
        query = '''
            SELECT 
                T0.ItemCode, 
                T0.ItemName,
                1 AS Cant, 
                CEILING (T1.Price * 1.16) AS partUnitPrice,  
                T0.OnHand AS Stock, 
                '' AS laborHours,
                '' AS laborHourPrice,
                0 AS discount,
                'Prueba' AS comments
            FROM OITM T0
            INNER JOIN ITM1 T1 ON T0.ItemCode = T1.ItemCode
            WHERE T1.PriceList = '1' AND T0.ItemCode = ?
        '''
        cur.execute(query, (itemId,))
        row = cur.fetchone()
        if not row:
            return {"success": False, "message": f"Item {itemId} no encontrado", "data": None}

        part = {
            "partName": row.ItemName,
            "partId": row.ItemCode,
            "quantity": int(row.Cant),
            "partUnitPrice": float(row.partUnitPrice),
            "availability": int(row.Stock),
            "laborHours": None,
            "laborHourPrice": None,
            "discount": float(row.discount) if hasattr(row, "discount") else 0,
            "comments": [str(row.comments) if hasattr(row, "comments") else ""]
        }
        labor = {
            "laborName": "Mantenimiento Preventivo",
            "laborId": "MantPrev",
            "laborHours": 1,
            "labourHourPrice": 1,
            "discount": None,
            "comments": None
        }
        return {
            "success": True,
            "message": None,
            "data": {"jobName": "Mantenimiento Preventivo", "jobId": "MantPrev", "parts": [part], "labors": [labor]}
        }
    finally:
        try:
            cur.close()
        except:
            pass
        conn.close()
