from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_api_key
from app.disks import DiskDiscoveryError, LsblkDiskDiscovery, get_disk_discovery
from app.models.schemas import DiskInventoryResponse, DiskResponse

router = APIRouter(prefix="/api/disks", tags=["disks"])


@router.get(
    "",
    response_model=DiskInventoryResponse,
    dependencies=[Depends(require_api_key)],
)
def list_disks(
    discovery: Annotated[LsblkDiskDiscovery, Depends(get_disk_discovery)],
) -> DiskInventoryResponse:
    try:
        disks = discovery.discover()
    except DiskDiscoveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Block-device inventory is unavailable.",
        ) from exc
    return DiskInventoryResponse(disks=[DiskResponse(**asdict(disk)) for disk in disks])
