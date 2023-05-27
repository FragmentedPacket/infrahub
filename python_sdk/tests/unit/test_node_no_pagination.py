from dataclasses import dataclass

import pytest
from pytest_httpx import HTTPXMock

from infrahub_client.client import InfrahubClient, InfrahubClientSync
from infrahub_client.exceptions import NodeNotFound
from infrahub_client.node import (
    InfrahubNode,
    InfrahubNodeBase,
    InfrahubNodeSync,
    RelatedNodeBase,
    RelationshipManagerBase,
)

# pylint: disable=no-member
# type: ignore[attr-defined]

async_node_methods = [method for method in dir(InfrahubNode) if not method.startswith("_")]
sync_node_methods = [method for method in dir(InfrahubNodeSync) if not method.startswith("_")]

client_types = ["standard", "sync"]


@dataclass
class BothClients:
    sync: InfrahubClientSync
    standard: InfrahubClient


@pytest.fixture
async def client() -> InfrahubClient:
    return await InfrahubClient.init(address="http://mock", insert_tracker=True, pagination=True)


@pytest.fixture
async def clients() -> BothClients:
    both = BothClients(
        standard=await InfrahubClient.init(address="http://mock", insert_tracker=True, pagination=True),
        sync=InfrahubClientSync.init(address="http://mock", insert_tracker=True, pagination=True),
    )
    return both


@pytest.mark.parametrize("client_type", client_types)
async def test_init_node_data_graphql(client, location_schema, location_data01, client_type):
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=location_data01)
    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=location_data01)

    assert node.name.value == "DFW"
    assert node.name.is_protected is True
    assert node.description.value is None
    assert node.type.value == "SITE"

    assert isinstance(node.tags, RelationshipManagerBase)
    assert len(node.tags.peers) == 1
    assert isinstance(node.tags.peers[0], RelatedNodeBase)
    assert isinstance(node.primary_tag, RelatedNodeBase)
    assert node.primary_tag.id == "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr"
    assert node.primary_tag.typename == "Tag"


@pytest.mark.parametrize("client_type", client_types)
async def test_query_data_no_filters(client, location_schema, client_type):
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema)
    else:
        node = InfrahubNodeSync(client=client, schema=location_schema)

    assert node.generate_query_data_no_pagination() == {
        "location": {
            "id": None,
            "display_label": None,
            "name": {
                "is_protected": None,
                "is_visible": None,
                "owner": {"__typename": None, "display_label": None, "id": None},
                "source": {"__typename": None, "display_label": None, "id": None},
                "value": None,
            },
            "description": {
                "is_protected": None,
                "is_visible": None,
                "owner": {"__typename": None, "display_label": None, "id": None},
                "source": {"__typename": None, "display_label": None, "id": None},
                "value": None,
            },
            "type": {
                "is_protected": None,
                "is_visible": None,
                "owner": {"__typename": None, "display_label": None, "id": None},
                "source": {"__typename": None, "display_label": None, "id": None},
                "value": None,
            },
            "primary_tag": {
                "id": None,
                "display_label": None,
                "__typename": None,
                "_relation__is_protected": None,
                "_relation__is_visible": None,
                "_relation__owner": {
                    "__typename": None,
                    "display_label": None,
                    "id": None,
                },
                "_relation__source": {
                    "__typename": None,
                    "display_label": None,
                    "id": None,
                },
            },
            "tags": {
                "id": None,
                "display_label": None,
                "__typename": None,
                "_relation__is_protected": None,
                "_relation__is_visible": None,
                "_relation__owner": {
                    "id": None,
                    "__typename": None,
                    "display_label": None,
                },
                "_relation__source": {
                    "id": None,
                    "__typename": None,
                    "display_label": None,
                },
            },
        },
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_create_input_data(client, location_schema, client_type):
    data = {"name": {"value": "JFK1"}, "description": {"value": "JFK Airport"}, "type": {"value": "SITE"}}

    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=data)
    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=data)
    assert node._generate_input_data()["data"] == {
        "data": {
            "name": {"value": "JFK1"},
            "description": {"value": "JFK Airport"},
            "type": {"value": "SITE"},
            # "primary_tag": None,
            "tags": [],
        }
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_create_input_data__with_relationships_02(client, location_schema, client_type):
    """Validate input data with variables that needs replacements"""
    data = {
        "name": {"value": "JFK1"},
        "description": {"value": "JFK\n Airport"},
        "type": {"value": "SITE"},
        "primary_tag": "pppppppp",
        "tags": [{"id": "aaaaaa"}, {"id": "bbbb"}],
    }
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=data)
    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=data)

    input_data = node._generate_input_data()
    assert len(input_data["variables"].keys()) == 1
    key = list(input_data["variables"].keys())[0]
    value = input_data["variables"][key]

    expected = {
        "data": {
            "name": {"value": "JFK1"},
            "description": {"value": f"${key}"},
            "type": {"value": "SITE"},
            "tags": [{"id": "aaaaaa"}, {"id": "bbbb"}],
            "primary_tag": {"id": "pppppppp"},
        }
    }
    assert input_data["data"] == expected
    assert value == "JFK\n Airport"


