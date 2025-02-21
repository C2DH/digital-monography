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
        # DYNAMODB_ASSETS_DOC_INFO_TBL,
        # DYNAMODB_ASSETS_UPLOAD_INFO_TBL,
        # DYNAMODB_ASSETS_BOOK_INFO_TBL,
        METADATA_ASSETS_BUCKET_NAME,
    )
except (ImportError, ModuleNotFoundError):
    from ..constants import (
        # DYNAMODB_ASSETS_DOC_INFO_TBL,
        # DYNAMODB_ASSETS_UPLOAD_INFO_TBL,
        # DYNAMODB_ASSETS_BOOK_INFO_TBL,
        METADATA_ASSETS_BUCKET_NAME,
    )


class Medium(enum.StrEnum):
    PAPER = "P"
    DIGITAL = "D"
    PAPER_AND_DIGITAL = "P+D"


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
        if hasattr(record, "medium") and record.medium in (
            Medium.PAPER,
            Medium.PAPER_AND_DIGITAL,
        ):
            self.count_paper += 1
        if getattr(record, "is_ready", False) == True:
            self.count_ready += 1


class AssetsWriter:
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


# if the paper and digital differs, there should be 2 separate records
@dataclasses.dataclass
class AssetInfoFromDoc(AssetInfoBase):
    f"""
    Information about an asset extracted from a document, especially from
    * Metadata Tables
    * captions
    * target id above caption
    """

    name: str
    slug: str
    # medium: t.Literal["P", "D", "P+D"]
    medium: Medium
    author: str
    source: str
    location: str
    alttext: str
    caption: str
    comments: str
    is_color: bool
    is_on_paper: bool  # maybe this can be computed from "medium"
    is_ready: bool

    # @property
    # def db_table(self) -> str:
    #     return DYNAMODB_ASSETS_DOC_INFO_TBL

    @property
    def s3_key(self) -> str:
        return f"{self.slug}/{self.location}.json"


@dataclasses.dataclass
class AssetInfoFromUpload(AssetInfoBase):
    f"""
    Upload level data. Information about an asset fetched from S3.
    """
    key: str
    slug: (
        str  # maybe computed from "key"? this does not exist in s3 ListObjects response
    )
    name: (
        str  # maybe computed from "key"? this does not exist in s3 ListObjects response
    )
    exists: bool  # hmm, maybe if no record then it doesn't exist?
    last_modified: datetime.datetime
    size: int
    # e_tag: str # incl. in response from s3 ListObjects
    # storage_class: str # incl. in response from s3 ListObjects

    # @property
    # def db_table(self) -> str:
    #     return DYNAMODB_ASSETS_UPLOAD_INFO_TBL

    @property
    def s3_key(self) -> str:
        # return f"{self.slug}/{self.key}.json"
        return f"{self.key}_upload_data.json"


@dataclasses.dataclass
class AssetInfoFromBook(AssetInfoBase):
    f"""
    Book level data. Information about an asset that can be gathered
    jointly based on all parts of a book, especially:
    * references
    """
    slug: str
    # ?? refs
    # TODO: implement AssetInfoFromBook

    # @property
    # def db_table(self) -> str:
    #     return DYNAMODB_ASSETS_BOOK_INFO_TBL

    @property
    def s3_key(self) -> str:
        return f"{self.slug}/_data_from_book.json"
