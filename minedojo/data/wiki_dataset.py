from __future__ import annotations

import glob
import json
import os

from PIL import Image

from .download import download as dl
from .download import get_fn


class WikiDataset:
    """
    Class for MineDojo Wiki Database API.
    We follow PyTorch Dataset format but without actually inheriting from PyTorch dataset to keep the framework general.

    Args:
        download: If ``True`` and there is no existing cache directory, the data will be downloaded automatically.

        download_dir: Directory path where the downloaded data will be saved.
                Default: ``~/.minedojo/``.

        full: If ``True``, the full version of the Wiki database will be downlaoded.
                If ``False``, only a sample version of the Wiki database will be downloaded.
                Default: ``True``.

    Examples:
        >>> from minedojo.data import WikiDataset
        >>> wiki_dataset = WikiDataset()
        >>> print(wiki_dataset[0].keys())
        dict_keys(['metadata', 'tables', 'images', 'sprites', 'texts', 'screenshot'])
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
            self.root = dl("wiki", download_dir, full)
        else:
            self.root, _, url = get_fn("wiki", download_dir, full)
            assert os.path.exists(self.root), (
                f"Wiki data folder {self.root} does not exist. "
                "Please set download=True or you can manually "
                f"download and extract it from {url}."
            )

        self.data_paths = glob.glob(f"{self.root}/**/data.json", recursive=True)

    def __len__(self):
        return len(self.data_paths)

    def __getitem__(self, idx):
        data_path = self.data_paths[idx]
        with open(data_path, "r") as f:
            data = json.load(f)

        screenshot_path = data_path.replace("data.json", "screenshot.png")
        with Image.open(screenshot_path) as im:
            im = self._to_rgb(im)
        data["screenshot"] = im

        data_dir = data_path.replace("data.json", "")
        images = []
        for image in data["images"]:
            img_path = f"{data_dir}/{image['path']}"
            with Image.open(img_path) as im:
                im = self._to_rgb(im)
            image["rgb"] = im
            images.append(image)
        data["images"] = images
        return data

    def _to_rgb(self, im: Image.Image):
        if im.mode in ("RGBA", "P"):
            rgba = im.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255))
            return Image.alpha_composite(background, rgba).convert("RGB")
        else:
            return im.convert("RGB")
