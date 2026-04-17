import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article
from src.app.models.user import User


async def _make_author(session: AsyncSession) -> User:
    user = User(
        email=f"author-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="not-a-real-hash",
        display_name="Author",
        initials="AU",
    )
    session.add(user)
    await session.flush()
    return user


def _make_article(author_id: uuid.UUID, **overrides) -> Article:
    defaults = {
        "id": f"art_{uuid.uuid4().hex[:16]}",
        "author_id": author_id,
        "title": "Hello",
    }
    defaults.update(overrides)
    return Article(**defaults)


async def test_article_array_fields_roundtrip(session: AsyncSession) -> None:
    author = await _make_author(session)
    article = _make_article(
        author.id,
        tags=["finance", "tips", "envelopes"],
        linked_set_ids=["set_1", "set_2"],
    )
    session.add(article)
    await session.flush()
    await session.refresh(article)

    fetched = (await session.execute(select(Article).where(Article.id == article.id))).scalar_one()

    assert fetched.tags == ["finance", "tips", "envelopes"]
    assert fetched.linked_set_ids == ["set_1", "set_2"]


async def test_article_array_fields_default_to_none(session: AsyncSession) -> None:
    author = await _make_author(session)
    article = _make_article(author.id)
    session.add(article)
    await session.flush()
    await session.refresh(article)

    assert article.tags is None
    assert article.linked_set_ids is None
    assert article.status == "draft"
    assert article.views_count == 0


async def test_article_tags_can_hold_unicode_and_empty_list(session: AsyncSession) -> None:
    author = await _make_author(session)
    article = _make_article(author.id, tags=["бюджет", "копилка", ""])
    session.add(article)
    await session.flush()
    await session.refresh(article)

    assert article.tags == ["бюджет", "копилка", ""]
