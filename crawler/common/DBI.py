#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Define extensions here
import logging
import sys
import pickle
import zlib
import ConfigParser
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import exc
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import DateTime, BLOB, String, CHAR, VARCHAR, BOOLEAN, VARBINARY, TEXT, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import text


cp = ConfigParser.SafeConfigParser()
cp.read('alchemy.conf')

# SQLAlchemy
# turn on SQLalchemy if echo=True
Base = declarative_base()
db_user = cp.get('db', 'user')
db_passwd = cp.get('db', 'pass')
db_name = 'fool'
connect_str = "mysql+pymysql://%s:%s@127.0.0.1:3306/%s?charset=utf8" % (db_user, db_passwd, db_name)
engine = create_engine(connect_str, max_overflow=5, encoding="utf-8", echo=False)
Session = scoped_session(sessionmaker(bind=engine))
# turn on debuglog log output
#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


# declare Database schema and ORM mapping
class ArticleEN(Base):
    __tablename__ = 'ArticleEN'
    url = Column(VARCHAR(128), unique=True, primary_key=True)
    mainTitle = Column(VARCHAR(128), nullable=False)
    subTitle = Column(VARCHAR(256))
    articleTag = Column(VARCHAR(128))
    articleSection = Column(VARCHAR(128))
    content = Column(BLOB, nullable=False)
    authorName = Column(VARCHAR(32))
    publishDate = Column(VARCHAR(32))
    publishTime = Column(DateTime)

    def __init__(self, item):
        self.url = item['url']
        self.mainTitle = item['mainTitle']
        self.subTitle = item['subTitle']
        self.content = zlib.compress(pickle.dumps(item['content']))
        self.articleTag = item['articleTag']
        self.articleSection = item['articleSection']
        self.authorName = item['authorName']
        self.publishDate = item['publishDate']
        self.publishTime = item['publishTime']

    def __repr__(self):
        return "<Metadata('%s','%s')>" % (self.url, self.mainTitle)


# declare Database schema and ORM mapping
class ArticleCN(Base):
    __tablename__ = 'ArticleCN'
    url = Column(VARCHAR(128), unique=True, primary_key=True)
    mainTitle = Column(VARCHAR(128), nullable=False)
    subTitle = Column(VARCHAR(256))
    articleTag = Column(VARCHAR(128))
    articleSection = Column(VARCHAR(128))
    content = Column(BLOB, nullable=False)
    contentCN = Column(TEXT)
    authorName = Column(VARCHAR(32))
    publishDate = Column(VARCHAR(32))
    publishTime = Column(DateTime)
    publishedFlag = Column(BOOLEAN)
    translator = Column(CHAR(1))

    def __init__(self):
        self.url = ''
        self.mainTitle = ''
        self.subTitle = ''
        self.content = ''
        self.contentCN = ''
        self.articleTag = ''
        self.articleSection = ''
        self.authorName = ''
        self.publishDate = ''
        self.publishTime = ''
        self.publishedFlag = False
        self.translator = ''

    def __repr__(self):
        return "<Metadata('%s','%s')>" % (self.url, self.mainTitle)


# store original article data
class ArticleOrig(Base):
    __tablename__ = 'ArticleOrig'
    url         = Column(VARCHAR(128), unique=True, primary_key=True)
    mainTitle   = Column(VARCHAR(128), nullable=False)
    mainTitleCN = Column(VARCHAR(128))
    articleTag  = Column(VARCHAR(128), nullable=False)
    articleSection = Column(VARCHAR(128))
    content = Column(BLOB, nullable=False)
    contentCN = Column(BLOB)
    authorId = Column(Integer, nullable=False)
    publishTime = Column(DateTime, nullable=False)

    def __init__(self, item):
        self.url = item['url']
        self.mainTitle = item['mainTitle']
        self.content = zlib.compress(pickle.dumps(item['content']))
        self.articleTag = item['articleTag']
        self.articleSection = item['articleSection']
        self.authorId = item['authorId']
        self.publishTime = item['publishTime']

    def __repr__(self):
        return "<Metadata('%s','%s')>" % (self.url, self.mainTitle)

