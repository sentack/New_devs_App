from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import DatabasePool
from sqlalchemy import text

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


@router.get("/properties")
async def get_properties(
    current_user: dict = Depends(get_current_user)
):
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    db_pool = DatabasePool()
    await db_pool.initialize()

    if not db_pool.session_factory:
        raise HTTPException(status_code=500, detail="Database unavailable")

    async with db_pool.get_session() as session:
        query = text("""
            SELECT id, name, timezone
            FROM properties
            WHERE tenant_id = :tenant_id
            ORDER BY name
        """)

        result = await session.execute(
            query,
            {"tenant_id": tenant_id}
        )

        properties = [
            {
                "id": row.id,
                "name": row.name,
                "timezone": row.timezone
            }
            for row in result.fetchall()
        ]

        return {
            "items": properties,
            "total": len(properties)
        }