#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Define extensions here
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import exc
from sqlalchemy import Table, Column, BLOB, String, CHAR, VARCHAR, BOOLEAN, VARBINARY, TEXT
from sqlalchemy import DateTime, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import text, func
import sys
import pickle
import zlib
import ConfigParser

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
        if sys.version_info[0] < 3:
            self.content = ''
            self.contentCN = ''
        else:
            #self.content = ''
            #self.contentCN = ''
            self.content = bytes('', 'utf8')
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
        else:
            logging.debug(logging.DEBUG, 'invalid table name: %s' % tbl_name)
            session.commit()

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
        if tbl_name == 'ArticleEN':
            result = session.query(ArticleEN).filter(ArticleEN.url == url).all()
        elif tbl_name == 'ArticleCN':
            result = session.query(ArticleCN).filter(ArticleCN.url == url).all()
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
