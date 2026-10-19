"""Regression test: generated-project sdists retain requirements.txt (#422).

All ten project templates previously used an explicit sdist include list
that predated requirements.txt generation (#368), so building a generated
project's source distribution silently dropped the deployment manifest
needed by the Azure Functions remote-build/Doctor workflow, even though
the freshly scaffolded directory itself contained the file.
"""

from __future__ import annotations

from pathlib import Path
import tarfile

from hatchling.builders.sdist import SdistBuilder
import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options, list_templates


@pytest.mark.parametrize("template_name", [template.name for template in list_templates()])
def test_generated_project_sdist_retains_requirements_txt(
    tmp_path: Path, template_name: str
) -> None:
    project_root = scaffold_project(
        f"sdist-{template_name}",
        tmp_path,
        template_name=template_name,
        options=build_project_options(
            preset_name="standard",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    canonical_requirements = (project_root / "requirements.txt").read_text(encoding="utf-8")

    artifact = next(SdistBuilder(str(project_root)).build(directory=str(project_root / "dist")))
    with tarfile.open(artifact) as archive:
        members = {
            name: archive.extractfile(name)
            for name in archive.getnames()
            if name.endswith("/requirements.txt")
        }
        assert len(members) == 1, archive.getnames()
        (member_name, fileobj) = next(iter(members.items()))
        assert fileobj is not None
        archived_requirements = fileobj.read().decode("utf-8")
        entrypoints = [name for name in archive.getnames() if name.endswith("/function_app.py")]
        host_jsons = [name for name in archive.getnames() if name.endswith("/host.json")]

    assert entrypoints, "function_app.py missing from sdist"
    assert host_jsons, "host.json missing from sdist"
    assert archived_requirements == canonical_requirements
