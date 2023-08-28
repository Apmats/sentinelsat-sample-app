from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from app.database import get_db
from app.models import BoundingBox
from app.settings import get_settings
from sentinelsat import SentinelAPI, geojson_to_wkt, make_path_filter
from sentinelsat.exceptions import QuerySyntaxError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import logging
from datetime import date
import os
import shutil
from dateutil.relativedelta import relativedelta

from app.util import get_main_color

router = APIRouter()

logger = logging.getLogger(__name__)


async def get_image_from_db(
    min_x: float, min_y: float, max_x: float, max_y: float, db: AsyncSession
) -> str | None:
    statement = select(BoundingBox).where(
        BoundingBox.min_x == min_x,
        BoundingBox.max_x == max_x,
        BoundingBox.min_y == min_y,
        BoundingBox.max_y == max_y,
    )
    results = await db.exec(statement)
    bounding_box = results.first()
    if bounding_box:
        return bounding_box.image_path
    return None


def find_file_by_extension(directory: str, target_extension: str) -> str:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(target_extension):
                return os.path.join(root, file)
    return None


def get_image_from_sentinelsat(
    min_x: float, min_y: float, max_x: float, max_y: float
) -> str:
    try:
        bbox_wkt = geojson_to_wkt(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        (min_x, min_y),
                        (max_x, min_y),
                        (max_x, max_y),
                        (min_x, max_y),
                        (min_x, min_y),
                    ]
                ],
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=e.args[0])
    api = SentinelAPI(get_settings().sentinelsat_user, get_settings().sentinelsat_pass)
    try:
        products = api.query(
            bbox_wkt,
            date=(
                (date.today() + relativedelta(months=-6)).strftime("%Y%m%d"),
                date.today().strftime("%Y%m%d"),
            ),
            order_by="-generationdate",
            platformname="Sentinel-2",
            producttype="S2MSI2A",
            cloudcoverpercentage=(0, 30),
        )
        if products:
            product_list = list(products.items())
            first_product = product_list[0][1]
            first_product_id = product_list[0][0]
            path_filter = make_path_filter("*_TCI*10m.jp2")

            api.download(
                first_product_id,
                directory_path=get_settings().temp_image_directory,
                nodefilter=path_filter,
            )

            return find_file_by_extension(
                os.path.join(
                    get_settings().temp_image_directory, first_product["filename"]
                ),
                ".jp2",
            )
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Failed to connect to sentinelsat")
    except QuerySyntaxError as er:
        raise HTTPException(status_code=422, detail=er.msg)


async def get_image_path(
    min_x: float, min_y: float, max_x: float, max_y: float, db: AsyncSession
) -> str | None:
    if image_path := await get_image_from_db(min_x, min_y, max_x, max_y, db):
        return image_path
    else:
        image_path = get_image_from_sentinelsat(min_x, min_y, max_x, max_y)
        return image_path


@router.get("/image")
async def get_image(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    db: AsyncSession = Depends(get_db),
):
    path = await get_image_path(min_x, min_y, max_x, max_y, db)
    if path:
        return FileResponse(path, media_type="image/jp2")


@router.post("/image")
async def post_image(
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_path = os.path.join(get_settings().image_directory, file.filename)

    with open(image_path, "wb") as image_file:
        shutil.copyfileobj(file.file, image_file)

    bounding_box = BoundingBox(
        min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, image_path=image_path
    )

    db.add(bounding_box)
    await db.commit()

    response_data = {"message": "Image stored successfully"}
    return JSONResponse(content=response_data, status_code=200)


@router.get("/image_color")
async def get_image_color(
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    db: AsyncSession = Depends(get_db),
):
    path = await get_image_path(min_x, min_y, max_x, max_y, db)
    if path:
        color = get_main_color(path)
        response_data = {"main_color": color}
        return JSONResponse(content=response_data, status_code=200)
