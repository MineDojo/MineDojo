import os
import sys
import zipfile

import requests
import wget


def get_doi(link):
    response = requests.get(link)
    return response.url


DOWNLOAD_URLS = {
    "youtube": {
        "full": f"{get_doi('https://doi.org/10.5281/zenodo.6641142')}/files/youtube_full.json",
        "tutorial": f"{get_doi('https://doi.org/10.5281/zenodo.6641142')}/files/youtube_tutorial.json",
    },
    "wiki": {
        "full": f"{get_doi('https://doi.org/10.5281/zenodo.6640448')}/files/wiki_full.zip",
        "samples": f"{get_doi('https://doi.org/10.5281/zenodo.6640448')}/files/wiki_samples.zip",
    },
    "reddit": {
        "full": f"{get_doi('https://doi.org/10.5281/zenodo.6641114')}/files/reddit.json",
    },
}


def get_fn(source: str = "youtube", download_dir: str = None, full: bool = True):
    url = DOWNLOAD_URLS[source][
        "full" if full else "tutorial" if source == "youtube" else "samples"
    ]
    fn = wget.filename_from_url(url)
    extracted_fn = fn if source != "wiki" else fn.replace(".zip", "")
    extracted_fn = os.path.join(download_dir, extracted_fn)
    download_fn = os.path.join(download_dir, fn)

    return extracted_fn, download_fn, url


def download(source: str = "youtube", download_dir: str = None, full: bool = True):
    r"""Function that downloads the datasets of MineDojo to local.

    Args:
        source (string): the sub-dataset name:
            ``'youtube'`` | ``'wiki'`` | ``'reddit'``
        download_dir (string, optional): Directory path where the downloaded data will be saved.
            The default directory is ``~/.minedojo/``.
        full (bool, optional): Only useful when ``source='youtube'`` or ``source='wiki'``. If set to ``False``, only the tutorial version
            of YouTube dataset or the sample version of Wiki dataset will be downloaded. Default is ``True``.

    Returns:
        Directory path to downloaded (extracted) file or folder.

    Examples::
        >>> from minedojo.data.download import download
        >>> print(download("youtube", full=False))
        '~/.minedojo/youtube_tutorial.json'
        >>> print(download("wiki", full=False))
        '~/.minedojo/wiki_samples'
        >>> print(download("reddit"))
        '~/.minedojo/reddit.json'
    """

    if download_dir is None:
        download_dir = os.path.join(os.path.expanduser("~"), ".minedojo")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    if source == "reddit" and not full:
        print(
            "Reddit dataset does not have a sample version. Will download / use the full version."
        )
        full = True

    extracted_fn, download_fn, url = get_fn(source, download_dir, full)

    if os.path.exists(extracted_fn) and (
        source != "wiki" or not os.path.exists(download_fn)
    ):
        return extracted_fn
    elif not os.path.exists(download_fn):
        print(f"Downloading {url} to {download_fn}...")
        wget.download(url, out=download_fn, bar=bar_progress)

    if source == "wiki":
        with zipfile.ZipFile(download_fn, "r") as zip_ref:
            zip_ref.extractall(download_dir)
        os.remove(download_fn)

    return extracted_fn


def bar_progress(current, total, width=80):
    progress_message = f"Downloading: {current / total * 100:.1f}% [{current/1e6:.1f} / {total/1e6:.1f}] MB"
    sys.stdout.write("\r" + progress_message)
    sys.stdout.flush()
