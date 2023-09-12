import config
import datetime
import telebot


# Functions
def format_coin_total_variance(variance):
    try:
        return "{:.2f} %".format(variance)
    except Exception as e:
        telebot.logger.info("Error during format.")
        return variance


def format_hashrate(hashrate):
    try:
        nhashrate = float(hashrate)/1000000000
        return "{:.2f} GH".format(nhashrate)
    except Exception as e:
        telebot.logger.info("Error during format.")
        return hashrate

def format_networkhasrate(network_hashrate):
    try:
        nhashrate = float(network_hashrate)
        return "{:.2f} GH".format(nhashrate)
    except Exception as e:
        telebot.logger.info("Error during format.")
        return network_hashrate

def format_minerpage_link(coin_url, miner_hash):
    try:
        minerm = get_contracted_hash(miner_hash)
        return "<a href='{}/#/account/{}' target='_blank'>{}</a>".format(coin_url, miner_hash, minerm)
    except Exception as e:
        telebot.logger.info("Error during format.")
        return miner_hash


def format_block_height(height):
    try:
        return '{:,}'.format(int(height))
    except Exception as e:
        telebot.logger.info("Error during format.")
        return height


def format_block_timestamp(timestamp):
    try:
        stamp = datetime.datetime.fromtimestamp(timestamp)
        return stamp.strftime("%d/%m/%Y, %H:%M:%S")
    except Exception as e:
        telebot.logger.info("Error during format.")
        return timestamp


def format_timeenlapsed(timestamp):
    try:
        # Format the timestamp in timedelta
        stamp = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        delta = now - stamp
        return strfdelta(delta)
    except Exception as e:
        telebot.logger.info("Error during format.")
        return timestamp


def format_difficulty(difficulty):
        return difficulty


def strfdelta(tdelta):
    if tdelta.days > 0:
        fmt = "{days:02d} days, {hours:02d} hours {minutes:02d} minutes {seconds:02d} seconds ago"
    else:
        fmt = "{hours:02d} hours {minutes:02d} minutes {seconds:02d} seconds ago"

    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def format_block_height(height):
    try:
        return '{:,}'.format(int(height))
    except Exception as e:
        telebot.logger.info("Error during format.")
        return height


def compute_coin_total_variance(difficulty, roundShares):
    if difficulty != config.DATANOTFOUND_STR and roundShares != config.DATANOTFOUND_STR:
        return (float(roundShares) / float(difficulty) * 100 - 4)
    else:
        return config.DATANOTFOUND_STR


def compute_network_hashrate(difficulty, blocktime):
    if difficulty != config.DATANOTFOUND_STR and blocktime != config.DATANOTFOUND_STR:
        return (float(difficulty) / 13.3 / 1000000000)  
    else:
        return config.DATANOTFOUND_STR


def get_contracted_hash(hash):
    return hash[:8]


def get_coin_from_command(text):
    parts = text.split(" ")
    if len(parts) >= 2:
        return parts[1]
    else:
        return ""


def get_wallet_from_command(text):
    parts = text.split(" ")
    if len(parts) == 3:
        return parts[2]
    else:
        return ""

def get_help_text():
    return """
Hi there, open-etc-pool-friends bot.
I am here to display pool stats.
Commands are :
/stats [coin] - displays statistics on a coin. Possible values are : etc
/stats [coin] [walletaddress] - Display stats on a wallet address for a coin
/miners [coin]
/help - displays this help text.
/start - display this help text too.
"""


def is_moderator(message):
    
    if config.ACTIVATE_MODERATOR_FILTERING:
        user_id = message.chat.id
        username = message.chat.username
        print("Checking if the user ", username, " is a moderator")
        print("The moderator list is", config.MODERATOR_USER_NAMES)
        return username in config.MODERATOR_USER_NAMES
    else:
        # Always say yes if moderator filtering is disabled.
        return True
