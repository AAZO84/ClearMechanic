from fastapi import FastAPI, Query, HTTPException
try:
    import pyodbc
except ImportError as e:
    pyodbc = None
    print("Error al importar pyodbc:", e)
import os
import httpx


app = FastAPI()

# Conexion a SQL Sever
def get_db_connection():
    if pyodbc is None:
       raise RuntimeError("pyodbc no está disponible en este entorno")

    server_sql = 'tcp:10.122.114.21'
    database_sql = 'PROSHOP-TEST'
    username_sql = 'sa'
    password_sql = 'P4ssw0rd'

    conexionbd = (
        f'DRIVER=ODBC Driver 18 for SQL Server;'
        f'SERVER={server_sql};DATABASE={database_sql};'
        f'UID={username_sql};PWD={password_sql};'
        'TrustServerCertificate=yes;'
      )
    return conexionbd 
    #cursor = conexion.cursor()
#conexion = get_db_connection()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/users/{cat}")
async def get_users(id,cat):
    return {"id": id, "cat": cat}

@app.get("/facturas")
def get_facturas(fecha: str = Query(..., description="Fecha de las facturas en formato YYYY-MM-DD")):

    query = """SELECT DocNum, DocDate, CardCode, CardName, DocTotal FROM OINV WHERE DocDate >= ?"""
    conexion = pyodbc.connect(get_db_connection())
    cursor = conexion.cursor()
    cursor.execute(query, fecha)
    resultado = cursor.fetchall()
    
    facturas = [
        {
            "DocNum": row.DocNum,
            "DocDate": row.DocDate.strftime("%Y-%m-%d"),
            "CardCode": row.CardCode,
            "CardName": row.CardName,
            "DocTotal": float(row.DocTotal)
        }
        for row in resultado
      ]
    cursor.close()
    conexion.close() 
    return {"facturas": facturas}

# Obtener detalles de un artículo de inventario por su código ClearMechanic

@app.get("/api/inventoryItems/{itemId}")
def get_inventory_item(itemId: str):
    conexion = None
    cursor = None
    try:
        conexion = pyodbc.connect(get_db_connection())
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

        # Si no hay resultado, devolvemos success=false con data=null
        if not row:
            return {
                "success": False,
                "message": f"Item {itemId} no encontrado",
                "data": None
            }

        # --------- ARMAR PARTS A PARTIR DEL QUERY ---------
        part = {
            "partName": row.ItemName,                
            "partId": row.ItemCode,                  
            "quantity": int(row.Cant),                
            "partUnitPrice": float(row.partUnitPrice),
            "availability": int(row.Stock),           
            "laborHours": None,
            "laborHourPrice": None,
            "discount": float(row.discount) if hasattr(row, "discount") else 0,
            "comments": [
                str(row.comments) if hasattr(row, "comments") else ""
            ]
        }

        # --------- ARMAR LABORS ---------
        labor = {
            "laborName": "Mantenimiento Preventivo",
            "laborId": "MantPrev",
            "laborHours": 1,
            "labourHourPrice": 1,  
            "discount": None,
            "comments": None
        }

        # --------- RESPUESTA FINAL CON LA ESTRUCTURA QUE QUIERES ---------
        response = {
            "success": True,
            "message": None,
            "data": {
                "jobName": "Mantenimiento Preventivo",  
                "jobId": "MantPrev",              
                "parts": [part],
                "labors": [labor]
            }
        }

        return response

    except Exception as e:
        # Si algo truena, mandamos 500 con el detalle del error
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@app.get("/my-egress-ip")
async def my_egress_ip():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.ipify.org?format=json")
        return r.json()

      