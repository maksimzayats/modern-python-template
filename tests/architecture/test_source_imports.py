import ast

from tests.architecture._source import SOURCE_ROOT, SourceModule, iter_imports


def test_import_from_records_fully_qualified_alias_modules() -> None:
    module = _source_module("from fastapi_template.core.user import delivery, dtos\n")

    import_names = {import_reference.module_name for import_reference in iter_imports(module)}

    assert {
        "fastapi_template.core.user",
        "fastapi_template.core.user.delivery",
        "fastapi_template.core.user.dtos",
    } <= import_names


def test_import_from_preserves_type_checking_alias_metadata() -> None:
    module = _source_module(
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from fastapi_template.core.user import infrastructure\n",
    )

    import_references = {
        import_reference.module_name: import_reference.is_type_checking
        for import_reference in iter_imports(module)
    }

    assert import_references["fastapi_template.core.user.infrastructure"] is True


def _source_module(source: str) -> SourceModule:
    return SourceModule(
        path=SOURCE_ROOT / "core" / "example.py",
        tree=ast.parse(source),
    )
