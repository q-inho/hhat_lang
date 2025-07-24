from __future__ import annotations

from typing import Any

from hhat_lang.core.code.core import BaseIR
from hhat_lang.core.execution.abstract_base import BaseIRManager
from hhat_lang.core.code.ir_graph import IRGraph, IRKey
from hhat_lang.dialects.heather.code.simple_ir_builder.new_ir import IR


class IRManager(BaseIRManager):
    """Handle IR codes for Heather dialect through ``IRGraph`` instance"""

    def __init__(self):
        self._graph = IRGraph()

    def add_ir(self, ir: IR) -> None:
        """
        Add a single IR

        Args:
            ir: the ``IR`` instance to be added to the manager
        """

        self._graph.add_node(ir)
        self.add_to_group(ir)

    def link_ir(self, ir_importing: BaseIR, ir_imported: BaseIR, **kwargs: Any) -> None:
        """
        Link two IRs, where one is the importer (importing IR) and the other is the imported IR.

        Args:
            ir_importing: the ``IR`` instance that will import data from another ``IR`` instance
            ir_imported: the imported ``IR``, which contains the data to be imported
            **kwargs: Extra data if needed
        """

        importing = IRKey.get_key(ir_importing)
        imported = IRKey.get_key(ir_imported)
        self._graph.add_edge(importing, imported)

    def link_many_ir(self, *irs_imported: BaseIR, ir_importing: BaseIR) -> None:
        """
        Link many ``IR`` (importing data from) to a single importer ``IR`` (importer of the data).

        Args:
            *irs_imported: list of imported ``IR`` instances, which contain the data to be imported
            ir_importing: the ``IR`` instance that will import data from those ``IR`` instances
        """

        importing = IRKey.get_key(ir_importing)
        imported = set(IRKey.get_key(k) for k in irs_imported)
        self._graph.add_edges(importing, imported)

    def update_ir(self, prev_ir: IR, new_ir: IR) -> None:
        """
        Update a current ``IR`` instance for a new ``IR`` instance. It will replace the current
        one on the IR graph as well, from its node position to all the current's relationships.

        Args:
            prev_ir: (the current, or to be) previous ``IR`` instance
            new_ir: the new ``IR`` instance, to replace the current ``IR`` instance
        """

        prev_key = IRKey.get_key(prev_ir)
        self._graph.update_node(prev_key, new_ir)

    def add_to_group(self, ir: BaseIR) -> Any:
        key = IRKey(ir)

        if ir.types is not None:
            types = set(ir.types.table.keys())
            self._types_graph[key] = types

        if ir.fns is not None:
            fns = set(ir.fns.table.keys())
            self._fns_graph[key] = fns
