from unittest.mock import patch

import pytest
from fastapi import FastAPI
from io import BytesIO


from src.app.routers.images import router

app = FastAPI()
app.include_router(router, prefix="/images")


@patch("app.routers.images.get_image_from_sentinelsat")
async def test_get_image_should_return_retrieved_image_from_external_service(
    mock_get_image, client
):
    mock_get_image.return_value = "test/fixtures/cat.jp2"

    response = client.get(
        "/images/image",
        params={"min_x": 29.0, "min_y": 30.0, "max_x": 31.0, "max_y": 32.0},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jp2"


async def test_get_image_should_return_appropriate_code_for_invalid_input(client):
    response = client.get(
        "/images/image",
        params={"min_x": 10000.0, "min_y": 10000.0, "max_x": 10000.0, "max_y": 10000.0},
    )
    assert response.status_code == 422


async def test_image_endpoint_post_should_store_and_make_image_retrievable(client):
    image_path = "./test/fixtures/cat.jp2"
    with open(image_path, "rb") as f:
        image_content = f.read()

    image_file = ("cat1.jp2", BytesIO(image_content), "image/jp2")

    response = client.post(
        "/images/image",
        params={"min_x": 29.0, "min_y": 30.0, "max_x": 31.0, "max_y": 32.0},
        files={"file": image_file},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data and data["message"] == "Image stored successfully"

    response = client.get(
        "/images/image",
        params={"min_x": 29.0, "min_y": 30.0, "max_x": 31.0, "max_y": 32.0},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jp2"

    downloaded_image_content = await response.aread()
    assert downloaded_image_content == image_content


async def test_image_color_endpoint_should_determine_dominant_color_correctly(client):
    image_path = "./test/fixtures/cat.jp2"
    with open(image_path, "rb") as f:
        image_content = f.read()

    image_file = ("cat2.jp2", BytesIO(image_content), "image/jp2")

    response = client.post(
        "/images/image",
        params={"min_x": 29.0, "min_y": 30.0, "max_x": 31.0, "max_y": 32.0},
        files={"file": image_file},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data and data["message"] == "Image stored successfully"

    response = client.get(
        "/images/image_color",
        params={"min_x": 29.0, "min_y": 30.0, "max_x": 31.0, "max_y": 32.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert "main_color" in data
    assert data["main_color"] == "grey"


async def test_get_image_color_return_appropriate_code_for_invalid_input(client):
    response = client.get(
        "/images/image_color",
        params={"min_x": 10000.0, "min_y": 10000.0, "max_x": 10000.0, "max_y": 10000.0},
    )
    assert response.status_code == 422