# store original article data
class AuthorCard(Base):
    __tablename__ = 'AuthorCard'
    id      = Column(Integer, unique=True, primary_key=True)
    name    = Column(VARCHAR(128), nullable=False)
    contact = Column(VARCHAR(128), nullable=False)
    link    = Column(VARCHAR(128), nullable=False)
    info    = Column(BLOB)
    infoCN  = Column(BLOB)

    # ------------------------------------------------
    # functions related to Author table
    # ------------------------------------------------
    def __init__(self):
        pass

    def __init__(self, item):
        self.name    = item['authorName']
        self.contact = item['authorContact']
        self.link    = item['authorLink']
        self.info    = zlib.compress(pickle.dumps(item['authorInfo']))

    def __repr__(self):
        return "<Metadata('%s','%s')>" % (self.name, self.contact)

    @staticmethod
    def get(contact):
        if contact == '':
            raise KeyError('contact is empty string')
        session = Session()
        result = session.query(
            AuthorCard).filter(AuthorCard.contact == contact).all()
        session.commit()
        if len(result)>0:
            return result[0]
        else:
            raise KeyError('%s does not exist' % contact)

    # update author infoCN
    def set_info_cn(self, info_cn):
        logging.log(logging.DEBUG, 'set_info_cn(): contact %s' % (self.contact))
        if self.contact == '':
            raise KeyError('contact is empty string')
        try:
            session = Session()
            for a in session.query(AuthorCard
                            ).filter(AuthorCard.contact == self.contact).all():
                a.infoCN = zlib.compress(pickle.dumps(info_cn))
            session.commit()
        except exc.SQLAlchemyError as e:
            logging.log(logging.DEBUG, e)
            raise e

    # check if an author exists in DB
    #   return author id if already exists
    #   return None if not existed
    @staticmethod
    def add_author(item):
        author_name = item['authorName']
        author_contact = item['authorContact']
        logging.log(logging.DEBUG, '%s %s' % (author_name, author_contact))
        try:
            session = Session()
            record = AuthorCard(item)
            session.add(record)
            session.commit()
            return record.id
        except exc.SQLAlchemyError as e:
            logging.log(logging.DEBUG, e)
            return None

    @staticmethod
    def has_author(item):
        author_name = item['authorName']
        author_contact = item['authorContact']
        logging.log(logging.DEBUG, '%s %s' % (author_name, author_contact))
        session = Session()
        result = []
        if author_contact:
            result = session.query(AuthorCard).filter(AuthorCard.contact == author_contact).all()
            session.commit()
            if len(result) > 0:
                return result.id
            else:
                return None
        else:
            return None

    # get all authors that are not translated
    @staticmethod
    def get_un_translated_authors():
        session = Session()
        result = session.query(
            AuthorCard.id,
            AuthorCard.name,
            AuthorCard.contact,
            AuthorCard.link
        ).filter(AuthorCard.infoCN == None).all()
        session.commit()
        return result

    # get an article exists in DB via URL
    @staticmethod
    def update_author(author):
        session = Session()
        if author.contact != '':
            for a in session.query(AuthorCard).filter(AuthorCard.contact == author.contact).all():
                a = author
        elif author.name != '':
            for a in session.query(AuthorCard).filter(AuthorCard.name == author.name).all():
                a = author
        session.commit()
        return True

# create database and tables
try:
    Base.metadata.create_all(engine)
except exc.SQLAlchemyError as err:
    print(err)
    sys.exit(1)


