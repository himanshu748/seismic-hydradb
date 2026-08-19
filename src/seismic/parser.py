"""Conservative Python AST extraction for Seismic repository snapshots."""

from __future__ import annotations

import ast
import hashlib
import re
import sys
import tomllib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from seismic.config import SeismicConfig
from seismic.gitmeta import (
    collect_last_touch,
    git_head,
    is_dirty,
    list_visible_python_files,
    load_codeowners,
    match_owner,
)
from seismic.identity import relationship_id, stable_id
from seismic.identity import repo_key as build_repo_key
from seismic.models import (
    ArtifactKind,
    ArtifactRecord,
    RelationshipKind,
    RelationshipRecord,
    RepositoryGraph,
)

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "output",
    "site-packages",
    "vendor",
    "venv",
}
_PACKAGE_NAME = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*(.*)$")
_EXACT_VERSION = re.compile(r"==\s*([A-Za-z0-9_.+!-]+)")


class RepositoryParseError(RuntimeError):
    """Raised when a repository cannot be parsed within configured safety limits."""


@dataclass(slots=True)
class _SourceFile:
    path: Path
    relative: str
    content: str
    digest: str
    tree: ast.Module
    module: str = ""
    is_test: bool = False
    imports: list[ast.Import | ast.ImportFrom] = field(default_factory=list)


@dataclass(slots=True)
class _Definition:
    source: _SourceFile
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    qualified_name: str
    artifact: ArtifactRecord | None = None


@dataclass(slots=True)
class _ModuleBindings:
    module_aliases: dict[str, str] = field(default_factory=dict)
    symbol_aliases: dict[str, tuple[str, str]] = field(default_factory=dict)


