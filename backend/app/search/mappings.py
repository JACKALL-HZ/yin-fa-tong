"""ES 索引映射定义 —— 使用 IK 中文分词器

索引用 ik_max_word（最大切分，高召回），搜索用 ik_smart（粗粒度，高精度）。
"""

from app.shared.elasticsearch import INDEX_HOSPITAL, INDEX_DEPARTMENT, INDEX_DOCTOR, INDEX_SYMPTOM

# 共用 settings 模板
_BASE_SETTINGS = {
    "index": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "analysis": {
        "analyzer": {
            "ik_index_analyzer": {"type": "custom", "tokenizer": "ik_max_word"},
            "ik_search_analyzer": {"type": "custom", "tokenizer": "ik_smart"},
        }
    },
}

# 文本字段模板：索引用 ik_max_word，搜索用 ik_smart
IK_TEXT = {"type": "text", "analyzer": "ik_index_analyzer", "search_analyzer": "ik_search_analyzer"}

INDEX_MAPPINGS = {
    INDEX_HOSPITAL: {
        "settings": _BASE_SETTINGS,
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "hospital_name": IK_TEXT,
                "hospital_level": {"type": "keyword"},
                "address": IK_TEXT,
            }
        },
    },
    INDEX_DEPARTMENT: {
        "settings": _BASE_SETTINGS,
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "hospital_id": {"type": "integer"},
                "hospital_name": IK_TEXT,
                "dept_name": IK_TEXT,
            }
        },
    },
    INDEX_DOCTOR: {
        "settings": _BASE_SETTINGS,
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "dept_id": {"type": "integer"},
                "hospital_id": {"type": "integer"},
                "doctor_name": IK_TEXT,
                "doctor_title": IK_TEXT,
                "specialty": IK_TEXT,
                "register_fee": {"type": "float"},
                "doctor_avatar": {"type": "keyword", "index": False},
                "dept_name": IK_TEXT,
                "hospital_name": IK_TEXT,
            }
        },
    },
    INDEX_SYMPTOM: {
        "settings": _BASE_SETTINGS,
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "keywords": IK_TEXT,
                "dept_name": {"type": "keyword"},
                "weight": {"type": "integer"},
            }
        },
    },
}
