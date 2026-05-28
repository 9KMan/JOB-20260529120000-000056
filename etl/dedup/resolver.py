from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein
from prisma import Prisma
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimilarityResult:
    entity_a_id: str
    entity_b_id: str
    score: float
    reason: str


class DuplicateResolver:
    """Resolve duplicate entities using PostgreSQL pg_trgm similarity."""

    def __init__(self, db: Optional[Prisma] = None, batch_size: int = 200):
        self.db = db or Prisma()
        self.batch_size = batch_size

    async def run(self) -> dict:
        """Find and mark duplicate candidates."""
        await self.db.connect()
        
        try:
            # Get all validated entities for comparison
            entities = await self.db.entity.find_many(
                where={"status": "VALIDATED"},
                take=self.batch_size,
            )
            
            candidates_found = 0
            for i, entity_a in enumerate(entities):
                for entity_b in entities[i + 1:]:
                    score = self._calculate_similarity(entity_a.name, entity_b.name)
                    
                    if score > 0.85:
                        await self._create_candidate(entity_a.id, entity_b.id, score)
                        candidates_found += 1
                        
            return {"candidates_found": candidates_found}
        finally:
            await self.db.disconnect()

    def _calculate_similarity(self, name_a: str, name_b: str) -> float:
        """Calculate similarity score between two names using multiple strategies."""
        # Exact match
        if name_a.lower() == name_b.lower():
            return 1.0
        
        # Trigram similarity
        ratio = fuzz.ratio(name_a.lower(), name_b.lower()) / 100
        partial = fuzz.partial_ratio(name_a.lower(), name_b.lower()) / 100
        token = fuzz.token_sort_ratio(name_a.lower(), name_b.lower()) / 100
        
        # Return max of the similarity metrics
        return max(ratio, partial, token)

    async def _create_candidate(
        self, entity_a_id: str, entity_b_id: str, score: float
    ) -> None:
        """Create a duplicate candidate record."""
        try:
            await self.db.duplicatecandidate.create(
                data={
                    "entityaid": entity_a_id,
                    "entitybid": entity_b_id,
                    "score": score,
                    "reason": "High name similarity",
                    "resolved": False,
                }
            )
        except Exception:
            # Candidate already exists
            pass