class RepositoryParser:
    """Build a bounded, snapshot-scoped code graph from one safe Python checkout."""

    def __init__(self, config: SeismicConfig) -> None:
        self.config = config

    def parse(self, repo_path: str, explicit_repo_key: str | None = None) -> RepositoryGraph:
        """Parse one repository without writing anything to HydraDB."""

        root = self.config.validate_repo_path(repo_path)
        sources, skipped, warnings = self._read_sources(root)
        commit_sha = git_head(root)
        content_fingerprint = _graph_input_fingerprint(root, sources)
        snapshot_version = f"worktree-{content_fingerprint[:16]}" if is_dirty(root) else commit_sha
        repository_key = (
            _clean_repo_key(explicit_repo_key)
            if explicit_repo_key is not None
            else build_repo_key(root.name, str(root))
        )
        snapshot_key = f"{repository_key}@{snapshot_version}"
        graph = RepositoryGraph(
            repo_key=repository_key,
            snapshot_key=snapshot_key,
            commit_sha=commit_sha,
            root_name=root.name,
            skipped_files=skipped,
            warnings=warnings,
        )
        self._assign_modules(sources)
        touch = collect_last_touch(root, {source.relative for source in sources})
        owner_file, owner_rules = load_codeowners(root)
        artifacts_by_module: dict[str, ArtifactRecord] = {}
        definitions: list[_Definition] = []
        definitions_by_module: dict[str, dict[str, ArtifactRecord]] = defaultdict(dict)

        for source in sources:
            last_touch = touch.get(source.relative)
            ownership = match_owner(source.relative, owner_file, owner_rules)
            file_artifact = _artifact(
                repository_key,
                snapshot_key,
                logical_key=source.relative,
                kind="file",
                path=source.relative,
                qualified_name=source.module,
                language="python",
                line_start=1,
                line_end=max(1, source.content.count("\n") + 1),
                content_hash=source.digest,
                last_author="" if last_touch is None else last_touch.author,
                last_modified="" if last_touch is None else last_touch.timestamp,
                owner=ownership.owner,
                owner_source=ownership.source,
                text=source.content[:20_000],
            )
            graph.artifacts.append(file_artifact)
            artifacts_by_module[source.module] = file_artifact
            for definition in _collect_definitions(source):
                kind: ArtifactKind
                if source.is_test or definition.qualified_name.split(".")[-1].startswith("test"):
                    kind = "test"
                elif isinstance(definition.node, ast.ClassDef):
                    kind = "class"
                else:
                    kind = "function"
                symbol_logical_key = f"{source.relative}::{definition.qualified_name}"
                symbol_artifact = _artifact(
                    repository_key,
                    snapshot_key,
                    logical_key=symbol_logical_key,
                    kind=kind,
                    path=source.relative,
                    qualified_name=definition.qualified_name,
                    language="python",
                    line_start=int(getattr(definition.node, "lineno", 0)),
                    line_end=int(getattr(definition.node, "end_lineno", 0) or 0),
                    content_hash=source.digest,
                    last_author=file_artifact.last_author,
                    last_modified=file_artifact.last_modified,
                    owner=file_artifact.owner,
                    owner_source=file_artifact.owner_source,
                    text=_definition_text(source.content, definition.node),
                )
                definition.artifact = symbol_artifact
                graph.artifacts.append(symbol_artifact)
                definitions.append(definition)
                definitions_by_module[source.module][definition.qualified_name] = symbol_artifact
                _add_edge(
                    graph,
                    snapshot_key,
                    "PART_OF",
                    symbol_artifact.id,
                    file_artifact.id,
                    first_evidence_line=symbol_artifact.line_start,
                )

        bindings: dict[str, _ModuleBindings] = {}
        external_imports: list[tuple[ArtifactRecord, str, int]] = []
        for source in sources:
            source_artifact = artifacts_by_module[source.module]
            module_bindings = _ModuleBindings()
            bindings[source.module] = module_bindings
            for import_node in source.imports:
                resolved_modules = _resolve_import_node(source, import_node)
                for bound_name, imported_module, imported_symbol in resolved_modules:
                    module_candidate = (
                        f"{imported_module}.{imported_symbol}"
                        if imported_module and imported_symbol
                        else imported_symbol
                    )
                    if module_candidate in artifacts_by_module:
                        imported_module = module_candidate
                        imported_symbol = ""
                    target_file = _resolve_module_artifact(imported_module, artifacts_by_module)
                    if target_file is not None:
                        _add_edge(
                            graph,
                            snapshot_key,
                            "IMPORTS",
                            source_artifact.id,
                            target_file.id,
                            first_evidence_line=int(getattr(import_node, "lineno", 0)),
                        )
                    elif imported_module.split(".", 1)[0] not in sys.stdlib_module_names:
                        external_imports.append(
                            (
                                source_artifact,
                                imported_module.split(".", 1)[0],
                                int(getattr(import_node, "lineno", 0)),
                            )
                        )
                        graph.unresolved_imports += 1
                    if imported_symbol:
                        module_bindings.symbol_aliases[bound_name] = (
                            imported_module,
                            imported_symbol,
                        )
                    else:
                        module_bindings.module_aliases[bound_name] = imported_module

        for definition in definitions:
            if definition.artifact is None or isinstance(definition.node, ast.ClassDef):
                continue
            calls = _collect_calls(definition.node)
            for call in calls:
                resolved = _resolve_call(
                    call,
                    definition,
                    bindings[definition.source.module],
                    definitions_by_module,
                )
                if resolved is None:
                    graph.unresolved_calls += 1
                    continue
                edge_kind: RelationshipKind = (
                    "TESTS"
                    if definition.artifact.kind == "test" and resolved.kind != "test"
                    else "CALLS"
                )
                _add_edge(
                    graph,
                    snapshot_key,
                    edge_kind,
                    definition.artifact.id,
                    resolved.id,
                    first_evidence_line=int(getattr(call, "lineno", 0)),
                    confidence=0.95,
                )

        packages = self._add_packages(root, graph, repository_key, snapshot_key)
        packages_by_name = {
            artifact.qualified_name.casefold().replace("-", "_"): artifact for artifact in packages
        }
        for source_artifact, import_root, line in external_imports:
            package = packages_by_name.get(import_root.casefold().replace("-", "_"))
            if package is None:
                continue
            _add_edge(
                graph,
                snapshot_key,
                "DEPENDS_ON",
                source_artifact.id,
                package.id,
                first_evidence_line=line,
                confidence=0.8,
                source="manifest+import",
            )

        self._add_entrypoints(root, graph, repository_key, snapshot_key, definitions_by_module)
        _deduplicate_edges(graph)
        if len(graph.artifacts) > self.config.max_artifacts:
            raise RepositoryParseError(
                f"repository produced {len(graph.artifacts)} artifacts; "
                f"limit is {self.config.max_artifacts}"
            )
        if len(graph.relationships) > self.config.max_relationships:
            raise RepositoryParseError(
                "repository produced "
                f"{len(graph.relationships)} relationships; "
                f"limit is {self.config.max_relationships}"
            )
        return graph

    def _read_sources(self, root: Path) -> tuple[list[_SourceFile], int, list[str]]:
        sources: list[_SourceFile] = []
        skipped = 0
        warnings: list[str] = []
        for path in list_visible_python_files(root):
            if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
                continue
            if path.is_symlink():
                skipped += 1
                continue
            if len(sources) >= self.config.max_files:
                raise RepositoryParseError(
                    f"repository exceeds SEISMIC_MAX_FILES={self.config.max_files}"
                )
            try:
                size = path.stat().st_size
            except OSError as exc:
                skipped += 1
                warnings.append(f"Could not stat {path.relative_to(root)}: {exc}")
                continue
            if size > self.config.max_file_bytes:
                skipped += 1
                warnings.append(f"Skipped oversized file {path.relative_to(root)} ({size} bytes)")
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            relative = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(content, filename=relative)
            except SyntaxError as exc:
                skipped += 1
                warnings.append(f"Skipped unparsable Python file {relative}: {exc.msg}")
                continue
            sources.append(
                _SourceFile(
                    path=path,
                    relative=relative,
                    content=content,
                    digest=hashlib.sha256(content.encode()).hexdigest(),
                    tree=tree,
                    is_test=_is_test_path(relative),
                    imports=[
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, (ast.Import, ast.ImportFrom))
                    ],
                )
            )
        return sources, skipped, warnings

    def _assign_modules(self, sources: list[_SourceFile]) -> dict[str, _SourceFile]:
        result: dict[str, _SourceFile] = {}
        for source in sources:
            candidates = _module_candidates(source.relative)
            source.module = candidates[0]
            for candidate in candidates:
                result.setdefault(candidate, source)
        return result

    def _add_packages(
        self,
        root: Path,
        graph: RepositoryGraph,
        repository_key: str,
        snapshot_key: str,
    ) -> list[ArtifactRecord]:
        packages: list[ArtifactRecord] = []
        for manifest, requirement in _manifest_requirements(root):
            match = _PACKAGE_NAME.match(requirement)
            if match is None:
                continue
            name = match.group(1).casefold().replace("_", "-")
            tail = match.group(2)
            version_match = _EXACT_VERSION.search(tail)
            version = version_match.group(1) if version_match else "unresolved"
            logical_key = f"pypi::{name}::{version}"
            package = _artifact(
                repository_key,
                snapshot_key,
                logical_key=logical_key,
                kind="package_version",
                path=manifest,
                qualified_name=name,
                language="pypi",
                resolution_confidence=1.0 if version != "unresolved" else 0.6,
                text=requirement,
            )
            if any(existing.logical_key == logical_key for existing in packages):
                continue
            packages.append(package)
            graph.artifacts.append(package)
        return packages

    def _add_entrypoints(
        self,
        root: Path,
        graph: RepositoryGraph,
        repository_key: str,
        snapshot_key: str,
        definitions_by_module: dict[str, dict[str, ArtifactRecord]],
    ) -> None:
        pyproject = root / "pyproject.toml"
        if not pyproject.is_file():
            return
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            graph.warnings.append("Could not parse pyproject.toml entrypoints")
            return
        scripts = data.get("project", {}).get("scripts", {})
        if not isinstance(scripts, dict):
            return
        for name, value in sorted(scripts.items()):
            if not isinstance(name, str) or not isinstance(value, str):
                continue
            module, separator, symbol = value.partition(":")
            if not separator:
                continue
            target = definitions_by_module.get(module, {}).get(symbol)
            if target is None:
                graph.warnings.append(f"Unresolved pyproject entrypoint {name}={value}")
                continue
            entrypoint = _artifact(
                repository_key,
                snapshot_key,
                logical_key=f"pyproject.toml::script::{name}",
                kind="entrypoint",
                path="pyproject.toml",
                qualified_name=name,
                language="python",
                text=value,
            )
            graph.artifacts.append(entrypoint)
            _add_edge(
                graph,
                snapshot_key,
                "STARTS_AT",
                entrypoint.id,
                target.id,
                source="pyproject",
            )


