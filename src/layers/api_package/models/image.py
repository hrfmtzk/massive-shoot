from datetime import (
    datetime,
    timezone,
)
import os
import typing

from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
)
from pynamodb.models import Model

table_name = os.environ["TABLE_NAME"]
table_region = os.environ["TABLE_REGION"]


class ImageModel(Model):
    class Meta:
        region = table_region
        table_name = table_name

    user_id = UnicodeAttribute(hash_key=True, attr_name="UserId")
    image_id = UnicodeAttribute(range_key=True, attr_name="ImageId")
    content_type = UnicodeAttribute(attr_name="ContentType")
    created = NumberAttribute(attr_name="Created")


def get_all_items():
    res = ImageModel.scan()
    items = [item for item in res]
    while res.last_evaluated_key:
        res = ImageModel.scan(last_evaluated_key=res.last_evaluated_key)
        items.extend([item for item in res])

    return items


def convert_respones_image(
    item: ImageModel,
    base_url: str,
    image_prefix: str,
) -> typing.Dict[str, typing.Any]:
    return {
        "id": item.image_id,
        "url": base_url + "/".join([image_prefix, item.user_id, item.image_id]),
        "timestamp": datetime.fromtimestamp(
            item.created, timezone.utc
        ).isoformat(),
        "user_id": item.user_id,
    }
