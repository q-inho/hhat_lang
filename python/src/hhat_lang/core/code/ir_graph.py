from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any

from hhat_lang.core.code.core import BaseIR
from hhat_lang.core.data.core import Symbol, CompositeSymbol


class IRKey:
    """IR key class to handle the nodes for the IRGraph"""

    _key: int

    def __init__(self, ir: BaseIR):
        if isinstance(ir, BaseIR):
            self._key = hash(ir)

        raise ValueError("ir must be of type BaseIR")

    @property
    def key(self) -> Any:
        return self._key

    @classmethod
    def get_key(cls, ir: BaseIR) -> IRKey:
        return IRKey(ir)

    def __hash__(self) -> int:
        return self._key

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IRKey):
            return hash(self) == hash(other)

        return False


class IRNode(OrderedDict):
    """
    Define the IR graph node. It is a special case for ``OrderedDict``, where it
    accepts only ``IRKey`` for the keys and ``BaseIR`` for the values.
    """

    def __init__(self, other=(), /):
        for k in other:
            if len(k) == 2:
                if isinstance(k[0], IRKey) and isinstance(k[1], BaseIR):
                    continue

            raise ValueError("IR node must have a key as IRKey and value as BaseIR")

        super().__init__(other)

    def update(self, m: dict | OrderedDict, /, **_kwargs: Any) -> None:
        """
        Update IR node data with ``m`` argument. Kwargs are ignored.

        Args:
            m: the dictionary or ``OrderedDict`` containing data to be updated into the IR node
            **_kwargs: just to keep the parent function template; not used.
        """

        if len(_kwargs) > 0:
            # this is enforced because arg name at **kwargs can only be of str type,
            # but we need arg name to be of IRKey type
            raise ValueError("do not use **kwargs for IR node")

        if all(isinstance(k, IRKey) and isinstance(v, BaseIR) for k, v in m.items()):
            super().update(m)

        else:
            raise ValueError(
                "cannot update IR node with data other than IRKey for keys and BaseIR for value"
            )

    def pop(self, key: IRKey, default: Any = None) -> BaseIR:
        return super().pop(key, default=default or object())

    def __setitem__(self, key: IRKey, value: BaseIR) -> None:
        if isinstance(key, IRKey) and isinstance(value, BaseIR):
            super().__setitem__(key, value)

        else:
            raise ValueError(
                "to set key and value on IR node, IRKey and BaseIR data are needed, respectively"
            )


class IREdge:
    """Define the IR graph edge"""

    _data: OrderedDict[IRKey, dict[Symbol | CompositeSymbol, IRKey]]

    def __init__(self):
        self._data = OrderedDict()

    def add_node(self, node: IRKey) -> None:
        if isinstance(node, IRKey) and node not in self._data:
            self._data.update({node: dict()})

        else:
            raise ValueError(
                f"node {node} ({type(node)}) already in IR edge or wrong type (should be IRKey)"
            )

    def add_links(self, *refs: Symbol | CompositeSymbol, node: IRKey, ref_node: IRKey) -> None:
        """
        Link each reference in ``*refs`` from its reference node ``ref_node`` with the
        reference importer ``node``.

        Args:
            *refs: reference as types or function name (``Symbol``, ``CompositeSymbol``)
            node: the IR block that needs the references to properly import their values
            ref_node: the IR block that contains the references in ``*refs``
        """

        if (
            all(isinstance(k, Symbol | CompositeSymbol) for k in refs)
            and isinstance(node, IRKey)
            and isinstance(ref_node, IRKey)
        ):
            if node in self._data and ref_node in self._data:
                # refs should contain unique values inside a node,
                # so they should not be assigned twice
                self._data[node].update({k: ref_node for k in refs})

        else:
            raise ValueError(
                "IR edge linking references (Symbol, CompositeSymbol) from ref_node"
                " (IRKey) to the node (IRKey); got wrong types"
            )

    def get_node(self, node: IRKey) -> dict[Symbol | CompositeSymbol, IRKey]:
        """Get the dictionary of references for all its imported types and functions"""

        return self._data[node]

    def get_ref(self, node: IRKey, ref: Symbol | CompositeSymbol) -> IRKey:
        """Get the IR key from a given reference inside an importer node"""

        return self._data[node][ref]

    def update_node(self, cur_node: IRKey, new_node: IRKey) -> None:
        """Update a current node IR key to a new one"""

        new_data: OrderedDict[IRKey, dict[Symbol | CompositeSymbol, IRKey]] = OrderedDict()

        for k0, v0 in self._data.items():

            cur_k0 = new_node if k0 == cur_node else k0
            new_data.update(
                {
                    cur_k0: {
                        k1: new_node if v1 == cur_node else v1
                        for k1, v1 in v0.items()
                    }
                }
            )

        self._data = deepcopy(new_data)
        del new_data

    def remove_node(self, node: IRKey) -> None:
        self._data.pop(node)
        new_data: OrderedDict[IRKey, dict[Symbol | CompositeSymbol, IRKey]] = OrderedDict()

        for k, v in self._data.items():
            for p, q in v.items():
                if q != node:
                    new_data[k].update({p:q})

        self._data = deepcopy(new_data)
        del new_data


class IRGraph:
    """
    Graph to hold IR objects as nodes and their relationship as edges.
    It is useful when a certain file imports others.
    """

    _nodes: IRNode
    _edges: IREdge

    def __init__(self):
        self._nodes = IRNode()
        self._edges = IREdge()

    @property
    def nodes(self) -> IRNode:
        """Last node in a program will always be its 'main' file."""
        return self._nodes

    @property
    def edges(self) -> IREdge:
        """Edges between t"""
        return self._edges

    def add_node(self, node: BaseIR) -> IRKey:
        key = IRKey(node)

        if key not in self._nodes:
            self._nodes.update({key: node})
            self._edges.add_node(key)
            return key

        raise ValueError(f"IR graph node inside IR manager must be unique; got {key}")

    def add_edge(self, *refs: Symbol | CompositeSymbol, node_key: IRKey, link_key: IRKey) -> None:
        """
        To add a new edge, both the node and the links must exist, so there should be
        a ``IRKey`` associated with them.

        Args:
            *refs: the references for types or functions from the ``link_key``
            node_key: the ``IRKey`` of the node (IR code) to import some instance from
                the linked IR code
            link_key: the ``IRKey`` of the node to be imported some instance
        """

        if isinstance(node_key, IRKey) and isinstance(link_key, IRKey):
            self._edges.add_links(*refs, node=node_key, ref_node=link_key)

        else:
            raise ValueError(f"cannot find the IR code node ({node_key})")

    def update_node(self, cur_node_key: IRKey, new_node: BaseIR):
        """
        Update a node (IR code) from a given current node key (``IRKey``)

        Args:
            cur_node_key:
            new_node:

        Returns:

        """

        cur_ir: BaseIR = self._nodes.pop(cur_node_key, None)

        if cur_ir is not None:
            new_key = self.add_node(new_node)
            self.update_edges(cur_node_key, new_key)

        else:
            raise ValueError(f"the IR key to be update ({cur_node_key}) was not found")

    def update_edges(self, old_key: IRKey, new_key: IRKey) -> None:
        """
        When a node (IR code) is updated, it triggers a change in all the edges
        that hold any relation with the previous node.
        """

        if new_key in self._edges:
            raise ValueError("IR graph new key already exists")

        self._edges.update_node(old_key, new_key)
