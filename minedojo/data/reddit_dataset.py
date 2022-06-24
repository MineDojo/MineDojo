from __future__ import annotations

import json
import os

import praw

from .download import download as dl
from .download import get_fn


class RedditDataset:
    """
    Class for MineDojo Reddit Database API.
    We follow PyTorch Dataset format but without actually inheriting from PyTorch dataset to keep the framework general.
    See https://praw.readthedocs.io/en/stable/getting_started/quick_start.html
    for setting up ``client_id``, ``cliend_secret`` and ``user_agent``.

    Args:
        download: If ``True`` and there is no existing cache directory, the data will be downloaded automatically.

        download_dir: Directory path where the downloaded data will be saved.
                Default: ``~/.minedojo/``.

        client_id: The client ID to access Reddit’s API as a script application.

        client_secret: The client secret to access Reddit’s API as a script application.

        user_agent:  A unique identifier that helps Reddit determine the source of network requests.

        max_comments: Maximum number of comments to load.

    Examples:
        >>> from minedojo.data import RedditDataset
        >>> reddit_dataset = RedditDataset(client_id={your_client_id}, client_secret={your_client_secret}, user_agent={your_user_agent})
        >>> print(reddit_dataset[0].keys())
        dict_keys(['id', 'title', 'link', 'score', 'num_comments', 'created_utc', 'type', 'content', 'comments'])
    """

    def __init__(
        self,
        *,
        download: bool = True,
        download_dir: None | str = None,
        client_id: str = None,
        client_secret: str = None,
        user_agent: str = None,
        max_comments: int = 100,
    ):
        if download_dir is None:
            download_dir = os.path.join(os.path.expanduser("~"), ".minedojo")

        if download:
            self.root = dl("reddit", download_dir)
        else:
            self.root, _, url = get_fn("reddit", download_dir)
            assert os.path.exists(self.root), (
                f"Reddit data file {self.root} does not exist. "
                "Please set download=True or you can manually "
                f"download it from {url}."
            )

        with open(self.root, "r") as f:
            self.data = json.load(f)

        if client_id is None or client_secret is None or user_agent is None:
            raise RedditAPIKeyNotSpecifiedError

        self.api = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,
        )

        self.max_comments = max_comments

    def get_metadata(self, post_id: str, post_type: str) -> dict:
        """Get post metadata using PRAW.

        Args:
            post_id: The unique, base36 ID of a Reddit post.
            post_type: The type of the post, either "image", "text", "video" or "link".

        Return:
            A dictionary containing the metadata of the post.

            - id(``str``) - The unique, base36 Reddit post ID.

            - title(``str``) - The title of the Reddit post.

            - link(``str``) - The url of the Reddit post.

            - score(``int``) - The score of the Reddit post.

            - num_comments(``int``) - The number of comments under the Reddit post. Does not account for deleted comments.

            - created_utc(``int``) - The date and time the Reddit post was created, in UTC format.

            - type(``str``) - The type of the post, either "image", "text", "video" or "link".

            - content(``str``) - If text type post, text in post body. Otherwise, the media source url or website link.

            - comments(``list[dict]``)

                - id(``str``) - The unique base36 comment ID.

                - parent_id(``str``) - The ID of the comment's parent in the nested comment tree.

                - content(``str``) - The text in comment body.
        """
        post = self.api.submission(id=post_id)

        metadata = {
            "id": post.id,
            "title": post.title,
            "link": f"https://www.reddit.com/r/Minecraft/comments/{post.id}",
            "score": post.score,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "type": post_type,
            "content": post.selftext if post_type == "text" else post.url,
            "comments": self.get_comments(post),
        }

        return metadata

    def get_comments(self, post: praw.models.Submission) -> list[dict]:
        comments = []
        comment_queue = post.comments[:]
        while len(comments) < self.max_comments and comment_queue:
            comment = comment_queue.pop(0)
            if isinstance(comment, praw.models.MoreComments):
                comment_queue.extend(comment.comments())
                continue

            comments.append(
                {
                    "id": comment.id,
                    "parent_id": comment.parent_id[3:],
                    "content": comment.body,
                }
            )

        return comments

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.get_metadata(
            post_id=self.data[idx]["id"], post_type=self.data[idx]["type"]
        )


class RedditAPIKeyNotSpecifiedError(Exception):
    def __init__(self):
        self.message = (
            'You need to specify "client_id", "client_secret" and "user_agent" for Reddit API. '
            "You can refer to https://praw.readthedocs.io/en/stable/getting_started/quick_start.html "
            "for the instructions of obtaining Reddit API keys."
        )
        super().__init__(self.message)
