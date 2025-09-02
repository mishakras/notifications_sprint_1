import logging

import requests
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(docs_url=None, redoc_url=None)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_URLS = {
    "auth": "http://nginx/api/v1/auth/openapi.json",
    "content": "http://nginx/api/v1/openapi.json",
    "ugc": "http://nginx/api/v1/ugc/openapi.json",
}


@app.get("/openapi.json")
def aggregated_openapi():
    schemas = {}
    components = {"schemas": {}}
    tags = []

    for name, url in SERVICE_URLS.items():
        logger.info(f"Fetching OpenAPI for {name} from {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Successfully fetched data from {url}")

            for path, methods in data["paths"].items():
                prefixed_path = f"{path}"
                schemas[prefixed_path] = methods

            for tag in data.get("tags", []):
                tag["name"] = f"{name}: {tag['name']}"
                tags.append(tag)

            components["schemas"].update(
                data.get("components", {}).get("schemas", {}),
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while fetching {url}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while fetching {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    logger.info(f"Schemas: {schemas}")
    logger.info(f"Tags: {tags}")
    logger.info(f"Components: {components}")

    combined = {
        "openapi": "3.0.0",
        "info": {
            "title": "Aggregated API",
            "version": "1.0.0",
        },
        "paths": schemas,
        "tags": tags,
        "components": components,
    }

    return combined


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    app.openapi = aggregated_openapi
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Aggregated Swagger UI",
    )
