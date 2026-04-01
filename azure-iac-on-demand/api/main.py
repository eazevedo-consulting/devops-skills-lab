from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import requests
import json

app = FastAPI(title="Azure Infrastructure-on-Demand API")

DB_FILE = "requests.db"

class InfraRequest(BaseModel):
    env_name: str
    region: str
    create_storage: bool = False
    create_vm: bool = False
    ssh_public_key: Optional[str] = None

class InfraRequestDB(InfraRequest):
    id: int
    status: str
    reason: Optional[str] = None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  env_name TEXT, 
                  region TEXT, 
                  create_storage BOOLEAN, 
                  create_vm BOOLEAN, 
                  ssh_public_key TEXT, 
                  status TEXT, 
                  reason TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.post("/request", response_model=InfraRequestDB)
async def create_request(req: InfraRequest):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO requests (env_name, region, create_storage, create_vm, ssh_public_key, status) 
                 VALUES (?, ?, ?, ?, ?, ?)''', 
              (req.env_name, req.region, req.create_storage, req.create_vm, req.ssh_public_key, "PENDING"))
    req_id = c.lastrowid
    conn.commit()
    conn.close()
    return {**req.dict(), "id": req_id, "status": "PENDING"}

@app.get("/requests", response_model=List[InfraRequestDB])
async def list_requests():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "env_name": r[1], "region": r[2], "create_storage": bool(r[3]), 
         "create_vm": bool(r[4]), "ssh_public_key": r[5], "status": r[6], "reason": r[7]} 
        for r in rows
    ]

@app.post("/requests/{req_id}/approve")
async def approve_request(req_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Trigger GitHub Action via repository_dispatch or workflow_dispatch
    # For this demo, we'll simulate the trigger logic
    # In a real scenario, you'd use the GitHub API here
    
    c.execute("UPDATE requests SET status = ? WHERE id = ?", ("APPROVED", req_id))
    conn.commit()
    conn.close()
    
    # Example of triggering GitHub Action (requires GITHUB_TOKEN and REPO)
    # trigger_github_action(req_id, "apply", row)
    
    return {"message": f"Request {req_id} approved and deployment triggered"}

@app.post("/requests/{req_id}/reject")
async def reject_request(req_id: int, reason: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE requests SET status = ?, reason = ? WHERE id = ?", ("REJECTED", reason, req_id))
    conn.commit()
    conn.close()
    return {"message": f"Request {req_id} rejected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
