from fastapi import FastAPI, Query, HTTPException
import os, socket

try:
    import pyodbc
except ImportError as e:
    pyodbc = None
    print("Error al importar pyodbc:", e)

app = FastAPI()

def get_connection_string() -> str:
    server_sql   = '64.250.122.114,1430'   # IP pública, coma para puerto
    database_sql = 'PROSHOP-TEST'
    username_sql = 'sa'
    password_sql = 'P4ssw0rd'
    # Driver con LLAVES y TLS permitido
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server_sql};DATABASE={database_sql};"
        f"UID={username_sql};PWD={password_sql};"
        "TrustServerCertificate=yes;"
        # Si tu instancia requiere cifrado estricto quita TrustServerCertificate y usa Encrypt=yes con certificado válido
    )

def connect_db():
    if pyodbc is None:
        raise HTTPException(status_code=500, detail="pyodbc no está disponible en este entorno (falta driver ODBC en la imagen).")
    conn_str = get_connection_string()
    try:
        return pyodbc.connect(conn_str, timeout=5)
    except Exception as e:
        # Log claro para depurar cadena/firewall
        raise HTTPException(status_code=500, detail=f"Error conectando a SQL Server: {e}")

@app.get("/facturas")
def get_facturas(fecha: str = Query(..., description="YYYY-MM-DD")):
    query = "SELECT DocNum, DocDate, CardCode, CardName, DocTotal FROM OINV WHERE DocDate >= ?"
    conexion = connect_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(query, (fecha,))  # <- como tupla
        rows = cursor.fetchall()
        facturas = [{
            "DocNum": row.DocNum,
            "DocDate": row.DocDate.strftime("%Y-%m-%d"),
            "CardCode": row.CardCode,
            "CardName": row.CardName,
            "DocTotal": float(row.DocTotal)
        } for row in rows]
        return {"facturas": facturas}
    finally:
        cursor.close()
        conexion.close()

@app.get("/api/inventoryItems/{itemId}")
def get_inventory_item(itemId: str):
    conexion = connect_db()
    try:
        cursor = conexion.cursor()
        query = """
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
        """
        cursor.execute(query, (itemId,))
        row = cursor.fetchone()
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
        cursor.close()
        conexion.close()
