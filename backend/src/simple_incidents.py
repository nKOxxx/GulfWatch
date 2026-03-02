# Temporarily replace the complex /incidents endpoint
# with a simpler version that works

SIMPLE_ENDPOINT = '''
@app.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    limit: int = Query(50, ge=1, le=200),
    min_status: str = Query("PROBABLE", enum=["UNCONFIRMED", "PROBABLE", "LIKELY", "CONFIRMED"]),
    db: Session = Depends(get_db)
):
    """Get all active incidents - SIMPLIFIED VERSION"""
    from sqlalchemy import text
    
    # Use raw SQL that definitely works
    query = """
    SELECT 
        id, status, event_type, classification, location_name,
        ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng,
        description, guidance, detected_at, confirmed_at,
        reports_count, unique_sources_count, media_urls
    FROM incidents 
    WHERE is_active = true 
      AND status NOT IN ('FALSE_ALARM', 'RESOLVED')
    ORDER BY detected_at DESC
    LIMIT :limit
    """
    
    result = db.execute(text(query), {'limit': limit})
    
    response = []
    for row in result:
        response.append(IncidentResponse(
            id=str(row.id),
            status=row.status,
            event_type=row.event_type,
            classification=row.classification,
            location_name=row.location_name,
            lat=row.lat or 0,
            lng=row.lng or 0,
            distance_meters=None,
            description=row.description,
            guidance=row.guidance,
            detected_at=row.detected_at,
            reports_count=row.reports_count or 0,
            unique_sources_count=row.unique_sources_count or 0,
            media_urls=row.media_urls or []
        ))
    
    return response
'''

print(SIMPLE_ENDPOINT)
