#!/usr/bin/python

from flask import Flask, request
from Model import CryptoBlock
import requests
import telebot
import time
import datetime
import logging
import sys
import logging.handlers
import traceback
import gettext
import pickle
import threading
import Model as model
import config
import controller_helper as utils
from api_exceptions import *


bot = telebot.TeleBot(config.API_TOKEN, threaded=False)

# Create flask app
app = Flask(__name__)

# Logging handling
handler = logging.StreamHandler(sys.stdout)
filehandler = logging.handlers.RotatingFileHandler(config.APP_LOG_FILENAME, maxBytes=2000000, backupCount=5)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
filehandler.setFormatter(formatter)
handler.setFormatter(formatter)

telebot.logger.addHandler(handler)
telebot.logger.addHandler(filehandler)
telebot.logger.setLevel(logging.INFO)



# Dictionnary that holds the current operations of the user
usersdict = {}

# Dictionnary that holds the current threads running for a countdown
threadsdict = {}


class BlockWatcher(threading.Thread):

    def __init__(self, thread_id, coin_slug):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.coin_slug = coin_slug
        self.name = "Thread-{}".format(coin_slug)

    def run(self):
        print("Starting ", self.name)
        # Check if new block is available every 25 seconds
        while True:
            check_for_crypto_block(self.coin_slug)
            time.sleep(25)

        print("Exiting ", self.name)


