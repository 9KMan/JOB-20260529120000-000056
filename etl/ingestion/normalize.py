import re
import json
import hashlib
from typing import Optional


def slugify(text: str) -> str:
    """Create a URL-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def normalize_record(record: dict, source: str) -> dict:
    """Normalize a record from any source into the standard entity format."""
    name = record.get('name', record.get('title', '')).strip()
    
    return {
        'externalId': record.get('id'),
        'source': source,
        'name': name,
        'slug': slugify(name) if name else f" entity-{abs(hash(name))}",
        'summary': record.get('title') or record.get('summary', ''),
        'description': record.get('description', ''),
        'entityType': record.get('type', record.get('entity_type', 'Product')),
        'rawJson': json.dumps(record),
        'status': 'PENDING',
    }


def parse_datatype(value: str) -> str:
    """Infer attribute datatype from string value."""
    if value.lower() in ('true', 'false'):
        return 'BOOLEAN'
    if re.match(r'^-?\d+(\.\d+)?$', value):
        return 'NUMBER'
    if re.match(r'^\d{4}-\d{2}-\d{2}', value):
        return 'DATE'
    if re.match(r'^https?://', value):
        return 'URL'
    if re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
        return 'EMAIL'
    return 'STRING'