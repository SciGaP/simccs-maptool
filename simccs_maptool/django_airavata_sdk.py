# Placeholder for the Airavata Django Portal Framework (ADPF) SDK, forthcoming
import logging
import mimetypes
import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage

# These are provided in airavata-django-portal, but need to move to SDK
from airavata.model.data.replica.ttypes import (
    DataProductModel,
    DataProductType,
    DataReplicaLocationModel,
    ReplicaLocationCategory,
    ReplicaPersistentType,
)

logger = logging.getLogger(__name__)

########################################################################
# data_products_helper.py
########################################################################
TMP_INPUT_FILE_UPLOAD_DIR = "tmp"


def save_input_file(request, file, name=None, content_type=None):
    """Save input file in staging area for input file uploads."""
    username = request.user.username
    file_name = name if name is not None else os.path.basename(file.name)
    full_path = datastore_save(username, TMP_INPUT_FILE_UPLOAD_DIR, file)
    data_product = _save_data_product(
        request, full_path, name=file_name, content_type=content_type
    )
    return data_product


def open_file(request, data_product_uri):
    "Return file object for replica if it exists in user storage."
    data_product = request.airavata_client.getDataProduct(
        request.authz_token, data_product_uri
    )
    path = _get_replica_filepath(data_product)
    return datastore_open(data_product.ownerName, path)


def _save_data_product(request, full_path, name=None, content_type=None):
    "Create, register and record in DB a data product for full_path."
    data_product = _create_data_product(
        request.user.username, full_path, name=name, content_type=content_type
    )
    product_uri = _register_data_product(request, full_path, data_product)
    data_product.productUri = product_uri
    return data_product


def _register_data_product(request, full_path, data_product):
    product_uri = request.airavata_client.registerDataProduct(
        request.authz_token, data_product
    )
    return product_uri


def _create_data_product(username, full_path, name=None, content_type=None):
    data_product = DataProductModel()
    data_product.gatewayId = settings.GATEWAY_ID
    data_product.ownerName = username
    if name is not None:
        file_name = name
    else:
        file_name = os.path.basename(full_path)
    data_product.productName = file_name
    data_product.dataProductType = DataProductType.FILE
    final_content_type = _determine_content_type(full_path, content_type)
    if final_content_type is not None:
        data_product.productMetadata = {"mime-type": final_content_type}
    data_replica_location = _create_replica_location(full_path, file_name)
    data_product.replicaLocations = [data_replica_location]
    return data_product


def _determine_content_type(full_path, content_type=None):
    result = content_type
    if result is None:
        # Try to guess the content-type from file extension
        guessed_type, encoding = mimetypes.guess_type(full_path)
        result = guessed_type
    if result is None or result == "application/octet-stream":
        # Check if file is Unicode text by trying to read some of it
        try:
            open(full_path, "r").read(1024)
            result = "text/plain"
        except UnicodeDecodeError:
            logger.debug(f"Failed to read as Unicode text: {full_path}")
    return result


def _create_replica_location(full_path, file_name):
    data_replica_location = DataReplicaLocationModel()
    data_replica_location.storageResourceId = settings.GATEWAY_DATA_STORE_RESOURCE_ID
    data_replica_location.replicaName = "{} gateway data store copy".format(file_name)
    data_replica_location.replicaLocationCategory = (
        ReplicaLocationCategory.GATEWAY_DATA_STORE
    )
    data_replica_location.replicaPersistentType = ReplicaPersistentType.TRANSIENT
    data_replica_location.filePath = "file://{}:{}".format(
        settings.GATEWAY_DATA_STORE_HOSTNAME, full_path
    )
    return data_replica_location


def _get_replica_filepath(data_product):
    replica_filepaths = [
        rep.filePath
        for rep in data_product.replicaLocations
        if rep.replicaLocationCategory == ReplicaLocationCategory.GATEWAY_DATA_STORE
    ]
    replica_filepath = replica_filepaths[0] if len(replica_filepaths) > 0 else None
    if replica_filepath:
        return urlparse(replica_filepath).path
    return None


########################################################################
# datastore.py
########################################################################


def datastore_save(username, path, file, name=None):
    """Save file to username/path in data store."""
    # file.name may be full path, so get just the name of the file
    file_name = name if name is not None else os.path.basename(file.name)
    user_data_storage = _user_data_storage(username)
    file_path = os.path.join(path, user_data_storage.get_valid_name(file_name))
    input_file_name = user_data_storage.save(file_path, file)
    input_file_fullpath = user_data_storage.path(input_file_name)
    return input_file_fullpath


def datastore_open(username, path):
    """Open path for user if it exists in this data store."""
    if datastore_exists(username, path):
        return _user_data_storage(username).open(path)
    else:
        raise ObjectDoesNotExist("File path does not exist: {}".format(path))


def datastore_exists(username, path):
    """Check if file path exists in this data store."""
    try:
        return _user_data_storage(username).exists(path) and os.path.isfile(
            datastore_path_(username, path)
        )
    except SuspiciousFileOperation as e:
        logger.warning("Invalid path for user {}: {}".format(username, str(e)))
        return False


def datastore_path_(username, file_path):
    user_data_storage = _user_data_storage(username)
    return user_data_storage.path(file_path)


def _user_data_storage(username):
    return FileSystemStorage(
        location=os.path.join(settings.GATEWAY_DATA_STORE_DIR, username)
    )