@app.route('/' + config.SECRET, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if not utils.is_moderator(message):
        bot.send_message(message.chat.id, config.NOT_MODERATOR_MESSAGE, parse_mode='HTML')
    else:
        message_text = utils.get_help_text()
        bot.send_message(message.chat.id, message_text, parse_mode='HTML')


@bot.message_handler(commands=['stats'])
def pull_stats(message):
    
    if not utils.is_moderator(message):
        bot.send_message(message.chat.id, config.NOT_MODERATOR_MESSAGE, parse_mode='HTML')
    else:
        try:
            print("Call", message)
            chat_id = message.chat.id
            print("message.chat.id = ", chat_id)
            print("message.chat.type = ", message.chat.type)
            print("message.message_id = ", message.message_id)

            command_length = len(message.text.split(" "))
            if command_length > 2:
                print_wallet_statistics(message)  # This is a request for a wallet details
            elif command_length == 2:
                print_coin_statistics(message)  # This is a request for a coin details
            else:
                message_text = "You haven't specified any coin. \n{}".format(utils.get_help_text())
                bot.send_message(message.chat.id, message_text)

        except ApidatanotfoundException as dataerror:
            telebot.logger.debug(dataerror)
            traceback.print_exc()
            bot.send_message(message.chat.id, dataerror.message, parse_mode='HTML')
            
        except Exception as e:
            telebot.logger.debug(e)
            traceback.print_exc()
            bot.send_message(message.chat.id, config.FATAL_ERROR_MESSAGE)
        finally:
            # Save the data
            model.save_countsdict()


@bot.message_handler(commands=['miners'])
def pull_miners(message):

    if not utils.is_moderator(message):
        bot.send_message(message.chat.id, config.NOT_MODERATOR_MESSAGE, parse_mode='HTML')
    else:
        try:
            print("Call", message)
            print("message.chat.id = ", message.chat.id)
            print("message.chat.type = ", message.chat.type)
            print("message.message_id = ", message.message_id)

            command_length = len(message.text.split(" "))
            if command_length == 2:
                # This is a request for a coin details
                print_miners_statistics(message)
            else:
                message_text = "You haven't specified any coin. \n{}".format(utils.get_help_text())
                bot.send_message(message.chat.id, message_text, parse_mode='HTML')

        except ApidatanotfoundException as dataerror:
            telebot.logger.debug(dataerror)
            traceback.print_exc()
            bot.send_message(message.chat.id, dataerror.message, parse_mode='HTML')
        except ApidatacomputeException as dataerror:
            telebot.logger.debug(dataerror)
            traceback.print_exc()
            bot.send_message(message.chat.id, dataerror.message, parse_mode='HTML')
        except DataformatErrorException as dataerror:
            telebot.logger.debug(dataerror)
            traceback.print_exc()
            bot.send_message(message.chat.id, dataerror.message, parse_mode='HTML')
        except Exception as e:
            telebot.logger.debug(e)
            traceback.print_exc()
            bot.send_message(message.chat.id, config.FATAL_ERROR_MESSAGE)
        finally:
            # Save the data
            model.save_countsdict()


def print_wallet_statistics(message):
    coin = utils.get_coin_from_command(message.text)
    wallet = utils.get_wallet_from_command(message.text)

    if "" is not coin and "" is not wallet:
        statistics = model.get_coin_wallet_statistics(coin, wallet)
        telebot.logger.info("Wallet statistics are {}".format(statistics['stats']))
        statistics_keys = statistics.keys()
        print(statistics_keys)
        telebot.logger.info(statistics['stats'])

        hashrate = statistics['hashrate'] if 'hashrate' in statistics_keys else config.DATANOTFOUND_STR
        workers_online = statistics['workersOnline'] if 'workersOnline' in statistics_keys else config.DATANOTFOUND_STR
        blocksfound = statistics['stats']['blocksFound'] if 'stats' in statistics_keys and 'blocksFound' in statistics['stats'].keys() else config.DATANOTFOUND_STR

        fhashrate = utils.format_hashrate(hashrate)
        fwallet = utils.format_minerpage_link(model.get_coin_root_url(coin), wallet)

        response_text = "Here are the stats for the wallet {} for coin {}\nHashrate: {}\nWorkers online: {}\nBlocksfound: {}".format(fwallet, coin, fhashrate, workers_online, blocksfound)
        bot.send_message(message.chat.id, response_text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        message_text = "The coin {} or wallet address {} is not valid".format(coin, wallet)
        bot.send_message(message.chat.id, message_text)


def print_coin_statistics(message):
    coin = utils.get_coin_from_command(message.text)

    if "" is not coin:
        statistics = model.get_coin_statistics(coin)
        telebot.logger.info("Coin statistics are {}".format(statistics))
        statistics_keys = statistics.keys()
        print(statistics_keys)

        hashrate = statistics['hashrate'] if 'hashrate' in statistics_keys else config.DATANOTFOUND_STR
        last_block_found = statistics['stats']['lastBlockFound'] if 'stats' in statistics_keys and 'lastBlockFound' in statistics['stats'].keys() else config.DATANOTFOUND_STR
        n_shares = statistics['stats']['nShares'] if 'stats' in statistics_keys and 'nShares' in statistics['stats'].keys() else config.DATANOTFOUND_STR
        round_shares = statistics['stats']['roundShares'] if 'stats' in statistics_keys and 'roundShares' in statistics['stats'].keys() else config.DATANOTFOUND_STR
        miners_online = statistics['minersTotal'] if 'minersTotal' in statistics_keys else config.DATANOTFOUND_STR
        
        network_hashrate = config.DATANOTFOUND_STR  # Set initial values
        total_variance = config.DATANOTFOUND_STR  # Set initial values
        if last_block_found != config.DATANOTFOUND_STR:
            found_block = get_block_by_timestamp(coin, last_block_found)

            # Extract the values
            difficulty = found_block['difficulty'] if found_block != config.DATANOTFOUND_STR else config.DATANOTFOUND_STR
            blocktime = found_block['timestamp'] if found_block != config.DATANOTFOUND_STR else config.DATANOTFOUND_STR
            network_hashrate = utils.compute_network_hashrate(difficulty, blocktime)
            total_variance = utils.compute_coin_total_variance(difficulty, round_shares)

        fhashrate = utils.format_hashrate(hashrate)
        fnetwork_hashrate = utils.format_networkhasrate(network_hashrate)
        flast_block_found = utils.format_timeenlapsed(last_block_found)
        ftotal_variance = utils.format_coin_total_variance(total_variance)

        response_text = "Here are the stats for the coin <b>{}</b>\nHashrate: {}\nNetwork hashrate: {}\nLast block found: {}\nTotal variance: {}\nMiners online: {}".format(coin, fhashrate, fnetwork_hashrate, flast_block_found, ftotal_variance, miners_online)
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')
    else:
        message_text = "You haven't specified any coin. \n{}".format(utils.get_help_text())
        bot.send_message(message.chat.id, message_text)


def print_miners_statistics(message):
    coin = utils.get_coin_from_command(message.text)
    coin_url = model.get_coin_root_url(coin)

    if "" is not coin:
        statistics = model.get_miners_statistics(coin)
        telebot.logger.info("Miners coin statistics are {}".format(statistics))
        statistics_keys = statistics.keys()
        print(statistics_keys)

        miners = statistics['miners'] if 'hashrate' in statistics_keys else config.DATANOTFOUND_STR
        
        response_text = "Here are the miners for the coin {}".format(coin)
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

        # Send a message for each miners
        for key in miners.keys():
            minerlink = utils.format_minerpage_link(coin_url, key)
            miner_statistics = model.get_miner_wallet_statistics(coin, key)
            miner_statistics_keys = miner_statistics.keys()

            hashrate = miner_statistics['hashrate'] if 'hashrate' in miner_statistics_keys else config.DATANOTFOUND_STR
            workers_total = miner_statistics['workersTotal'] if 'workersTotal' in miner_statistics_keys else config.DATANOTFOUND_STR

            fhashrate = utils.format_hashrate(hashrate)

            message_text = "Miner {}\nHashrate: {}\nTotal workers: {}".format(minerlink, fhashrate, workers_total)
            bot.send_message(message.chat.id, message_text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        message_text = "You haven't specified any coin. \n{}".format(utils.get_help_text())
        bot.send_message(message.chat.id, message_text)


def print_new_block_details(crypto_block):
    ftimestamp = utils.format_block_timestamp(crypto_block.timestamp) 
    fheight = utils.format_block_height(crypto_block.height)
    fdifficulty = utils.format_difficulty(crypto_block.difficulty)
    fhash = crypto_block.hash

    message_text = "New block found.\nCoin: <b>{}</b>\nHeight: {}\nTimestamp: {}\nMiner: {}".format(crypto_block.coin_slug, fheight, 
                                        ftimestamp, crypto_block.finder)
    bot.send_message(config.CHANNEL_USERNAME, message_text, parse_mode='HTML')


def check_for_crypto_block(coin_slug):
    telebot.logger.info("check_for_crypto_block > starting the block checker in a thread.")
    telebot.logger.info("check_for_crypto_block > coin slug is {}".format(coin_slug))

    try:
        # Pull the last crypto block
        last_block_data = model.get_cryptoblock_by_coinslug(coin_slug)

        if last_block_data == config.DATANOTFOUND_STR:
            telebot.logger.info("No last block data found. Creating a fresh one.")
            last_block_data = CryptoBlock(coin_slug)
            model.save_cryptoblock(coin_slug, last_block_data)


        # Get the actual block timestamp
        current_block_timetamp = get_coin_lastBlockFound(coin_slug)
        last_block_timetamp = last_block_data.timestamp

        telebot.logger.info("Comparing timestamps : current : {} vs last {}".format(current_block_timetamp, last_block_timetamp))
        if current_block_timetamp != last_block_timetamp:

            telebot.logger.info("Current {} and last {} timestamps are different. NOTIFYING".format(current_block_timetamp, last_block_timetamp))
            # We update the block
            new_block = get_block_by_timestamp(coin_slug, current_block_timetamp)

            if new_block is not None and new_block != config.DATANOTFOUND_STR:
                last_block_data.height = new_block['height']
                last_block_data.timestamp = new_block['timestamp']
                last_block_data.difficulty = new_block['difficulty']
                last_block_data.shares = new_block['shares']
                last_block_data.uncle = new_block['uncle']
                last_block_data.uncleHeight = new_block['uncleHeight']
                last_block_data.orphan = new_block['orphan']
                last_block_data.hash = new_block['hash']
                last_block_data.finder = new_block['finder']
                last_block_data.reward = new_block['reward']

                # Save the last block data
                model.save_cryptoblock(coin_slug, last_block_data)

                # We send an update to the channel with the new information.
                print_new_block_details(last_block_data)
            else:
                telebot.logger.info("No block found with the timestamp {}".format(current_block_timetamp))
        else:
            telebot.logger.info("Current timestamp is the same as last one. NO NOTIFICATION")

    except Exception as e:
        telebot.logger.debug(e)
        traceback.print_exc()
        # bot.send_message(message.chat.id, config.FATAL_ERROR_MESSAGE)


def get_coin_lastBlockFound(coin_slug):
    
    statistics = model.get_coin_statistics(coin_slug)
    #telebot.logger.info("get_coin_lastBlockFound > Coin statistics are {}".format(statistics))
    statistics_keys = statistics.keys()
    print(statistics_keys)

    last_block_found = statistics['stats']['lastBlockFound'] if 'stats' in statistics_keys and 'lastBlockFound' in statistics['stats'].keys() else config.DATANOTFOUND_STR
    
    telebot.logger.info("get_coin_lastBlockFound > Last block found is {}".format(last_block_found))

    return last_block_found


def get_block_by_timestamp(coin_slug, timestamp):

    telebot.logger.info("get_block_by_timestamp > Timestamp is {}".format(timestamp))
    statistics = model.get_blocks_statistics(coin_slug)
    telebot.logger.info("get_block_by_timestamp > Coin statistics are ", statistics)
    statistics_keys = statistics.keys()
    print(statistics_keys)

    # Checking candidates blocks
    candidates_blocks = statistics['candidates'] if 'candidates' in statistics_keys else config.DATANOTFOUND_STR
    if candidates_blocks != config.DATANOTFOUND_STR and candidates_blocks is not None:
        for block in candidates_blocks:
            telebot.logger.info("Looking into the candicates block {}".format(block))
            if block['timestamp'] == timestamp:
                return block
    else:
        telebot.logger.info("No candicates block found.")

    # Checking immature blocks
    immature_blocks = statistics['immature'] if 'immature' in statistics_keys else config.DATANOTFOUND_STR
    if immature_blocks != config.DATANOTFOUND_STR and immature_blocks is not None:
        for block in immature_blocks:
            telebot.logger.info("Looking into the immature block {}".format(block))
            if block['timestamp'] == timestamp:
                return block
    else:
        telebot.logger.info("No immatures block found.")
    

    # Checking mature blocks
    mature_blocks = statistics['matured'] if 'matured' in statistics_keys else config.DATANOTFOUND_STR
    if mature_blocks != config.DATANOTFOUND_STR and mature_blocks is not None:
        for block in mature_blocks:
            telebot.logger.info("Looking into the mature block {}".format(block))
            if block['timestamp'] == timestamp:
                return block
    else:
        telebot.logger.info("No mature block found.")

    return config.DATANOTFOUND_STR


# bot.polling()
try:
    model.load_countsdict()
    
    i = 1
    for key in config.COIN2URL_MAP.keys():
        block_watcher = BlockWatcher(i, key)
        block_watcher.setDaemon(True)
        block_watcher.start()
        
        threadsdict[key] = block_watcher
        i = i + 1

    # Start telebot process
    bot.polling()

    model.save_countsdict()

    # Stop all the threads if they are still alive

except Exception as e:
    telebot.logger.debug(e)
    time.sleep(1)
    traceback.print_exc()
    model.save_countsdict()