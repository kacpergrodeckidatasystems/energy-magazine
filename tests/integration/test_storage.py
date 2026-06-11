import os

import pandas as pd

from src.airflow.raw_to__etl import LocalParquetStorage


def test_storage_integration_with_(tmp_path):
    storage = LocalParquetStorage(base_dir=str(tmp_path))

    test_df = pd.DataFrame({"voltage": [1.0, 2.0], "current": [0.5, 0.6]})
    subfolder = "test_subfolder"
    filename = "test_file"

    saved_path = storage.save_dataframe(test_df, subfolder, filename)

    assert os.path.exists(saved_path)
    read_df = pd.read_parquet(saved_path)
    pd.testing.assert_frame_equal(test_df, read_df)
