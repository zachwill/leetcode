# -*- coding: utf-8 -*-

"""
Models to store scraped data in a database.
"""

import inspect

from peewee import SqliteDatabase, Model
from peewee import CompositeKey, FloatField, IntegerField, TextField
from playhouse.sqliteq import SqliteQueueDatabase


db = SqliteQueueDatabase("leetcode.db", autostart=True)
# db = SqliteDatabase("leetcode.db")


class BaseModel(Model):
    class Meta:
        database = db

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __delitem__(self, key):
        return setattr(self, key, None)

    @classmethod
    def primary_keys(cls):
        pk = cls._meta.primary_key
        if "field_names" in pk.__dict__:
            names = pk.field_names
        else:
            names = (pk.name,)
        return names

    @classmethod
    def from_scrapy_item(cls, item):
        query = cls.insert(**item).on_conflict("REPLACE")
        return query.execute()


# ----------------------------------------------------------------------------
# Example Models
# ----------------------------------------------------------------------------

class Question(BaseModel):
    leetcode_id = IntegerField()
    question_id = TextField(primary_key=True)
    title = TextField(null=True)
    difficulty = TextField(null=True)
    likes = TextField(null=True)
    dislikes = IntegerField(null=True)
    content = TextField(null=True)
    text_content = TextField(null=True)
    paid_only = IntegerField(null=True)
    sample_test_case = TextField(null=True)
    accepted = IntegerField(null=True)
    submitted = IntegerField(null=True)
    accepted_rate = FloatField(null=True)

    class Meta:
        db_table = "question"

    @classmethod
    def from_scrapy_item(cls, item):
        question_id = item.pop("question_id")
        query = cls.insert(question_id=question_id, **item).on_conflict("IGNORE")
        query.execute()
        return cls.update(**item).where((cls.question_id == question_id)).execute()


class SimilarQuestion(BaseModel):
    leetcode_id = IntegerField(null=True)
    question_id = TextField()
    similar_id = TextField()
    similar_title = TextField(null=True)
    similar_difficulty = TextField(null=True)

    class Meta:
        db_table = "similar_question"
        primary_key = CompositeKey("question_id", "similar_id")


class Tag(BaseModel):
    leetcode_id = IntegerField(null=True)
    question_id = TextField()
    tag_id = TextField()
    tag_name = TextField(null=True)

    class Meta:
        db_table = "tag"
        primary_key = CompositeKey("question_id", "tag_id")


class Hint(BaseModel):
    leetcode_id = IntegerField(null=True)
    question_id = TextField()
    hint = TextField()

    class Meta:
        db_table = "hint"
        primary_key = CompositeKey("question_id", "hint")


class Solution(BaseModel):
    leetcode_id = IntegerField(null=True)
    question_id = TextField(primary_key=True)
    url = TextField(null=True)
    content = TextField(null=True)
    visible = IntegerField(null=True)
    rating = FloatField(null=True)
    rating_count = IntegerField(null=True)

    class Meta:
        db_table = "solution"


# ----------------------------------------------------------------------------
# Automatically create the tables...
# ----------------------------------------------------------------------------


def create_tables():
    models = []
    for name, cls in globals().items():
        if inspect.isclass(cls) and issubclass(cls, BaseModel):
            if name == "BaseModel":
                continue
            models.append(cls)
    db.create_tables(models, safe=True)


if __name__ == "__main__":
    create_tables()
