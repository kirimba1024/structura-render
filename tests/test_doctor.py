import json
import os
import subprocess
import sys
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from structura_render import doctor


@pytest.fixture
def installation(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, '_version', lambda package: '1.0')
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    root = tmp_path / 'assets/minecraft'
    for directory in doctor.RESOURCE_DIRECTORIES:
        (root / directory).mkdir(parents=True)
    return root


def test_missing_extra_gives_exact_install_command(installation, monkeypatch):
    monkeypatch.setattr(doctor, '_version', lambda package: None if package == 'trimesh' else '1.0')
    report = doctor.diagnose(source=installation)
    assert report['outputs']['glb']['missing'] == ['trimesh']
    assert report['outputs']['glb']['install'] == 'pip install "structura-render[gltf]"'
    assert report['outputs']['png']['status'] == 'render_unchecked'
    assert report['assets']['minecraft_version'] is None
    assert report['cache']['writable_by_permissions']
    assert not (installation.parents[1] / 'cache').exists()


def test_missing_assets_do_not_disable_projections(installation):
    report = doctor.diagnose(source=installation / 'missing')
    assert report['outputs']['projections']['status'] == 'dependencies_present'
    assert report['outputs']['glb']['status'] == 'assets_missing'
    assert report['assets']['error']


def test_base_outputs_work_without_scipy_or_optional_backends(installation, monkeypatch):
    packages = {'structura-core', 'structura-render', 'amulet-nbt', 'numpy', 'Pillow'}
    monkeypatch.setattr(doctor, '_version', lambda package: '1.0' if package in packages else None)

    report = doctor.diagnose(source=installation / 'missing')

    for output in ('projections', 'svg', 'vox'):
        assert report['outputs'][output] == {'status': 'dependencies_present', 'missing': []}
    for output in ('usd', 'usda', 'usdc', 'usdz'):
        assert report['outputs'][output]['missing'] == ['usd-core']
        assert report['outputs'][output]['install'] == 'pip install "structura-render[usdz]"'


def test_jar_is_inspected_without_extraction(installation):
    path = installation.parents[1] / 'client.jar'
    with ZipFile(path, 'w') as archive:
        for name in doctor.RESOURCE_DIRECTORIES:
            archive.writestr(f'assets/minecraft/{name}/sample.json', '{}')
        archive.writestr('version.json', '{"id":"1.21.1"}')
    report = doctor.diagnose(source=path)
    assert report['assets']['layout_ok']
    assert report['assets']['minecraft_version'] == '1.21.1'
    assert not (installation.parents[1] / 'cache').exists()


@pytest.mark.parametrize('kind', ['broken', 'incomplete', 'traversal'])
def test_bad_assets_are_reported_without_traceback(installation, kind):
    path = installation.parents[1] / 'client.jar'
    if kind == 'broken':
        path.write_bytes(b'not a zip')
    else:
        with ZipFile(path, 'w') as archive:
            archive.writestr('assets/minecraft/models/block/example.json', '{}')
            if kind == 'traversal':
                archive.writestr('assets/minecraft/../outside', 'bad')
    report = doctor.diagnose(source=path)
    assert not report['assets']['layout_ok']
    assert report['outputs']['usdz']['status'] == 'assets_missing'


def test_metadata_and_help_never_import_backends_or_resolve_assets(tmp_path):
    script = '''
import importlib.abc, runpy, sys
class NoBackend(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'pyvista', 'vtk', 'vtkmodules', 'trimesh', 'pxr', 'amulet', 'amulet_nbt'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, NoBackend())
sys.argv = ['structura-render', 'doctor', '--json']
runpy.run_module('structura_render', run_name='__main__')
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, check=True,
                            env={**os.environ, 'STRUCTURA_MINECRAFT_ASSETS': str(tmp_path / 'missing'),
                                 'XDG_CACHE_HOME': str(tmp_path / 'cache')})
    assert not json.loads(result.stdout)['assets']['layout_ok']
    assert not (tmp_path / 'cache').exists()


@pytest.mark.parametrize('outcome', ['passed', 'crash', 'timeout'])
def test_graphics_probe_is_explicit_isolated_and_bounded(installation, monkeypatch, outcome):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        assert command[0] == sys.executable and kwargs['timeout'] == 30
        if outcome == 'timeout':
            raise subprocess.TimeoutExpired(command, 30)
        return SimpleNamespace(returncode=0 if outcome == 'passed' else -6, stderr='backend error')

    monkeypatch.setattr(doctor.subprocess, 'run', run)
    assert doctor.diagnose(source=installation)['render_test']['status'] == 'not_run'
    assert not calls
    report = doctor.diagnose(source=installation, render_test=True)
    assert report['render_test']['status'] == ('passed' if outcome == 'passed' else 'failed')
    assert len(calls) == 1


def test_failed_explicit_probe_returns_json_and_nonzero_exit(installation, monkeypatch, capsys):
    monkeypatch.setattr(doctor, '_render_test', lambda: {'status': 'failed', 'error': 'backend unavailable'})
    with pytest.raises(SystemExit) as error:
        doctor.main(['--assets', str(installation), '--render-test', '--json'])
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)['render_test']['status'] == 'failed'
