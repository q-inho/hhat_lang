from __future__ import annotations

from arpeggio import NonTerminal, PTNodeVisitor, SemanticActionResults, Terminal

from hhat_lang.core.code.ast import AST
from hhat_lang.dialects.heather.code.ast import (
    ArgTypePair,
    ArgValuePair,
    Assign,
    Body,
    Call,
    CallArgs,
    CallWithArgsBodyOptions,
    CallWithBody,
    CallWithBodyOptions,
    Cast,
    CompositeId,
    CompositeIdWithClosure,
    CompositeLiteral,
    Declare,
    DeclareAssign,
    EnumTypeMember,
    Expr,
    FnArgs,
    FnDef,
    FnImport,
    Id,
    Imports,
    InsideOption,
    Literal,
    Main,
    ManyTypeImport,
    ModifiedId,
    Modifier,
    OnlyValue,
    Program,
    Return,
    SingleTypeMember,
    TypeDef,
    TypeImport,
    TypeMember,
)


class ParserVisitor(PTNodeVisitor):
    def visit_program(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        imports: Imports | None = None
        types: tuple | tuple[TypeDef] = ()
        fns: tuple | tuple[FnDef] = ()
        main: Main | None = Main()

        for k in child:
            match k:
                case Imports():
                    imports = k

                case TypeDef():
                    types += (k,)

                case FnDef():
                    fns += (k,)

                case Main():
                    main = k

                case _:
                    raise ValueError(f"something went wrong! {k} ({type(k)})")

        return Program(
            main=main,
            imports=imports,
            types=types or None,
            fns=fns or None,
        )

    def visit_type_file(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if all(isinstance(k, TypeDef) for k in child):
            return child[0]

        raise ValueError("types must be TypeDef instance.")

    def visit_typesingle(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if isinstance(child[0], Id) and isinstance(child[1], Id):
            return TypeDef(
                SingleTypeMember(child[1]), type_name=child[0], type_ds=Id("single")
            )

        raise ValueError("type single wrong value")

    def visit_typemember(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if isinstance(child[0], Id) and isinstance(
            child[1], Id | CompositeId | ModifiedId
        ):
            return TypeMember(member_name=child[0], member_type=child[1])

        raise ValueError("type single wrong value")

    def visit_typestruct(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        name, *members = child
        return TypeDef(*members, type_name=name, type_ds=Id("struct"))

    def visit_typeenum(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        name, *members = child
        return TypeDef(*members, type_name=name, type_ds=Id("enum"))

    def visit_typeunion(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        raise NotImplementedError()

    def visit_enummember(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return EnumTypeMember(member_name=child[0])

    def visit_fns(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if len(child) == 4:
            return FnDef(
                fn_name=child[0], fn_type=child[2], args=child[1], body=child[-1]
            )

        return FnDef(
            fn_name=child[0], fn_type=Id("null"), args=child[1], body=child[-1]
        )

    def visit_fnargs(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return FnArgs(*child)

    def visit_argtype(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return ArgTypePair(arg_name=child[0], arg_type=child[1])

    def visit_fn_body(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Body(*child)

    def visit_body(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Body(*child)

    def visit_declare(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Declare(var_name=child[0], var_type=child[1])

    def visit_assign(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Assign(var_name=child[0], expr=child[1])

    def visit_declareassign(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return DeclareAssign(var_name=child[0], var_type=child[1], expr=child[2])

    def visit_return(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Return(*child)

    def visit_expr(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Expr(*child)

    def visit_cast(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Cast(name=child[0], cast_to=child[1])

    def visit_call(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        args = CallArgs(*[k for k in child[1:]])
        return Call(caller=child[0], args=args)

    def visit_trait_id(self, node: NonTerminal, child: SemanticActionResults) -> AST:
        raise NotImplementedError()

    def visit_args(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return child[0]

    def visit_callargs(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return ArgValuePair(arg=child[0], value=child[1])

    def visit_valonly(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return OnlyValue(value=child[0])

    def visit_option(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return InsideOption(option=child[0], body=child[1])

    def visit_callwithbody(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return CallWithBody(caller=child[0], args=child[1], body=child[-1])

    def visit_callwithbodyoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> AST:
        return CallWithBodyOptions(*child[2:], caller=child[0], args=child[1])

    def visit_callwithargsbodyoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> AST:
        return CallWithArgsBodyOptions(*child[1:], caller=child[0])

    def visit_id_composite_value(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> AST:
        """Get the value to form the type member for arguments and type definitions"""
        return child[0]

    def visit_imports(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        """
        Take the tuple of optional type imports and function imports and place
        inside the `Imports` object, to be properly handled later by the type and
        function checkers and importers.
        """

        type_import: tuple | tuple[TypeImport] = ()
        fn_import: tuple | tuple[FnImport] = ()

        for k in child:
            match k:
                case TypeImport():
                    type_import += (k,)

                case FnImport():
                    fn_import += (k,)

        return Imports(type_import=type_import, fn_import=fn_import)

    def visit_typeimport(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        types: tuple | tuple[Id | CompositeId | CompositeIdWithClosure] = ()

        for k in child:
            match k:
                case ManyTypeImport():
                    types += tuple(p for p in k)

                case Id() | CompositeId() | CompositeIdWithClosure():
                    types += (k,)

                case _:
                    raise ValueError(
                        f"something went wrong when defining type import: {k} ({type(k)})"
                    )

        return TypeImport(type_list=types)

    def visit_fnimport(
        self, _: NonTerminal | None, child: SemanticActionResults
    ) -> AST:
        fns: tuple | tuple[Id | CompositeId | CompositeIdWithClosure] = ()

        for k in child:
            match k:
                case Id() | CompositeId() | CompositeIdWithClosure():
                    fns += (k,)

                case _:
                    raise ValueError("something went wrong when defining type import.")

        return FnImport(fn_list=fns)

    def visit_single_import(
        self, _: NonTerminal | Terminal, child: SemanticActionResults
    ) -> AST:
        """simply return the import AST"""

        return tuple(k for k in child)[0]

    def visit_many_import(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return ManyTypeImport(*child)

    def visit_main(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        return Main(*child)

    def visit_composite_id_with_closure(
        self, _: NonTerminal | Terminal, child: SemanticActionResults
    ) -> AST:
        """
        Get an Id and its dependencies, ex:

        ```python
        math.{add sub mul div}
        ```

        """

        name, *deps = tuple(k for k in child)
        return CompositeIdWithClosure(*deps, name=name)

    def visit_id(self, _: NonTerminal | Terminal, child: SemanticActionResults) -> AST:
        if len(child) == 2 and isinstance(child[1], Modifier):
            return ModifiedId(name=child[0], modifier=child[1])

        return child[0]

    def visit_modifier(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if all(isinstance(k, ArgValuePair) for k in child):
            return Modifier(*child)

        raise ValueError(
            f"Modifier should have had ArgValuePair, got {set(type(k) for k in child)} instead."
        )

    def visit_array(self, node: NonTerminal, child: SemanticActionResults) -> AST:
        raise NotImplementedError()

    def visit_composite_id(self, _: NonTerminal, child: SemanticActionResults) -> AST:
        if all(isinstance(k, Id) for k in child):
            return CompositeId(*child)

        raise ValueError(
            f"CompositeId must contain Id values; got {set(type(k) for k in child)} instead."
        )

    def visit_simple_id(self, node: Terminal, _: SemanticActionResults) -> AST:
        return Id(node.value)

    def visit_literal(self, _: Terminal, child: SemanticActionResults) -> AST:
        return child[0]

    def visit_null(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="null")

    def visit_bool(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="bool")

    def visit_str(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="str")

    def visit_int(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="int")

    def visit_float(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="float")

    def visit_imag(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="imag")

    def visit_complex(self, node: Terminal, child: SemanticActionResults) -> AST:
        return CompositeLiteral(*child, value_type="complex")

    def visit_q__bool(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="@bool")

    def visit_q__int(self, node: Terminal, _: None) -> AST:
        return Literal(value=node.value, value_type="@int")
