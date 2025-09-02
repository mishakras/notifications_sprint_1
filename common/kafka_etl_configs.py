from pydantic import BaseModel


class TopicSettings(BaseModel):
    page_views: dict = {
        "table": "user_page_views",
        "topic": "ugc_PageView",
        "fields": {
            "created_at": "DateTime",
            "user_id": "UUID",
            "page_id": "UUID",
            "page_url": "String",
            "page_type": "String",
            "duration_seconds": "DOUBLE",
        },
    }
    clicks: dict = {
        "table": "user_clicks",
        "topic": "ugc_Clicks",
        "fields": {
            "created_at": "DateTime",
            "user_id": "UUID",
            "target_id": "UUID",
            "target_type": "String",
            "page_url": "String",
        },
    }
    video_quality_changes: dict = {
        "table": "user_video_quality_changes",
        "topic": "ugc_VideoQuality",
        "fields": {
            "created_at": "DateTime",
            "user_id": "UUID",
            "film_id": "UUID",
            "from_quality": "String",
            "to_quality": "String",
        },
    }
    video_completions: dict = {
        "table": "user_video_completions",
        "topic": "ugc_VideoCompletions",
        "fields": {
            "created_at": "DateTime",
            "user_id": "UUID",
            "film_id": "UUID",
            "duration": "DOUBLE",
            "watched_percentage": "DOUBLE",
        },
    }
    search_filter_usages: dict = {
        "table": "user_search_filter_usages",
        "topic": "ugc_SearchFilters",
        "fields": {
            "created_at": "DateTime",
            "user_id": "UUID",
            "page_id": "UUID",
            "filter_type": "String",
            "filter_value": "String",
            "search_query": "Nullable(String)",
        },
    }
