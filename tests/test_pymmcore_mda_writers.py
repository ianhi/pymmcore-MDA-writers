from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
import zarr
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import MDAEngine
from useq import MDASequence

from pymmcore_mda_writers import SimpleMultiFileTiffWriter, ZarrWriter

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


@pytest.fixture
def core() -> CMMCorePlus:
    mmc = CMMCorePlus.instance()
    if len(mmc.getLoadedDevices()) < 2:
        mmc.loadSystemConfiguration(str(Path(__file__).parent / "test-config.cfg"))
    return mmc


def test_engine_registration(core: CMMCorePlus, tmp_path: Path, qtbot: "QtBot"):
    mda = MDASequence(
        stage_positions=[(1, 1, 1)],
        z_plan={"range": 3, "step": 1},
        channels=[{"config": "DAPI", "exposure": 1}],
    )

    writer = ZarrWriter(  # noqa
        tmp_path / "zarr_data", (512, 512), dtype=np.uint16, core=core
    )
    new_engine = MDAEngine(core)
    with qtbot.waitSignal(core.events.mdaEngineRegistered):
        core.register_mda_engine(new_engine)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    arr1 = np.asarray(zarr.open(tmp_path / "zarr_data_1.zarr"))
    arr2 = np.asarray(zarr.open(tmp_path / "zarr_data_2.zarr"))
    print(list(tmp_path.glob("*")))
    assert arr1.shape == (1, 1, 4, 512, 512)
    assert arr2.shape == (1, 1, 4, 512, 512)
    for i in range(4):
        assert not np.all(arr1[0, 0, i] == 0)
        assert not np.all(arr2[0, 0, i] == 0)


def test_tiff_writer(core: CMMCorePlus, tmp_path: Path, qtbot: "QtBot"):
    mda = MDASequence(
        time_plan={"interval": 0.1, "loops": 2},
        stage_positions=[(1, 1, 1)],
        z_plan={"range": 3, "step": 1},
        channels=[{"config": "DAPI", "exposure": 1}],
    )
    writer = SimpleMultiFileTiffWriter(str(tmp_path / "mda_data"), core=core)  # noqa

    # run twice to check that we aren't overwriting files
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)

    # check that the correct folders/files were generated
    data_folders = set(tmp_path.glob("mda_data*"))
    assert {tmp_path / "mda_data_1", tmp_path / "mda_data_2"}.issubset(
        set(data_folders)
    )
    expected = [
        Path("t000_p000_c000_z000.tiff"),
        Path("t001_p000_c000_z000.tiff"),
        Path("t001_p000_c000_z002.tiff"),
        Path("t001_p000_c000_z001.tiff"),
        Path("t000_p000_c000_z001.tiff"),
        Path("t001_p000_c000_z003.tiff"),
        Path("t000_p000_c000_z002.tiff"),
        Path("t000_p000_c000_z003.tiff"),
    ]
    actual_1 = list((tmp_path / "mda_data_1").glob("*"))
    actual_2 = list((tmp_path / "mda_data_2").glob("*"))
    for e in expected:
        assert tmp_path / "mda_data_1" / e in actual_1
        assert tmp_path / "mda_data_2" / e in actual_2