def _artifact(
    repository_key: str,
    snapshot_key: str,
    *,
    logical_key: str,
    kind: ArtifactKind,
    path: str,
    qualified_name: str,
    language: str,
    line_start: int = 0,
    line_end: int = 0,
    content_hash: str = "",
    last_author: str = "",
    last_modified: str = "",
    owner: str = "",
    owner_source: str = "",
    resolution_confidence: float = 1.0,
    text: str = "",
) -> ArtifactRecord:
    key = f"{snapshot_key}::{kind}::{logical_key}"
    identity_key = f"{repository_key}::{kind}::{logical_key}"
    return ArtifactRecord(
        id=stable_id("artifact", key),
        key=key,
        identity_id=stable_id("artifact-identity", identity_key),
        identity_key=identity_key,
        repo_key=repository_key,
        snapshot_key=snapshot_key,
        logical_key=logical_key,
        kind=kind,
        path=path,
        qualified_name=qualified_name,
        language=language,
        line_start=line_start,
        line_end=line_end,
        content_hash=content_hash,
        last_author=last_author,
        last_modified=last_modified,
        owner=owner,
        owner_source=owner_source,
        resolution_confidence=resolution_confidence,
        text=text,
    )


def _add_edge(
    graph: RepositoryGraph,
    snapshot_key: str,
    kind: RelationshipKind,
    source_id: int,
    target_id: int,
    *,
    confidence: float = 1.0,
    first_evidence_line: int = 0,
    source: str = "ast",
    requirement: str = "",
) -> None:
    if source_id == target_id:
        return
    graph.relationships.append(
        RelationshipRecord(
            id=relationship_id(snapshot_key, kind, source_id, target_id),
            kind=kind,
            source_id=source_id,
            target_id=target_id,
            confidence=confidence,
            first_evidence_line=first_evidence_line,
            source=source,
            requirement=requirement,
        )
    )


