from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

import infrahub.config as config
from infrahub.core.definitions import Brancher
from infrahub.exceptions import BranchNotFound, DataTypeNotFound, Error
from infrahub.lock import registry as lock_registry

if TYPE_CHECKING:
    import graphene
    from neo4j import AsyncSession

    from infrahub.core.attribute import BaseAttribute
    from infrahub.core.branch import Branch
    from infrahub.core.manager import SchemaManager
    from infrahub.core.schema import GenericSchema, GroupSchema, NodeSchema
    from infrahub.graphql.mutations import BaseAttributeInput
    from infrahub.graphql.types import InfrahubObject
    from infrahub.types import InfrahubDataType


@dataclass
class Registry:
    id: Optional[str] = None
    attribute: Dict[str, BaseAttribute] = field(default_factory=dict)
    branch: dict = field(default_factory=dict)
    node: dict = field(default_factory=dict)
    schema: Optional[SchemaManager] = None
    default_graphql_type: Dict[str, InfrahubObject] = field(default_factory=dict)
    graphql_type: dict = field(default_factory=lambda: defaultdict(dict))
    data_type: Dict[str, InfrahubDataType] = field(default_factory=dict)
    input_type: Dict[str, BaseAttributeInput] = field(default_factory=dict)
    account: dict = field(default_factory=dict)
    account_id: dict = field(default_factory=dict)
    node_group: dict = field(default_factory=dict)
    attr_group: dict = field(default_factory=dict)
    branch_object: Optional[Brancher] = None

    def set_item(self, kind: str, name: str, item, branch: Optional[str] = None) -> bool:
        branch = branch or config.SETTINGS.main.default_branch
        getattr(self, kind)[branch][name] = item
        return True

    def has_item(self, kind: str, name: str, branch=None) -> bool:
        try:
            self.get_item(kind=kind, name=name, branch=branch)
            return True
        except ValueError:
            return False

    def get_item(self, kind: str, name: str, branch: Optional[Union[Branch, str]] = None):
        branch = get_branch_from_registry(branch=branch)

        attr = getattr(self, kind)

        if branch.name in attr and name in attr[branch.name]:
            return attr[branch.name][name]

        default_branch = config.SETTINGS.main.default_branch
        if name in attr[default_branch]:
            return attr[default_branch][name]

        raise ValueError(f"Unable to find the {kind} {name} for the branch {branch.name} in the registry")

    def get_all_item(self, kind: str, branch: Optional[Union[Branch, str]] = None) -> dict:
        """Return all the nodes in the schema for a given branch.
        The current implementation is a bit simplistic, will need to re-evaluate."""
        branch = get_branch_from_registry(branch=branch)

        attr = getattr(self, kind)

        if branch.name in attr:
            return attr[branch.name]

        default_branch = config.SETTINGS.main.default_branch
        return attr[default_branch]

    def set_schema(
        self, name: str, schema: Union[NodeSchema, GenericSchema, GroupSchema], branch: Optional[str] = None
    ) -> int:
        return self.schema.set(name=name, schema=schema, branch=branch)

    def has_schema(self, name: str, branch: Optional[Union[Branch, str]] = None) -> bool:
        return self.schema.has(name=name, branch=branch)

    def get_schema(
        self, name: str, branch: Optional[Union[Branch, str]] = None
    ) -> Union[NodeSchema, GenericSchema, GroupSchema]:
        return self.schema.get(name=name, branch=branch)

    def get_data_type(
        self,
        name: str,
    ) -> InfrahubDataType:
        if name not in self.data_type:
            raise DataTypeNotFound(name=name)
        return self.data_type[name]

    def get_full_schema(
        self, branch: Optional[Union[Branch, str]] = None
    ) -> Dict[str, Union[NodeSchema, GenericSchema, GroupSchema]]:
        """Return all the nodes in the schema for a given branch."""
        return self.schema.get_full(branch=branch)

    def set_graphql_type(
        self,
        name: str,
        graphql_type: Union[Type[InfrahubObject], Type[graphene.Interface], Type[graphene.ObjectType]],
        branch: Optional[str] = None,
    ) -> bool:
        return self.set_item(kind="graphql_type", name=name, item=graphql_type, branch=branch)

    def has_graphql_type(self, name: str, branch: Optional[Union[Branch, str]] = None) -> bool:
        return self.has_item(kind="graphql_type", name=name, branch=branch)

    def get_graphql_type(self, name: str, branch: Optional[Union[Branch, str]] = None) -> InfrahubObject:
        return self.get_item(kind="graphql_type", name=name, branch=branch)

    def get_all_graphql_type(self, branch: Optional[Union[Branch, str]] = None) -> Dict[str, InfrahubObject]:
        """Return all the graphql_type for a given branch."""
        return self.get_all_item(kind="graphql_type", branch=branch)

    def delete_all(self):
        self.branch = {}
        self.node = {}
        self.schema = None
        self.graphql_type = defaultdict(dict)
        self.account = {}
        self.account_id = {}
        self.node_group = {}
        self.attr_group = {}
        self.data_type = {}
        self.attribute = {}
        self.input_type = {}

    def get_branch_from_registry(self, branch: Optional[Union[Branch, str]] = None) -> Branch:
        """Return a branch object from the registry based on its name.

        Args:
            branch (Optional[Union[Branch, str]]): Branch object or name of a branch

        Raises:
            BranchNotFound:

        Returns:
            Branch: A Branch Object
        """

        if self.branch_object and branch:
            if self.branch_object.isinstance(branch) and not isinstance(branch, str):
                return branch

        # if the name of the branch is not defined or not a string we used the default branch name
        if not branch or not isinstance(branch, str):
            branch = config.SETTINGS.main.default_branch

        # Try to get it from the registry
        #   if not present in the registry and if a session has been provided get it from the database directly
        #   and update the registry
        if branch in self.branch:
            return self.branch[branch]

        raise BranchNotFound(identifier=branch)

    async def get_branch(self, branch: Optional[Union[Branch, str]], session: Optional[AsyncSession]) -> Branch:
        """Return a branch object based on its name.

        First the function will check in the registry
        if the Branch is not present, and if a session object has been provided
            it will attempt to retrieve the branch and its schema from the database.

        Args:
            branch (Optional[Union[Branch, str]]): Branch object or name of a branch
            session (Optional[AsyncSession], optional): AsyncSession to connect to the database. Defaults to None.

        Raises:
            BranchNotFound:

        Returns:
            Branch: A Branch Object
        """

        if self.branch_object and branch:
            if self.branch_object.isinstance(branch) and not isinstance(branch, str):
                return branch

        if not branch or not isinstance(branch, str):
            branch = config.SETTINGS.main.default_branch

        try:
            return self.get_branch_from_registry(branch=branch)
        except BranchNotFound:
            if not session:
                raise

        if not self.branch_object:
            raise Error("Branch object not initialized")

        async with lock_registry.get_branch_schema_update():
            obj = await self.branch_object.get_by_name(name=branch, session=session)
            registry.branch[branch] = obj

            # Pull the schema for this branch
            await registry.schema.load_schema_from_db(session=session, branch=obj)

        return obj


registry = Registry()

get_branch_from_registry = registry.get_branch_from_registry
get_branch = registry.get_branch
