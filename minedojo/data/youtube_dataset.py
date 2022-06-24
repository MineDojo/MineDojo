from __future__ import annotations

import json
import os

from .download import download as dl
from .download import get_fn


class YouTubeDataset:
    """
    Class for MineDojo YouTube Database API.
    We follow PyTorch Dataset format but without actually inheriting from PyTorch dataset to keep the framework general.

    Args:
        download: If set to ``True`` and there is no existing cache directory, the data will be downloaded automatically.

        download_dir: Directory path where the downloaded data will be saved.
                Default: ``~/.minedojo/``.

        full: If ``True``, the full version of the YouTube database will be downlaoded.
                If ``False``, only the tutorial version of the YouTube database will be downloaded.
                Default: ``True``.

    Examples:
        >>> from minedojo.data import YouTubeDataset
        >>> youtube_dataset = YouTubeDataset()
        >>> print(youtube_dataset[0].keys())
        dict_keys(['id', 'title', 'link', 'view_count', 'like_count', 'duration', 'fps'])
    """

    def __init__(
        self,
        *,
        download: bool = True,
        download_dir: None | str = None,
        full: bool = True,
    ):
        if download_dir is None:
            download_dir = os.path.join(os.path.expanduser("~"), ".minedojo")

        if download:
            self.root = dl("youtube", download_dir, full)
        else:
            self.root, _, url = get_fn("youtube", download_dir, full)
            assert os.path.exists(self.root), (
                f"YouTube data file {self.root} does not exist. "
                "Please set download=True or you can manually "
                f"download it from {url}."
            )

        with open(self.root, "r") as f:
            self.data = json.load(f)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