def _deduplicate_edges(graph: RepositoryGraph) -> None:
    deduplicated: dict[tuple[str, int, int], RelationshipRecord] = {}
    for edge in graph.relationships:
        key = (edge.kind, edge.source_id, edge.target_id)
        existing = deduplicated.get(key)
        if existing is None:
            deduplicated[key] = edge
            continue
        existing.evidence_count += 1
        if not existing.first_evidence_line or (
            edge.first_evidence_line and edge.first_evidence_line < existing.first_evidence_line
        ):
            existing.first_evidence_line = edge.first_evidence_line
        existing.confidence = max(existing.confidence, edge.confidence)
    graph.relationships = sorted(deduplicated.values(), key=lambda edge: (edge.kind, edge.id))


def _collect_definitions(source: _SourceFile) -> list[_Definition]:
    result: list[_Definition] = []

    def walk(body: Iterable[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            qualified = f"{prefix}.{node.name}" if prefix else node.name
            result.append(_Definition(source=source, node=node, qualified_name=qualified))
            walk(node.body, qualified)

    walk(source.tree.body)
    return result


class _CallCollector(ast.NodeVisitor):
    def __init__(self, root: ast.AST) -> None:
        self.root = root
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node is self.root:
            self.generic_visit(node)


def _collect_calls(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    collector = _CallCollector(node)
    collector.visit(node)
    return collector.calls


def _resolve_call(
    call: ast.Call,
    definition: _Definition,
    bindings: _ModuleBindings,
    definitions_by_module: dict[str, dict[str, ArtifactRecord]],
) -> ArtifactRecord | None:
    current_module = definition.source.module
    local = definitions_by_module.get(current_module, {})
    if isinstance(call.func, ast.Name):
        name = call.func.id
        imported = bindings.symbol_aliases.get(name)
        if imported is not None:
            return definitions_by_module.get(imported[0], {}).get(imported[1])
        return local.get(name)
    if not isinstance(call.func, ast.Attribute):
        return None
    chain = _attribute_chain(call.func)
    if not chain:
        return None
    if chain[0] in {"self", "cls"} and len(chain) == 2:
        class_name = definition.qualified_name.split(".", 1)[0]
        return local.get(f"{class_name}.{chain[1]}")
    module = bindings.module_aliases.get(chain[0])
    if module is not None:
        return definitions_by_module.get(module, {}).get(".".join(chain[1:]))
    if chain[0] in local and len(chain) == 2:
        return local.get(f"{chain[0]}.{chain[1]}")
    return None


def _attribute_chain(node: ast.Attribute) -> list[str]:
    values: list[str] = [node.attr]
    current: ast.expr = node.value
    while isinstance(current, ast.Attribute):
        values.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return []
    values.append(current.id)
    return list(reversed(values))


def _resolve_import_node(
    source: _SourceFile,
    node: ast.Import | ast.ImportFrom,
) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            bound = alias.asname or alias.name.split(".", 1)[0]
            result.append((bound, alias.name, ""))
        return result
    module = _resolve_from_module(source.module, source.relative.endswith("/__init__.py"), node)
    for alias in node.names:
        if alias.name == "*":
            continue
        bound = alias.asname or alias.name
        result.append((bound, module, alias.name))
    return result


def _resolve_from_module(module: str, is_package: bool, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = module.split(".") if is_package else module.split(".")[:-1]
    keep = max(0, len(package_parts) - (node.level - 1))
    base = package_parts[:keep]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _resolve_module_artifact(
    module: str,
    artifacts_by_module: dict[str, ArtifactRecord],
) -> ArtifactRecord | None:
    current = module
    while current:
        artifact = artifacts_by_module.get(current)
        if artifact is not None:
            return artifact
        current = current.rpartition(".")[0]
    return None


def _module_candidates(relative: str) -> list[str]:
    path = Path(relative)
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    candidates: list[str] = []
    if parts:
        if parts[0] in {"src", "lib"} and len(parts) > 1:
            candidates.append(".".join(parts[1:]))
        candidates.append(".".join(parts))
    return list(dict.fromkeys(candidate for candidate in candidates if candidate)) or [path.stem]


def _manifest_requirements(root: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            dependencies = data.get("project", {}).get("dependencies", [])
            if isinstance(dependencies, list):
                result.extend(
                    ("pyproject.toml", value) for value in dependencies if isinstance(value, str)
                )
        except (OSError, tomllib.TOMLDecodeError):
            pass
    requirements = root / "requirements.txt"
    if requirements.is_file():
        for line in requirements.read_text(encoding="utf-8", errors="replace").splitlines():
            value = line.strip()
            if value and not value.startswith(("#", "-")):
                result.append(("requirements.txt", value))
    return result


def _graph_input_fingerprint(root: Path, sources: list[_SourceFile]) -> str:
    """Hash every worktree input that can change the emitted code graph."""

    digest = hashlib.sha256()
    for source in sorted(sources, key=lambda item: item.relative):
        digest.update(source.relative.encode())
        digest.update(b"\0")
        digest.update(source.digest.encode())
        digest.update(b"\0")
    for relative in (
        "pyproject.toml",
        "requirements.txt",
        ".github/CODEOWNERS",
        "CODEOWNERS",
        "docs/CODEOWNERS",
    ):
        path = root / relative
        digest.update(relative.encode())
        digest.update(b"\0")
        if path.is_file():
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        else:
            digest.update(b"missing")
        digest.update(b"\0")
    return digest.hexdigest()


def _definition_text(
    content: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> str:
    lines = content.splitlines()
    start = max(0, int(getattr(node, "lineno", 1)) - 1)
    end = min(len(lines), int(getattr(node, "end_lineno", start + 1) or start + 1))
    return "\n".join(lines[start:end])[:20_000]


def _is_test_path(relative: str) -> bool:
    path = Path(relative)
    return "tests" in path.parts or path.name.startswith("test_") or path.name.endswith("_test.py")


def _clean_repo_key(value: str | None) -> str:
    if value is None:
        raise RepositoryParseError("repo_id cannot be null")
    cleaned = value.strip().casefold()
    if not cleaned or len(cleaned) > 120:
        raise RepositoryParseError("repo_id must contain 1 to 120 characters")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", cleaned):
        raise RepositoryParseError(
            "repo_id may contain lowercase letters, numbers, '.', '_', and '-'"
        )
    return cleaned
