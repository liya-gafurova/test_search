import inspect
import json
import uuid
from datetime import datetime
import os
from typing import List, Dict
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.schemas import Bible, Chapter, Book
from app.settings import settings


def generate_uuid() -> str:
    return uuid.uuid4().hex


def get_file_extension(filepath: str) -> str:
    extension = Path(filepath).suffix
    return extension


def get_file_name_without_extension(filepath: str) -> str:
    name = Path(filepath).stem
    return name


def get_formatted_filepath(formatted_filepath: str, date_configurator: datetime) -> str:
    """
    :param formatted_filepath: 'some/path/{year}/{month}/{day}/'
    :param date_configurator:  e.g. datetime.datetime.now()
    :return: some/path/2022/3/11/
    """

    return formatted_filepath.format(year=date_configurator.year,
                                     month=date_configurator.month,
                                     day=date_configurator.day)


def create_dir_if_not_exists(dir_path: str):
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


def get_file_name(filepath: str) -> str:
    return os.path.basename(filepath)


def get_filename_with_modifier(name: str) -> str:
    """
    :param name: file.txt
    :return: file_20220322173512.txt
    """
    filename_without_ext = get_file_name_without_extension(name)
    ext = get_file_extension(name)

    modifier_base: datetime = datetime.now()
    datetime_modifier = get_datetime_modifier(modifier_base)

    new_name = f"{filename_without_ext}_{datetime_modifier}{ext}"
    return new_name


def get_datetime_modifier(modifier_base: datetime):
    """
    :param modifier_base: 2022-03-12 12:35:12
    :return: 20220312123512
    """
    return f'{modifier_base.year}{modifier_base.month}{modifier_base.day}{modifier_base.hour}{modifier_base.minute}{modifier_base.second}'


def read_json(json_path: str) -> Dict:
    with open(json_path, mode="r") as json_file:
        return json.loads(json_file.read())


def get_file_url(filename: str) -> str:
    """
    :param filename: e.g 'some_file.gpx'
    :param entity_type: e.g 'TrackFile'
    :return: media/uploaded/files/tracks/2022/3/11/some_file_20220322173512.gpx
    """
    path = settings.SOURCE_FILES_DIR
    create_dir_if_not_exists(path)
    filename_with_modifier = get_filename_with_modifier(filename)
    path_with_filename = os.path.join(path, filename_with_modifier)

    return path_with_filename


async def save_file(filepath: str, file: UploadFile):
    # store file to storage / filesystem
    async with aiofiles.open(filepath, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)


async def save_json(filepath: str, json_data: str):
    async with aiofiles.open(filepath, 'wb') as out_file:
        await out_file.write(bytes(json_data, 'utf-8'))


################################