@pytest.mark.parametrize("client_type", client_types)
async def test_create_input_data__with_relationships_01(client, location_schema, client_type):
    data = {
        "name": {"value": "JFK1"},
        "description": {"value": "JFK Airport"},
        "type": {"value": "SITE"},
        "primary_tag": "pppppppp",
        "tags": [{"id": "aaaaaa"}, {"id": "bbbb"}],
    }
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=data)
    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=data)
    assert node._generate_input_data()["data"] == {
        "data": {
            "name": {"value": "JFK1"},
            "description": {"value": "JFK Airport"},
            "type": {"value": "SITE"},
            "tags": [{"id": "aaaaaa"}, {"id": "bbbb"}],
            "primary_tag": {"id": "pppppppp"},
        }
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_create_input_data_with_relationships_02(clients, rfile_schema, client_type):
    data = {
        "name": {"value": "rfile01", "is_protected": True, "source": "ffffffff", "owner": "ffffffff"},
        "template_path": {"value": "mytemplate.j2"},
        "query": {"id": "qqqqqqqq", "source": "ffffffff", "owner": "ffffffff"},
        "template_repository": {"id": "rrrrrrrr", "source": "ffffffff", "owner": "ffffffff"},
        "tags": [{"id": "t1t1t1t1"}, "t2t2t2t2"],
    }
    if client_type == "standard":
        node = InfrahubNode(client=clients.standard, schema=rfile_schema, data=data)
    else:
        node = InfrahubNodeSync(client=clients.sync, schema=rfile_schema, data=data)

    assert node._generate_input_data()["data"] == {
        "data": {
            "name": {
                "is_protected": True,
                "owner": "ffffffff",
                "source": "ffffffff",
                "value": "rfile01",
            },
            "query": {
                "_relation__owner": "ffffffff",
                "_relation__source": "ffffffff",
                "id": "qqqqqqqq",
            },
            "tags": [{"id": "t1t1t1t1"}, {"id": "t2t2t2t2"}],
            "template_path": {"value": "mytemplate.j2"},
            "template_repository": {
                "_relation__owner": "ffffffff",
                "_relation__source": "ffffffff",
                "id": "rrrrrrrr",
            },
        }
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_create_input_data_with_relationships_03(clients, rfile_schema, client_type):
    data = {
        "id": "aaaaaaaaaaaaaa",
        "name": {"value": "rfile01", "is_protected": True, "source": "ffffffff"},
        "template_path": {"value": "mytemplate.j2"},
        "query": {"id": "qqqqqqqq", "source": "ffffffff", "owner": "ffffffff", "is_protected": True},
        "template_repository": {"id": "rrrrrrrr", "source": "ffffffff", "owner": "ffffffff"},
        "tags": [{"id": "t1t1t1t1"}, "t2t2t2t2"],
    }
    if client_type == "standard":
        node = InfrahubNode(client=clients.standard, schema=rfile_schema, data=data)
    else:
        node = InfrahubNodeSync(client=clients.sync, schema=rfile_schema, data=data)

    assert node._generate_input_data()["data"] == {
        "data": {
            "name": {
                "is_protected": True,
                "source": "ffffffff",
                "value": "rfile01",
            },
            "query": {
                "_relation__is_protected": True,
                "_relation__owner": "ffffffff",
                "_relation__source": "ffffffff",
                "id": "qqqqqqqq",
            },
            "tags": [{"id": "t1t1t1t1"}, {"id": "t2t2t2t2"}],
            "template_path": {"value": "mytemplate.j2"},
            "template_repository": {
                "_relation__owner": "ffffffff",
                "_relation__source": "ffffffff",
                "id": "rrrrrrrr",
            },
        }
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_update_input_data__with_relationships_01(
    client, location_schema, location_data01, tag_schema, tag_blue_data, tag_green_data, client_type
):
    if client_type == "standard":
        location = InfrahubNode(client=client, schema=location_schema, data=location_data01)
        tag_green = InfrahubNode(client=client, schema=tag_schema, data=tag_green_data)
        tag_blue = InfrahubNode(client=client, schema=tag_schema, data=tag_blue_data)

    else:
        location = InfrahubNodeSync(client=client, schema=location_schema, data=location_data01)
        tag_green = InfrahubNodeSync(client=client, schema=tag_schema, data=tag_green_data)
        tag_blue = InfrahubNode(client=client, schema=tag_schema, data=tag_blue_data)

    location.primary_tag = tag_green_data
    location.tags.add(tag_green)
    location.tags.remove(tag_blue)

    assert location._generate_input_data()["data"] == {
        "data": {
            "name": {"is_protected": True, "is_visible": True, "value": "DFW"},
            "primary_tag": {"id": "gggggggg-gggg-gggg-gggg-gggggggggggg"},
            "tags": [{"id": "gggggggg-gggg-gggg-gggg-gggggggggggg"}],
            "type": {"is_protected": True, "is_visible": True, "value": "SITE"},
        },
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_update_input_data_with_relationships_02(client, location_schema, location_data02, client_type):
    if client_type == "standard":
        location = InfrahubNode(client=client, schema=location_schema, data=location_data02)

    else:
        location = InfrahubNodeSync(client=client, schema=location_schema, data=location_data02)

    assert location._generate_input_data()["data"] == {
        "data": {
            "name": {
                "is_protected": True,
                "is_visible": True,
                "source": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "value": "dfw1",
            },
            "primary_tag": {
                "_relation__is_protected": True,
                "_relation__is_visible": True,
                "_relation__source": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "id": "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr",
            },
            "tags": [
                {
                    "_relation__is_protected": True,
                    "_relation__is_visible": True,
                    "_relation__source": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                    "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                },
            ],
            "type": {
                "is_protected": True,
                "is_visible": True,
                "source": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "value": "SITE",
            },
        },
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_update_input_data_empty_relationship(
    client, location_schema, location_data01, tag_schema, tag_blue_data, client_type
):
    if client_type == "standard":
        location = InfrahubNode(client=client, schema=location_schema, data=location_data01)
        tag_blue = InfrahubNode(client=client, schema=tag_schema, data=tag_blue_data)

    else:
        location = InfrahubNodeSync(client=client, schema=location_schema, data=location_data01)
        tag_blue = InfrahubNode(client=client, schema=tag_schema, data=tag_blue_data)

    location.tags.remove(tag_blue)
    location.primary_tag = None

    assert location._generate_input_data()["data"] == {
        "data": {
            "name": {"is_protected": True, "is_visible": True, "value": "DFW"},
            # "primary_tag": None,
            "tags": [],
            "type": {"is_protected": True, "is_visible": True, "value": "SITE"},
        },
    }


@pytest.mark.parametrize("client_type", client_types)
async def test_node_get_relationship_from_store(
    client, location_schema, location_data01, tag_schema, tag_red_data, tag_blue_data, client_type
):
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=location_data01)
        tag_red = InfrahubNode(client=client, schema=tag_schema, data=tag_red_data)
        tag_blue = InfrahubNode(client=client, schema=tag_schema, data=tag_blue_data)

    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=location_data01)
        tag_red = InfrahubNodeSync(client=client, schema=tag_schema, data=tag_red_data)
        tag_blue = InfrahubNodeSync(client=client, schema=tag_schema, data=tag_blue_data)

    client.store.set(key=tag_red.id, node=tag_red)
    client.store.set(key=tag_blue.id, node=tag_blue)

    assert node.primary_tag.peer == tag_red
    assert node.primary_tag.get() == tag_red

    assert node.tags[0].peer == tag_blue
    assert [tag.peer for tag in node.tags] == [tag_blue]


@pytest.mark.parametrize("client_type", client_types)
async def test_node_get_relationship_not_in_store(client, location_schema, location_data01, client_type):
    if client_type == "standard":
        node = InfrahubNode(client=client, schema=location_schema, data=location_data01)

    else:
        node = InfrahubNodeSync(client=client, schema=location_schema, data=location_data01)

    with pytest.raises(NodeNotFound):
        node.primary_tag.peer  # pylint: disable=pointless-statement

    with pytest.raises(NodeNotFound):
        node.tags[0].peer  # pylint: disable=pointless-statement


@pytest.mark.parametrize("client_type", client_types)
async def test_node_fetch_relationship(
    httpx_mock: HTTPXMock,
    mock_schema_query_01,
    clients,
    location_schema,
    location_data01,
    tag_schema,
    tag_red_data,
    tag_blue_data,
    client_type,
):  # pylint: disable=unused-argument
    response1 = {
        "data": {
            "tag": [
                tag_red_data,
            ]
        }
    }

    httpx_mock.add_response(method="POST", json=response1, match_headers={"X-Infrahub-Tracker": "query-tag-get"})

    response2 = {
        "data": {
            "tag": [
                tag_blue_data,
            ]
        }
    }

    httpx_mock.add_response(method="POST", json=response2, match_headers={"X-Infrahub-Tracker": "query-tag-get"})

    if client_type == "standard":
        node = InfrahubNode(client=clients.standard, schema=location_schema, data=location_data01)
        await node.primary_tag.fetch()  # type: ignore[attr-defined]
        await node.tags.fetch()  # type: ignore[attr-defined]
    else:
        node = InfrahubNodeSync(client=clients.sync, schema=location_schema, data=location_data01)  # type: ignore[assignment]
        node.primary_tag.fetch()  # type: ignore[attr-defined]
        node.tags.fetch()  # type: ignore[attr-defined]

    assert isinstance(node.primary_tag.peer, InfrahubNodeBase)  # type: ignore[attr-defined]
    assert isinstance(node.tags[0].peer, InfrahubNodeBase)  # type: ignore[attr-defined]
