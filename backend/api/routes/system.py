import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from database import get_db

try:
    import docker
    # We use from_env() which will pick up /var/run/docker.sock mounted
    docker_client = docker.from_env()
except Exception as e:
    docker_client = None

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/docker")
async def get_docker_stats():
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker client not initialized. Socket not mounted?")
    
    try:
        containers = docker_client.containers.list(all=True)
        results = []
        for c in containers:
            # Check if this container is part of our compose project
            labels = c.labels
            project = labels.get('com.docker.compose.project')
            if project and project != 'projectwhereami_now':
                pass # You can filter if you want, but maybe the user wants to see all. We will show all for now.
            
            # CPU/Mem stats (stream=False makes it synchronous and one-shot)
            stats = c.stats(stream=False)
            
            # Calculation for CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_cpu_delta = stats['cpu_stats'].get('system_cpu_usage', 0) - stats['precpu_stats'].get('system_cpu_usage', 0)
            number_cpus = stats['cpu_stats'].get('online_cpus', 1)
            
            cpu_percent = 0.0
            if system_cpu_delta > 0.0 and cpu_delta > 0.0:
                cpu_percent = (cpu_delta / system_cpu_delta) * number_cpus * 100.0
                
            # Calculation for Mem usage
            mem_usage = stats['memory_stats'].get('usage', 0)
            mem_limit = stats['memory_stats'].get('limit', 0)
            mem_percent = 0.0
            if mem_limit > 0:
                mem_percent = (mem_usage / mem_limit) * 100.0
                
            # Memory in MB
            mem_mb = mem_usage / (1024 * 1024)
            
            # Logs
            logs = c.logs(tail=20).decode('utf-8', errors='replace').splitlines()
            
            results.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.id,
                "cpu_percent": round(cpu_percent, 2),
                "mem_mb": round(mem_mb, 2),
                "mem_percent": round(mem_percent, 2),
                "logs": "\n".join(logs)
            })
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/host")
async def get_host_stats():
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "mem_total_mb": round(mem.total / (1024 * 1024), 2),
            "mem_used_mb": round(mem.used / (1024 * 1024), 2),
            "mem_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
            "disk_percent": disk.percent,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db")
async def get_db_stats(db: AsyncSession = Depends(get_db)):
    try:
        query = text("""
            SELECT 
                relname as table_name, 
                n_live_tup as row_count 
            FROM pg_stat_user_tables 
            ORDER BY n_live_tup DESC;
        """)
        result = await db.execute(query)
        rows = result.fetchall()
        
        size_query = text("SELECT pg_size_pretty(pg_database_size('whereami_db')) as size;")
        size_res = await db.execute(size_query)
        db_size = size_res.scalar()

        stats = {
            "status": "Online",
            "size": db_size,
            "tables": [{"name": r.table_name, "rows": r.row_count} for r in rows]
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ollama")
async def get_ollama_stats():
    import httpx
    import os
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{ollama_host}/api/tags")
            res.raise_for_status()
            models = res.json().get("models", [])
            
            # optionally query process info or show log (Ollama doesn't have a direct /api/logs endpoint usually)
            return {
                "status": "online",
                "host": ollama_host,
                "models": models
            }
    except Exception as e:
        return {
            "status": "offline",
            "host": ollama_host,
            "error": str(e)
        }
