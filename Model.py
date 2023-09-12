import telebot
import traceback
import config
import requests
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import Column, Integer, Text, MetaData, Table, String, Date, Boolean, DateTime
from api_exceptions import *

# Dictionnary that holds all the information about a countdown
countsdict = {}

# DB
engine = create_engine('sqlite:///' + config.COUNTSDICT_FILENAME)
Base = declarative_base()
# Create the session to save the data
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)


class CryptoBlock(Base):
    __tablename__ = 'cryptoblock'

    coin_slug = Column(String, primary_key=True)
    height = Column(String)
    timestamp = Column(String)
    difficulty = Column(String)
    shares = Column(String)
    uncle = Column(Boolean)
    uncleHeight = Column(String)
    orphan = Column(Boolean)
    block_hash = Column(String)
    reward = Column(String)

    def __init__(self, coin_slug):
        self.coin_slug = coin_slug
        height = "unknown"
        timestamp = -1
        difficulty = "unknown"
        shares = "unknown"
        uncle = "unknown"
        uncleHeight = "unknown"
        orphan = "unknown"
        block_hash = "unknown"
        reward = "unknown"

    def create(self):
        session = Session()
        block = CryptoBlock(self.coin_slug)
        session.add(block)
        session.commit()
        session.close()

    def update(self):
        coin_slug = self.coin_slug.strip()

        session = Session()
        dbcoin = session.query(CryptoBlock).filter(CryptoBlock.coin_slug == coin_slug).first()

        # We update the coin only if we have a valid dbevent
        if dbcoin is not None:
            dbcoin.coin_slug = self.coin_slug.strip()
        else:
            session.add(self)

        session.commit()
        session.close()

        return dbcoin

    def __repr__(self):
        return "Last CryptoBlock. Coin: {} Timestamp: {}".format(self.coin_slug, self.timestamp)

# create table
Base.metadata.create_all(engine)


def get_miner_wallet_statistics(coin_slug, walletaddress):
    try:
        url = get_coin_wallet_url(coin_slug, walletaddress)
        telebot.logger.info("get_miner_wallet_statistics > Querying url {}".format(url))
        resp = requests.get(url=url)
        data = resp.json()
        return data
    except Exception as e:
        telebot.logger.info("get_miner_wallet_statistics > Error while pulling data for the coin {} and wallet {}.".format(coin_slug, walletaddress))
        traceback.print_exc()
        error_message = "Unable to get data for the coin {} and wallet {}".format(coin_slug, walletaddress)
        raise ApidatanotfoundException(error_message)


def get_miners_statistics(coin_slug):
    try:
        url = get_coin_miners_url(coin_slug)
        telebot.logger.info("get_miners_statistics > Querying url {}".format(url))
        resp = requests.get(url=url)
        data = resp.json()
        return data
    except Exception as e:
        telebot.logger.info("get_miners_statistics > Error while pulling data for the coin {}.".format(coin_slug))
        traceback.print_exc()
        error_message = "Unable to get miners data for the coin {}".format(coin_slug)
        raise ApidatanotfoundException(error_message)


def get_blocks_statistics(coin_slug):
    try:
        url = get_coin_block_api_url(coin_slug)
        telebot.logger.info("get_blocks_statistics > Querying url {}".format(url))
        resp = requests.get(url=url)
        data = resp.json()
        return data
    except Exception as e:
        telebot.logger.info("get_blocks_statistics > Error while pulling data for the coin {}.".format(coin_slug))
        traceback.print_exc()
        error_message = "Unable to get block data for the coin {}".format(coin_slug)
        raise ApidatanotfoundException(error_message)


def get_coin_statistics(coin_slug):
    try:
        url = get_coin_stats_api_url(coin_slug)
        telebot.logger.info("get_coin_statistics > Querying url {}".format(url))
        resp = requests.get(url=url)
        data = resp.json()
        return data
    except Exception as e:
        telebot.logger.info("get_coin_statistics > Error while pulling data for the coin {}.".format(coin_slug))
        traceback.print_exc()
        error_message = "Unable to get data for the coin {}".format(coin_slug)
        raise ApidatanotfoundException(error_message)


