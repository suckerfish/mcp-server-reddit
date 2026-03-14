from enum import Enum
import json
import redditwarp.SYNC
import redditwarp.models.subreddit
from fastmcp import FastMCP
from pydantic import BaseModel

# Monkey-patch redditwarp to handle missing 'active_user_count' field
# (Reddit removed it from their API response, breaking redditwarp 1.3.0)
_orig_subreddit_init = redditwarp.models.subreddit.Subreddit.__init__
def _patched_subreddit_init(self, d, *args, **kwargs):
    if isinstance(d, dict) and 'active_user_count' not in d:
        d['active_user_count'] = None
    _orig_subreddit_init(self, d, *args, **kwargs)
redditwarp.models.subreddit.Subreddit.__init__ = _patched_subreddit_init


class PostType(str, Enum):
    LINK = "link"
    TEXT = "text"
    GALLERY = "gallery"
    UNKNOWN = "unknown"


class SubredditInfo(BaseModel):
    name: str
    subscriber_count: int
    description: str | None


class Post(BaseModel):
    id: str
    title: str
    author: str
    score: int
    subreddit: str
    url: str
    created_at: str
    comment_count: int
    post_type: PostType
    content: str | None


class Comment(BaseModel):
    id: str
    author: str
    body: str
    score: int
    replies: list['Comment'] = []


class PostDetail(BaseModel):
    post: Post
    comments: list[Comment]


mcp = FastMCP("mcp-reddit")

reddit_client = redditwarp.SYNC.Client()


def _get_post_type(submission) -> PostType:
    if isinstance(submission, redditwarp.models.submission_SYNC.LinkPost):
        return PostType.LINK
    elif isinstance(submission, redditwarp.models.submission_SYNC.TextPost):
        return PostType.TEXT
    elif isinstance(submission, redditwarp.models.submission_SYNC.GalleryPost):
        return PostType.GALLERY
    return PostType.UNKNOWN


def _get_post_content(submission) -> str | None:
    if isinstance(submission, redditwarp.models.submission_SYNC.LinkPost):
        return submission.permalink
    elif isinstance(submission, redditwarp.models.submission_SYNC.TextPost):
        return submission.body
    elif isinstance(submission, redditwarp.models.submission_SYNC.GalleryPost):
        return str(submission.gallery_link)
    return None


def _build_post(submission) -> Post:
    return Post(
        id=submission.id36,
        title=submission.title,
        author=submission.author_display_name or '[deleted]',
        score=submission.score,
        subreddit=submission.subreddit.name,
        url=submission.permalink,
        created_at=submission.created_at.astimezone().isoformat(),
        comment_count=submission.comment_count,
        post_type=_get_post_type(submission),
        content=_get_post_content(submission)
    )


def _build_comment_tree(node, depth: int = 3) -> Comment | None:
    if depth <= 0 or not node:
        return None

    comment = node.value
    replies = []
    for child in node.children:
        child_comment = _build_comment_tree(child, depth - 1)
        if child_comment:
            replies.append(child_comment)

    return Comment(
        id=comment.id36,
        author=comment.author_display_name or '[deleted]',
        body=comment.body,
        score=comment.score,
        replies=replies
    )


@mcp.tool()
def get_frontpage_posts(limit: int = 10) -> str:
    """Get hot posts from Reddit frontpage"""
    posts = [_build_post(subm) for subm in reddit_client.p.front.pull.hot(limit)]
    return json.dumps([p.model_dump() for p in posts], indent=2)


@mcp.tool()
def get_subreddit_info(subreddit_name: str) -> str:
    """Get information about a subreddit"""
    subr = reddit_client.p.subreddit.fetch_by_name(subreddit_name)
    info = SubredditInfo(
        name=subr.name,
        subscriber_count=subr.subscriber_count,
        description=subr.public_description
    )
    return json.dumps(info.model_dump(), indent=2)


@mcp.tool()
def get_subreddit_hot_posts(subreddit_name: str, limit: int = 10) -> str:
    """Get hot posts from a specific subreddit"""
    posts = [_build_post(subm) for subm in reddit_client.p.subreddit.pull.hot(subreddit_name, limit)]
    return json.dumps([p.model_dump() for p in posts], indent=2)


@mcp.tool()
def get_subreddit_new_posts(subreddit_name: str, limit: int = 10) -> str:
    """Get new posts from a specific subreddit"""
    posts = [_build_post(subm) for subm in reddit_client.p.subreddit.pull.new(subreddit_name, limit)]
    return json.dumps([p.model_dump() for p in posts], indent=2)


@mcp.tool()
def get_subreddit_top_posts(subreddit_name: str, limit: int = 10, time: str = '') -> str:
    """Get top posts from a specific subreddit. Time filter: hour, day, week, month, year, all"""
    posts = [_build_post(subm) for subm in reddit_client.p.subreddit.pull.top(subreddit_name, limit, time=time)]
    return json.dumps([p.model_dump() for p in posts], indent=2)


@mcp.tool()
def get_subreddit_rising_posts(subreddit_name: str, limit: int = 10) -> str:
    """Get rising posts from a specific subreddit"""
    posts = [_build_post(subm) for subm in reddit_client.p.subreddit.pull.rising(subreddit_name, limit)]
    return json.dumps([p.model_dump() for p in posts], indent=2)


@mcp.tool()
def get_post_content(post_id: str, comment_limit: int = 10, comment_depth: int = 3) -> str:
    """Get detailed content of a specific post including comments"""
    submission = reddit_client.p.submission.fetch(post_id)
    post = _build_post(submission)
    comments = _get_comments(post_id, comment_limit)
    detail = PostDetail(post=post, comments=comments)
    return json.dumps(detail.model_dump(), indent=2)


@mcp.tool()
def get_post_comments(post_id: str, limit: int = 10) -> str:
    """Get comments from a post"""
    comments = _get_comments(post_id, limit)
    return json.dumps([c.model_dump() for c in comments], indent=2)


def _get_comments(post_id: str, limit: int = 10) -> list[Comment]:
    comments = []
    tree_node = reddit_client.p.comment_tree.fetch(post_id, sort='top', limit=limit)
    for node in tree_node.children:
        comment = _build_comment_tree(node)
        if comment:
            comments.append(comment)
    return comments
