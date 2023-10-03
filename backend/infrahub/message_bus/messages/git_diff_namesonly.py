from pydantic import Field

from infrahub.message_bus import InfrahubBaseMessage


class GitDiffNamesOnly(InfrahubBaseMessage):
    """Request a list of modified files between two commits."""

    repository_id: str = Field(..., description="The unique ID of the Repository")
    repository_name: str = Field(..., description="The name of the repository")
    first_commit: str = Field(..., description="The first commit")
    second_commit: str = Field(..., description="The second commit")