def get_coin_wallet_statistics(coin_slug, walletaddress):
    try:
        url = get_coin_wallet_url(coin_slug, walletaddress)
        telebot.logger.info("get_coin_wallet_statistics > Querying url {}".format(url))
        resp = requests.get(url=url)
        data = resp.json()
        return data
    except Exception as e:
        telebot.logger.info("get_coin_wallet_statistics > Error while pulling data for the coin {} and wallet {}.".format(coin_slug, walletaddress))
        traceback.print_exc()
        error_message = "Unable to get data for the coin {} and wallet {}".format(coin_slug, walletaddress)
        raise ApidatanotfoundException(error_message)


def get_coin_root_url(coin_slug):
    try:
        return config.COIN2URL_MAP[coin_slug]
    except KeyError as e:
        errormessage = "The coin {} is not available".format(coin_slug)
        telebot.logger.info("get_coin_root_url > {}".format(errormessage))
        traceback.print_exc()
        raise ApidatanotfoundException(errormessage)


def get_coin_api_url(coin_slug):
    return "{}/api".format(get_coin_root_url(coin_slug))


def get_coin_stats_api_url(coin_slug):
    telebot.logger.info("Getting stats api url for slug {}.".format(coin_slug))
    return "{}/stats".format(get_coin_api_url(coin_slug))


def get_coin_block_api_url(coin_slug):
    telebot.logger.info("Getting block api url for slug {}.".format(coin_slug))
    return "{}/blocks".format(get_coin_api_url(coin_slug))


def get_coin_miners_url(coin_slug):
    telebot.logger.info("Getting miners url for slug {}.".format(coin_slug))
    return "{}/miners".format(get_coin_api_url(coin_slug))


def get_coin_wallet_url(coin_slug, walletaddress):
    telebot.logger.info("Getting wallet url for slug {} and wallet address {}".format(coin_slug, walletaddress))
    return "{}/accounts/{}".format(get_coin_api_url(coin_slug), walletaddress)


def get_cryptoblock_by_coinslug(coin_slug):
    if coin_slug in countsdict.keys():
        return countsdict[coin_slug]
    else:
        return config.DATANOTFOUND_STR


def save_cryptoblock(coin_slug, cryptoblock):
    countsdict[coin_slug] = cryptoblock


def save_countsdict():

    try:
        print("Saving last block into file ", config.COUNTSDICT_FILENAME)
        # for key in countsdict.keys():
        #     #pickle.dump(countsdict[key], f)
        #     event = countsdict[key]
        #     session.add(event)
        # session.commit()
        # with open(config.COUNTSDICT_FILENAME,"w") as f:
        #     for key in countsdict.keys():
        #         #pickle.dump(countsdict[key], f)
        #         event = countsdict[key]
        #         session.add(event)
        #     session.commit()

        print("Done.")

    except Exception as e:
        telebot.logger.debug(e)
        traceback.print_exc()
        print("Error while saving the contsdict")


def load_countsdict():
    countsdict.clear()
    try:
        print("Loading countsdict from file ", config.COUNTSDICT_FILENAME)
        # session = sessionmaker(bind=engine)
        session = Session()

        events = session.query(CryptoBlock).all()
        print("Got crypto block. #", len(events))

        for event in events:
            print("Loading block ", event.id)
            countsdict[event.coin_slug] = event
        # with open(config.COUNTSDICT_FILENAME) as f:
        #     countsdict = pickle.load(f)
        print("Done.")

        print("Counts Dictionnary = ", countsdict)
    except Exception as e:
        
        # Initialize with default values
        # sellerchannel = Event("Classroom", "@thesellerreview", "2019-06-09 08:15:27", "Chineese")
        # countsdict["@thesellerreview"] = sellerchannel
        telebot.logger.debug(e)
        traceback.print_exc()
        print("Error while loading the contsdict")
    finally:
        session.close()