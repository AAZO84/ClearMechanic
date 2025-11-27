from fastapi import FastAPI
import psycopg
import os




app = FastAPI(title="Clear Mechanic")

def connect_pg():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL no está configurada en Railway")
    return psycopg.connect(db_url)

@app.get("/api/inventoryItems/{itemId}")
def get_inventory_item(itemId: str):
    conn = connect_pg()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            itemcode,           -- 0
            itemname,           -- 1
            cant,               -- 2
            partunitprice,      -- 3
            stock,              -- 4
            laborhours,         -- 5
            laborhourprice,     -- 6
            discount,           -- 7
            comments            -- 8
        FROM inv_sap
        WHERE itemcode = %s
        LIMIT 1;
    """, (itemId,))
    row = cur.fetchone()
    cur.close(); conn.close()

    if not row:
        return {
            "success": False,
            "message": f"Item {itemId} no encontrado",
            "data": None
        }

    # EstructuraClearMechanic
    part = {
        "partName": row[1],
        "partId": row[0],
        "quantity": int(row[2]) if row[2] is not None else 1,
        "partUnitPrice": float(row[3]) if row[3] is not None else 0.0,
        "availability": int(row[4]) if row[4] is not None else 0,
        "laborHours": float(row[5]) if row[5] not in (None, "",) else None,
        "laborHourPrice": float(row[6]) if row[6] not in (None, "",) else None,
        "discount": float(row[7]) if row[7] is not None else 0.0,
        "comments": [str(row[8])] if row[8] not in (None, "",) else []
    }

    response = {
        "success": True,
        "message": None,
        "data": {
            "jobName": {row[1]},
            "jobId": {row[0]},   
            "parts": [part],
            "labors": []             
        }
    }
    return response
