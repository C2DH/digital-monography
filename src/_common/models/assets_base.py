import abc
import dataclasses
import datetime
import enum
import json
import typing as t

from mypy_boto3_dynamodb.client import DynamoDBClient as boto3_DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    PutItemOutputTypeDef as boto3_PutItemOutputTypeDef,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_s3.type_defs import (
    PutObjectOutputTypeDef as boto3_PutObjectOutputTypeDef,
)

try:
    from constants import (
        METADATA_ASSETS_BUCKET_NAME,
        MediumEnum,
    )
except (ImportError, ModuleNotFoundError):
    from ..constants import (
        METADATA_ASSETS_BUCKET_NAME,
        MediumEnum,
    )


class AssetInfoEncoder(json.JSONEncoder):
    def default(self, record):
        if dataclasses.is_dataclass(record):
            new_record = {}
            for field in dataclasses.fields(record):
                field: dataclasses.Field
                val = getattr(record, field.name)
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                elif isinstance(val, enum.Enum):
                    val = val.value
                elif field.type not in [str, int, bool]:
                    val = str(val)
                new_record[field.name] = val
            return new_record
        return super().default(record)


@dataclasses.dataclass
class AssetInfoBase(abc.ABC):
    # def dumps(self) -> None:
    #     return json.dumps(self.__dict__, default=str)

    # @property
    # def db_table(self) -> str:
    #     raise NotImplementedError

    @property
    def s3_key(self) -> str:
        raise NotImplementedError

    def send_item(
        self, client: t.Optional[boto3_DynamoDBClient]
    ) -> t.Optional[boto3_PutItemOutputTypeDef]:
        if client is None:
            return
        return client.put_item(TableName=self.db_table, Item={})

    # def __str__(self) -> str:
    #     fields = ", ".join(
    #         [f"{attr}={getattr(self, attr)}" for attr in self.__annotations__.keys()]
    #     )
    #     return f"{self.__class__.__name__}({fields})"


class AssetsStats:
    def __init__(self):
        self.count_assets: int = 0
        self.count_color: int = 0
        self.count_paper: int = 0
        self.count_ready: int = 0

    def update(self, record: AssetInfoBase) -> None:
        self.count_assets += 1
        if getattr(record, "is_color", False) == True:
            self.count_color += 1
        if getattr(record, "medium", None) in (
            MediumEnum.PAPER,
            MediumEnum.PAPER_AND_DIGITAL,
        ):
            self.count_paper += 1
        if getattr(record, "is_ready", False) == True:
            self.count_ready += 1


class Assets:
    def __init__(self, s3_key: t.Optional[str] = None):
        self._s3_key = s3_key
        self._s3_bucket: str = METADATA_ASSETS_BUCKET_NAME
        self._records: list[AssetInfoBase] = []
        self._stats: AssetsStats = AssetsStats()

    def add(self, record: AssetInfoBase) -> None:
        self._records.append(record)
        self._stats.update(record)
        if self._s3_key is None:
            self._s3_key = record.s3_key

    def write_to_s3(
        self, client: t.Optional[boto3_S3Client]
    ) -> boto3_PutObjectOutputTypeDef:
        if client is None:
            return
        elif self._s3_key is None:
            raise Exception(
                "Cannot write to storage, no S3 key found. Please provide S3 key."
            )
        return client.put_object(
            Body=self._records_in_bytes(),
            Bucket=self._s3_bucket,
            Key=self._s3_key,
        )

    def _records_in_bytes(self) -> bytes:
        s = json.dumps(self._records, cls=AssetInfoEncoder)
        return s.encode("utf-8")