class SQLiteManager(object):
    @staticmethod
    def add_article(tbl_name, item):
        logging.log(logging.DEBUG, 'add_article() %s' % item['url'])
        try:
            if tbl_name == 'ArticleEN':
                session = Session()
                record = ArticleEN(item)
                session.add(record)
                session.commit()
                return True
            elif tbl_name == 'ArticleCN':
                session = Session()
                record = ArticleCN()
                session.add(record)
                session.commit()
                return True
            else:
                logging.log(logging.DEBUG, 'invalid table name: %s' % tbl_name)
                return False
        except exc.SQLAlchemyError as e:
            logging.log(logging.DEBUG, e)
            return False

    @staticmethod
    def add_article(article):
        logging.log(logging.DEBUG, 'add_article() %s %s' % (type(article), article.url))
        try:
            session = Session()
            record = article
            session.add(record)
            session.commit()
            return True
        except exc.SQLAlchemyError as e:
            logging.log(logging.DEBUG, e)
            return False


    
    # update article tag field
    @staticmethod
    def upd_article_tag(tbl_name, url, tags):
        session = Session()
        if tbl_name == 'ArticleCN':
            for a in session.query(ArticleCN).filter(ArticleCN.url == url).all():
                a.articleTag = tags
            session.commit()
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()

    # update article publishedFlag field
    @staticmethod
    def upd_article_published_flag(tbl_name, url, published_flag):
        session = Session()
        if tbl_name == 'ArticleCN':
            for a in session.query(ArticleCN).filter(ArticleCN.url == url).all():
                a.publishedFlag = published_flag
            session.commit()
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()

    # update article translator field
    @staticmethod
    def upd_article_translator(tbl_name, url, t):
        session = Session()
        if tbl_name == 'ArticleCN':
            for a in session.query(ArticleCN).filter(ArticleCN.url == url).all():
                a.translator = t
            session.commit()
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()

    # update article contentCN field
    @staticmethod
    def upd_article_contentCN(tbl_name, url, c):
        session = Session()
        if tbl_name == 'ArticleCN':
            for a in session.query(ArticleCN).filter(ArticleCN.url == url).all():
                a.contentCN = c
            session.commit()
            return True
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()
            return False

    # update article contentCN field
    @staticmethod
    def upd_article(tbl_name, article):
        session = Session()
        if tbl_name == 'ArticleOrig':
            for a in session.query(ArticleOrig).filter(ArticleOrig.url == article.url).all():
                a = article
            session.commit()
            return True
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()
            return False

    # delete article from DB via URL
    @staticmethod
    def del_article(tbl_name, url):
        logging.debug(logging.DEBUG, 'delete %s' % url)
        session = Session()
        if tbl_name == 'ArticleEN':
            ret = session.query(ArticleEN).filter(ArticleEN.url == url).delete(synchronize_session=False)
            session.commit()
            return ret
        elif tbl_name == 'ArticleCN':
            ret = session.query(ArticleCN).filter(ArticleCN.url == url).delete(synchronize_session=False)
            session.commit()
            return ret
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()

    # check if an article exists in DB via URL
    @staticmethod
    def has_article(tbl_name, url):
        # logging.log(logging.DEBUG, '%s %s' % (tbl_name, url))
        session = Session()
        result = []
        if   tbl_name == 'ArticleEN':
            result = session.query(ArticleEN).filter(ArticleEN.url == url).all()
        elif tbl_name == 'ArticleCN':
            result = session.query(ArticleCN).filter(ArticleCN.url == url).all()
        elif tbl_name == 'ArticleOrig':
            result = session.query(ArticleOrig).filter(ArticleOrig.url == url).all()
        else:
            logging.error(logging.DEBUG, 'invalid table name: %s' % tbl_name)

        session.commit()
        ret = (len(result) > 0)
        logging.log(logging.DEBUG, 'has_article() return %r' % ret)
        return ret

    # get an article exists in DB via URL
    @staticmethod
    def get_article(tbl_name, url):
        # logging.log(logging.DEBUG, '%s %s' % (tbl_name, url))
        session = Session()
        result = []
        if tbl_name == 'ArticleEN':
            result = session.query(ArticleEN).filter(ArticleEN.url == url).all()
        elif tbl_name == 'ArticleCN':
            result = session.query(
                ArticleCN.mainTitle,
                ArticleCN.authorName,
                ArticleCN.articleTag,
                ArticleCN.articleSection,
                ArticleCN.publishDate,
                ArticleCN.publishedFlag,
                ArticleCN.content,
                ArticleCN.contentCN
            ).filter(ArticleCN.url == url).all()
        elif tbl_name == 'ArticleOrig':
            result = session.query(ArticleOrig).filter(ArticleOrig.url == url).all()
        else:
            logging.error(logging.DEBUG, 'invalid table name: %s' % tbl_name)
        session.commit()

        logging.log(logging.DEBUG, 'get_article() return %d articles' % len(result))
        if len(result) > 0:
            return result[0]
        else:
            return None

    # retrieve all articles from DB
    @staticmethod
    def all_article(tbl_name):
        if tbl_name == 'ArticleEN':
            session = Session()
            ret = session.query(ArticleEN).order_by(ArticleEN.publishDate.asc()).all()
            session.commit()
            return ret
        elif tbl_name == 'ArticleCN':
            session = Session()
            ret = session.query(
                ArticleCN.url,
                ArticleCN.mainTitle,
                ArticleCN.authorName,
                ArticleCN.articleTag,
                ArticleCN.articleSection,
                ArticleCN.publishDate,
                ArticleCN.publishedFlag
            ).order_by(ArticleCN.publishTime).all()
            session.commit()
            return ret
        else:
            return None

    # retrieve all articles that are not published
    @staticmethod
    def query_unpublished_article():
        session = Session()
        result = session.query(ArticleCN).filter(ArticleCN.publishedFlag == 1).all()
        session.commit()
        return result

    # retrieve all articles that are not translated
    @staticmethod
    def query_un_translated_article():
        sql = text('select url from ArticleEN where url not in (select url from ArticleCN)')
        result = engine.execute(sql)
        urls = []
        for row in result:
            urls.append(row[0])
        logging.log(logging.DEBUG, 'return %d un-translated articles' % len(urls))
        return urls

    # retrieve all articles that are not translated
    @staticmethod
    def query_un_translated_orig_article():
        sql = text('select url from ArticleOrig where contentCN is null')
        result = engine.execute(sql)
        urls = []
        for row in result:
            urls.append(row[0])
        logging.log(logging.DEBUG, 'return %d un-translated articles' % len(urls))
        return urls


def ut_test():
    logging.info(logging.DEBUG, 'MySQL Database')
    # Query records
    session = Session()
    for record in session.query(ArticleEN):
        logging.debug(logging.DEBUG, "url: %s , content: %s " % (record.url, record.mainTitle))
    session.commit()


# for unit test
if __name__ == "__main__":
    ut_test()
