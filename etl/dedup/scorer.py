import math
from datetime import datetime
from prisma import Prisma
from typing import Optional


class DataQualityScorer:
    """Compute data quality scores for entities."""

    def __init__(self, entity_id: str, db: Optional[Prisma] = None):
        self.entity_id = entity_id
        self.db = db or Prisma()

    async def compute(self) -> dict:
        """Compute and store quality scores for an entity."""
        await self.db.connect()
        
        try:
            entity = await self.db.entity.find_unique(
                where={"id": self.entity_id},
                include={"attributes": True}
            )
            
            if not entity:
                return {"error": "Entity not found"}
            
            freshness = self._compute_freshness(entity.updatedAt)
            completeness = self._compute_completeness(entity)
            consistency = self._compute_consistency(entity)
            overall = (freshness + completeness + consistency) / 3
            
            # Upsert data quality record
            await self.db.dataqualityrecord.upsert(
                where={"entityid": self.entity_id},
                data={
                    "create": {
                        "entityid": self.entity_id,
                        "freshness": freshness,
                        "completeness": completeness,
                        "consistency": consistency,
                        "overall": overall,
                    },
                    "update": {
                        "freshness": freshness,
                        "completeness": completeness,
                        "consistency": consistency,
                        "overall": overall,
                    }
                }
            )
            
            return {
                "freshness": freshness,
                "completeness": completeness,
                "consistency": consistency,
                "overall": overall,
            }
        finally:
            await self.db.disconnect()

    def _compute_freshness(self, last_updated: datetime) -> float:
        """Compute freshness score (0.0-1.0) based on days since last update."""
        if not last_updated:
            return 0.0
            
        days_since = (datetime.utcnow() - last_updated).days
        # Score decreases linearly from 1.0 at 0 days to 0.0 at 90+ days
        freshness = max(0.0, 1.0 - (days_since / 90))
        return round(freshness, 3)

    def _compute_completeness(self, entity) -> float:
        """Compute completeness score (0.0-1.0) based on populated fields."""
        required_fields = ['name', 'entityType']
        optional_fields = ['summary', 'description', 'externalId']
        
        required_populated = sum(1 for f in required_fields if getattr(entity, f, None))
        optional_populated = sum(1 for f in optional_fields if getattr(entity, f, None))
        
        required_score = required_populated / len(required_fields)
        optional_score = optional_populated / len(optional_fields)
        
        # Required fields weigh more (70%) than optional (30%)
        return round(required_score * 0.7 + optional_score * 0.3, 3)

    def _compute_consistency(self, entity) -> float:
        """Compute consistency score based on schema compliance."""
        score = 1.0
        
        # Check entityType is valid
        valid_types = {'Product', 'Place', 'Person', 'Organization', 'Event'}
        if entity.entityType not in valid_types:
            score -= 0.3
            
        # Check name is reasonable length
        if len(entity.name) < 2 or len(entity.name) > 500:
            score -= 0.2
            
        # Check description length if present
        if entity.description:
            if len(entity.description) < 10:
                score -= 0.1
            elif len(entity.description) > 50000:
                score -= 0.1
                
        return max(0.0, round(score, 3))