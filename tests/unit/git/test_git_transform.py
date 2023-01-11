import uuid

from infrahub.message_bus.events import InfrahubRPCResponse, RPCStatusCode, InfrahubTransformRPC, TransformMessageAction
from infrahub.git import handle_git_transform_message, InfrahubRepository


async def test_git_transform_jinja2_success(git_repo_jinja: InfrahubRepository):

    commit = git_repo_jinja.get_commit_value(branch_name="main")

    message = InfrahubTransformRPC(
        action=TransformMessageAction.JINJA2.value,
        repository_id=uuid.uuid4(),
        repository_name=git_repo_jinja.name,
        commit=commit,
        transform_location="template01.tpl.j2",
        data={"items": ["consilium", "potum", "album", "magnum"]},
    )

    response = await handle_git_transform_message(message=message, client=None)

    assert isinstance(response, InfrahubRPCResponse)
    assert response.status == RPCStatusCode.OK.value


async def test_git_transform_jinja2_missing(git_repo_jinja: InfrahubRepository):

    commit = git_repo_jinja.get_commit_value(branch_name="main")

    message = InfrahubTransformRPC(
        action=TransformMessageAction.JINJA2.value,
        repository_id=uuid.uuid4(),
        repository_name=git_repo_jinja.name,
        commit=commit,
        transform_location="template03.tpl.j2",
        data={"items": ["consilium", "potum", "album", "magnum"]},
    )

    response = await handle_git_transform_message(message=message, client=None)

    assert isinstance(response, InfrahubRPCResponse)
    assert response.status == RPCStatusCode.INTERNAL_ERROR.value


async def test_git_transform_jinja2_invalid(git_repo_jinja: InfrahubRepository):

    commit = git_repo_jinja.get_commit_value(branch_name="main")

    message = InfrahubTransformRPC(
        action=TransformMessageAction.JINJA2.value,
        repository_id=uuid.uuid4(),
        repository_name=git_repo_jinja.name,
        commit=commit,
        transform_location="template02.tpl.j2",
        data={"items": ["consilium", "potum", "album", "magnum"]},
    )

    response = await handle_git_transform_message(message=message, client=None)

    assert isinstance(response, InfrahubRPCResponse)
    assert response.status == RPCStatusCode.INTERNAL_ERROR.value
