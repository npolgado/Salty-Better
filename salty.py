#!usr/env/python3
import selenium, os, sys, time, math, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import webbrowser, threading

LAST_BALANCE = 0

POLLING_RATE = 1
BET_FACTOR = 0.01
BET_MAX_FACTOR = 0.1

NUM_WINS = 0
NUM_LOSSES = 0
WINRATE = 0

DID_BET = False
DID_START = False
DID_END = False

try:
    with open('salty_creds.txt') as f:
        username = str(f.readline())
        password = str(f.readline())
except:
    username = ''
    password = ''


print(f"found username = {username}, password = {password}")

options = Options()
options.add_argument("start-maximized")
options.add_experimental_option("detach", True)

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.saltybet.com")
except:
    print('ERROR GETTING WEBSITE...')
    sys.exit(1)

try:
    # logging in 
    sign_in = driver.find_element(by=By.PARTIAL_LINK_TEXT, value='Sign ').click()
    driver.implicitly_wait(1)
    user_input = driver.find_element(by=By.ID, value='email').send_keys(username)
    pass_input = driver.find_element(by=By.ID, value='pword').send_keys(password)
    driver.implicitly_wait(1)
    submit = driver.find_element(by=By.CLASS_NAME, value='Submit').click()
    driver.implicitly_wait(1)
    LAST_BALANCE = int(str(driver.find_element(by=By.ID, value="balance").text).replace(',', ''))
    th = threading.Thread(target=lambda: webbrowser.open('https://www.twitch.tv/saltybet')).start()
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

while True:
    # poll balance, odds
    balance = driver.find_element(by=By.ID, value="balance").text
    odds = driver.find_element(by=By.ID, value='odds').text

    try: # formatting
        balance = int(str(balance).replace(',', ''))
        src = odds.split()
        player1_name = src[0]
        player1_total_bet = src[1]
        player2_name = src[2]
        player2_total_bet = src[3]
    except:
        balance = LAST_BALANCE
        odds = ''

    # is odds displaying text or not? (fighting?)
    if len(odds) > 0: 
        fighting = True
        if not DID_START:
            print(f"CURRENT MATCH: {odds}\n")
            DID_START = True
    else:
        fighting = False

        # if num wins/losses was updated before, we need to assume a fight has just ended
        if DID_END: 
            DID_END = False
            DID_BET = False
            DID_START = False
        
        # if we have not bet on this betting phase, bet now
        if not DID_BET:
            
            # auto bet amount
            bet_amount = round(balance * BET_FACTOR)
            wager = driver.find_element(by=By.ID, value='wager').send_keys(bet_amount)

            # choose bet
            bet = str(input("which player should we bet on? (r/b)"))
            try:
                if re.match("(?i)r", bet):
                    player_1 = driver.find_element(by=By.ID, value='player1').click()
                    driver.implicitly_wait(1)
                elif re.match("(?i)b", bet): 
                    player_2 = driver.find_element(by=By.ID, value='player2').click()
                    driver.implicitly_wait(1)
                DID_BET = True
            except:
                print(f"ERROR COULDN'T BET ON {bet}")
                print(f"Balance = {balance} -- Winrate = {WINRATE} %\n")
        
        # if we have bet, we want to be able to change our bet unless its locked in
        else:
            print(f"Bet on {bet}\n")
            print(f"Balance = {balance} -- Winrate = {WINRATE} %\n")

            # choose bet
            bet = str(input("change bet? (r/b)"))
            try:
                if re.match("(?i)r", bet):
                    player_1 = driver.find_element(by=By.ID, value='player1').click()
                    driver.implicitly_wait(1)
                elif re.match("(?i)b", bet): 
                    player_2 = driver.find_element(by=By.ID, value='player2').click()
                    driver.implicitly_wait(1)
                DID_BET = True
            except:
                print(f"ERROR COULDN'T BET ON {bet}")
                print(f"Balance = {balance} -- Winrate = {WINRATE} %")
        
    if LAST_BALANCE > balance:
        NUM_LOSSES += 1
        DID_END = True
    elif LAST_BALANCE < balance:
        NUM_WINS += 1
        DID_END = True
    
    if NUM_WINS + NUM_LOSSES > 0:
        WINRATE = float((NUM_WINS / (NUM_WINS + NUM_LOSSES)) * 100)

    LAST_BALANCE = balance
    time.sleep(POLLING_RATE)