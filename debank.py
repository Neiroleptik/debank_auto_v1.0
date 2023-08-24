import sys
import time
import atexit
from io import StringIO
import pyautogui
import sqlite3
import urllib.parse
import datetime
import random
from auto_metamask import *
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_words_from_file(filename):
    """
    :param filename: In collections[lead_...(path_to_txt)]
    :return: String
    """
    with open(filename, 'r') as file:
        words = file.readlines()
    return [word.strip() for word in words]


def generate_post():
    num_collections_to_pick = random.randint(4, 6)
    selected_collections = random.sample(collections, num_collections_to_pick)

    sentence = [random.choice(collection) for collection in selected_collections]

    sentence[0] = sentence[0].capitalize()

    return ' '.join(sentence)


def get_all_mnemonics():
    """
    :return: mnemonics
    """
    cursor.execute("SELECT mnemonic FROM accounts")
    results = cursor.fetchall()
    return [item[0] for item in results]


def get_link_for_account(mnemonic):
    """
    :param mnemonic: use for comparison
    :return: 0 or None
    """
    cursor.execute("SELECT link FROM accounts WHERE mnemonic=?", (mnemonic,))
    result = cursor.fetchone()
    return result[0] if result else None


def update_link_for_account(mnemonic, link):
    """
    :param mnemonic: using for comparison
    :param link: taking from website in function: auth()
    """
    cursor.execute("UPDATE accounts SET link=? WHERE mnemonic=?", (link, mnemonic))
    conn.commit()


def get_all_links_except_current(mnemonic):
    """
    :param mnemonic: using for comparison
    :return: links
    """
    cursor.execute("SELECT link FROM accounts WHERE mnemonic!=?", (mnemonic,))
    results = cursor.fetchall()
    return [item[0] for item in results if item[0]]


def get_token(site_key, url, api_key):
    """
        :param site_key: Site key (ReCaptcha)
        :type site_key: String
        :param url: Website Url
        :type url: String
        :param api_key: Anti-captcha.com API-Key
        :type api_key: String
    """

    client = AnticaptchaClient(api_key)
    task = NoCaptchaTaskProxylessTask(website_url=url, website_key=site_key)
    job = client.createTask(task)
    job.join()
    return job.get_solution_response()


def new_post(post):
    """
        :param post: Your text for posting
        :type post: String
    """

    driver.get('https://debank.com/new-stream')
    time.sleep(3)
    try:
        restriction_null = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                        '.PostFooter_footerSelect__39GeV')))
        restriction_null.click()

        checkbox = wait.until(EC.presence_of_element_located((By.NAME, 'has_web3_id')))
        actions = ActionChains(driver)
        actions.move_to_element(checkbox).click().perform()

        button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".Button_button__2mB3w.Button_is_primary__1Xhp7.CommentEligibilityModal_postBtn__37UgD")))
        button.click()
        time.sleep(2)
        input = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.RichTextEditor_editorContainer__3xx5l')))
        input.send_keys(post)
        time.sleep(2)
        post_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.PostFooter_submitButton__12qgb')))
        post_button.click()
        time.sleep(3)
    except:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Post:--Error--:Debank ban your requests or Reached Day LIMIT. Change YOUR IP or skip.')
        pass


def post_comment(comment):
    """
        :param comment: Your text for comment. В коде аргумент наследуется от функции 'trust_comment'
        :type comment: String
    """

    COMMENTS_COUNT = 0
    wait = WebDriverWait(driver, 10)

    try:
        container = driver.find_element(By.CSS_SELECTOR, '.ArticleContent_leftOps__2Fpq4')

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Comment:--Searching--')

        comment_button = container.find_element(By.CSS_SELECTOR, '.ArticleContent_operation__1yHNs')
        # driver.execute_script("arguments[0].click();", comment_button)
        comment_button.click()
        time.sleep(1)

        input_area = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.Input_textarea__B9Uh1'))
        )
        driver.execute_script(f"arguments[0].value = '{comment}';", input_area)
        input_area.send_keys(".")
        time.sleep(1)

        try:
            btn_post = pyautogui.locateOnScreen('images/post.jpg', confidence=0.7)
            if btn_post is not None:
                btn_post_center = pyautogui.center(btn_post)
                pyautogui.click(btn_post_center)
            time.sleep(2)
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Comment:--Success--')
            COMMENTS_COUNT += 1

        except Exception as ex:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Comment:--Error--: Could not post')
            pass

    except Exception as ex:
        message = str(ex).split('\n')[0]
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Comment:--Error--:{message}')
        pass

    return COMMENTS_COUNT


def auth(mnemonic, api_key, SLEEP_BEFORE_CONFIRM_LOAD, SLEEP_AFTER_VERIFY_CLICK):
    """
        :param mnemonic: Mnemonic phrase (Only 12 words)
        :type mnemonic: String
        :param api_key: Anti-captcha.com API-Key
        :type api_key: String
        :param SLEEP_BEFORE_CONFIRM_LOAD:
        :type SLEEP_BEFORE_CONFIRM_LOAD: Float
        :param SLEEP_AFTER_VERIFY_CLICK:
        :type SLEEP_AFTER_VERIFY_CLICK: Float
    """
    MAX_RETRIES = 3
    retries = 0
    step = "start"

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{current_time}:--JOB STARTED--')
    print(f'{current_time}:Auth:--Setup MetaMask--')

    setupMetamask(
        mnemonic, 'password1234')
    time.sleep(2)
    btn_pick = pyautogui.locateOnScreen('images/chain_pick.jpg', confidence=0.5)
    if btn_pick is not None:
        btn_pick_center = pyautogui.center(btn_pick)
        pyautogui.click(btn_pick_center)
        pyautogui.click(btn_pick_center)
    time.sleep(2)

    btn_add_chain = pyautogui.locateOnScreen('images/addChain.jpg', confidence=0.5)
    if btn_add_chain is not None:
        btn_add_chain_center = pyautogui.center(btn_add_chain)
        pyautogui.click(btn_add_chain_center)
    time.sleep(2)

    btn_add_bsc = pyautogui.locateOnScreen('images/add_bsc.png', confidence=0.5)
    if btn_add_bsc is not None:
        x_right = btn_add_bsc.left + btn_add_bsc.width - 6
        y_center = btn_add_bsc.top + btn_add_bsc.height // 2
        pyautogui.click(x_right, y_center)
    time.sleep(2)
    btn_confirm = pyautogui.locateOnScreen('images/confirm_add.jpg', confidence=0.5)
    if btn_confirm is not None:
        btn_confirm_center = pyautogui.center(btn_confirm)
        pyautogui.click(btn_confirm_center)
    time.sleep(2)

    btn_switch_bsc = pyautogui.locateOnScreen('images/switch_to_bsc.jpg', confidence=0.5)
    if btn_switch_bsc is not None:
        btn_switch_bsc_center = pyautogui.center(btn_switch_bsc)
        pyautogui.click(btn_switch_bsc_center)
        time.sleep(2)

    while retries < MAX_RETRIES:
        try:
            driver.get('https://debank.com')
            driver.refresh()
            time.sleep(3)
            if step in ["start", "verify"]:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".Button_button__1yaWD.Button_is_primary__1"
                                                                        "b4PX.UserInfoBtn_mainBtn__6YIGn"))).click()
                time.sleep(1)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="MetaMask"]'))).click()
                time.sleep(3)
                if step == 'start':
                    # Нажимаем на Sign
                    wait.until(EC.element_to_be_clickable((By.XPATH,
                                                           '//button[@class="Button_button__1yaWD'
                                                           ' Button_is_primary__1b4PX '
                                                           'SignLoginModal_loginBtn__2RIf1"]'))).click()
                    time.sleep(SLEEP_BEFORE_CONFIRM_LOAD)
                    # Подтверждаем [MetaMask]
                    meta_confirm = pyautogui.locateOnScreen('images/confirm.jpg', confidence=0.5)
                    if meta_confirm is not None:
                        meta_cnfm = pyautogui.center(meta_confirm)
                        pyautogui.click(meta_cnfm)
                    else:
                        retries += 1
                        print(f"Error during:Auth: Retry {retries}/{MAX_RETRIES}.")
                        continue

                    time.sleep(2)
                    # Подтверждаем [MetaMask]
                    meta_connect = pyautogui.locateOnScreen('images/connect.jpg', confidence=0.5)
                    if meta_connect is not None:
                        meta_cnct = pyautogui.center(meta_connect)
                        pyautogui.click(meta_cnct)
                        step = 'verify'
                    else:
                        retries += 1
                        print(f"Error during:Auth: Retry {retries}/{MAX_RETRIES}.")
                        continue

            if step == "verify":
                
                wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Verify"]'))).click()

                time.sleep(SLEEP_AFTER_VERIFY_CLICK)

                # Находим iframe с ReCAPTCHA и извлекаем site_key
                iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]'))
                )
                src = iframe.get_attribute('src')
                parsed_url = urllib.parse.urlparse(src)
                site_key = urllib.parse.parse_qs(parsed_url.query)['k'][0]

                # Получаем решение от Anti-captcha.com
                captcha = get_token(site_key, 'https://debank.com', api_key)

                # Делаем инъекцию решения с JS
                driver.execute_script(
                    'document.getElementById("g-recaptcha-response").innerHTML = "{}";'.format(captcha))
                time.sleep(1)
                try:
                    driver.execute_script(f"___grecaptcha_cfg.clients[0].P.P.callback('{captcha}')")
                except:
                    try:
                        driver.execute_script(f"___grecaptcha_cfg.clients[0].O.O.callback('{captcha}')")
                    except:
                        try:
                            driver.execute_script(f"___grecaptcha_cfg.clients[0].l.l.callback('{captcha}')")
                        except:
                            retries += 1
                            continue

                time.sleep(5)
                # Подтверждаем [MetaMask]
                meta_login = pyautogui.locateOnScreen('images/login.jpg', confidence=0.5)
                if meta_login is not None:
                    meta_lgn = pyautogui.center(meta_login)
                    pyautogui.click(meta_lgn)
                time.sleep(3)

                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Auth:--Authentication Success--')
                # Проверка наличия ссылки в базе данных для этого аккаунта
                link = get_link_for_account(mnemonic)

                # Если ссылки нет, добавляем ее
                if not link:
                    current_url = driver.current_url
                    new_link = current_url + "/stream"
                    update_link_for_account(mnemonic, new_link)

                break

        except ElementClickInterceptedException:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time}:Auth: The MetaMask page probably didn't load. Check your network connection")
            driver.quit()
            sys.exit(1)


        except Exception as e:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time}:Error during auth: {e}. Retry {retries + 1}/{MAX_RETRIES}.")
            retries += 1

    if retries == MAX_RETRIES:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{current_time}:Auth:Error:Changed Callback Path. Please DM soft Author!")
        driver.quit()
        sys.exit(1)

    time.sleep(2)


def registerL2(chain_id):
    """
    :param chain_id: 0 - Ethereum; 1 - BSC; 2 - OP; 3 - Arbitrum; 4 - Polygon
    :type chain_id: Integer
    """
    try:
        acc_status_l2 = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(@class, 'L2AccountBalance_hoverText__"
                                                        "btQ5F')]/span[text()='DeBank L2 Unregistered']")))
        if acc_status_l2 is not None:

            try:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:L2:--Try Registration--')

                acc_status_l2.click()

                btn_reg = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'AccountWarningItem_button__3fO9x')][text()='Register']")))
                btn_reg.click()
                chains = wait.until(
                    EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '.AccountModal_chainItem__1v6wZ')))
                chains[chain_id].click()
                btn_next = driver.find_element(By.XPATH,
                                               '//button[text()="Next"]')
                btn_next.click()

                btn_request = wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                           '//button[text()="Send request"]')))
                btn_request.click()
                time.sleep(10)
                
                btn_confirm = pyautogui.locateOnScreen('images/confirmTransaction_1.jpg', confidence=0.6)
                if btn_confirm is not None:
                    btn_confirm_center = pyautogui.center(btn_confirm)
                    pyautogui.click(btn_confirm_center)
                time.sleep(10)
                
                btn_confirm_tx = pyautogui.locateOnScreen('images/confirmTransaction.jpg', confidence=0.5)
                if btn_confirm_tx is not None:
                    btn_confirm_tx_center = pyautogui.center(btn_confirm_tx)
                    pyautogui.click(btn_confirm_tx_center)
                    
                time.sleep(3)
                print(f'{current_time}:L2:--Success--')

            except Exception as ex:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                message = str(ex).split('\n')[0]
                print(f'{current_time}:L2:{message}')
                pass

        else:
            pass
            
    except TimeoutException:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:L2:{"L2 registered!"}')
        pass
    time.sleep(5)


def trust_comment(url, comments):
    """
        :param url: Account stream url
        :type url: String
        :param comment: Your text for comment
        :type comment: String
    """
    comment = random.choice(comments)
    LIKES_COUNT = 0

    driver.get(url)
    time.sleep(5)
    try:
        COMMENTS_COUNT = post_comment(comment)
    except:
        pass
    try:
        follow = driver.find_element(By.XPATH, '//button[contains(@class, "HeaderInfo_followBtn__2mm4F") and '
                                               '(text()="Follow" or text()="Follow Back")]')
        if follow is not None:
            follow.click()
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Following:--Followed--')
    except NoSuchElementException:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Following:Followed')
    except:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Following:--ERROR--: UNDEFINED')
    while True:
        try:

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ArticleContent_rightOps__2j9PM')))
            container = driver.find_element(By.CSS_SELECTOR, '.ArticleContent_rightOps__2j9PM')

            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Trust:--Find--')

            like_buttons = container.find_elements(By.CSS_SELECTOR, '.ArticleContent_operation__1yHNs')

            if like_buttons and not 'ArticleContent_isTrust__2yyvS' in like_buttons[0].get_attribute("class"):
                like_buttons[0].click()
                time.sleep(0.5)

                classes_after_click = like_buttons[0].get_attribute('class')

                if 'ArticleContent_isTrust__2yyvS' in classes_after_click:
                    print(f'{current_time}:Trust:--Success--')
                    LIKES_COUNT += 1
                else:
                    print(f'{current_time}:Trust:--Failed--: Possible insufficient balance or other issue')

        except Exception as ex:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = str(ex).split('\n')[0]
            print(f'{current_time}:Trust:--Error--:{message}')


            pass
        time.sleep(2)

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Trust:--Success--:Count: {LIKES_COUNT}')
        print(f'{current_time}:Comments:--Success--:Count: {COMMENTS_COUNT}')

        break


def post_comment_with_circle(comment):
    """
        :param comment: Your text for comment. В коде аргумент наследуется от функции 'trust_comment'
        :type comment: String
    """

    COMMENTS_COUNT = 0
    wait = WebDriverWait(driver, 10)

    try:
        containers = driver.find_elements(By.CSS_SELECTOR, '.ArticleContent_leftOps__2Fpq4')
        for container in containers:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Comment:--Searching--')

            comment_button = container.find_element(By.CSS_SELECTOR, '.ArticleContent_operation__1yHNs')
            driver.execute_script("arguments[0].click();", comment_button)

            time.sleep(1)

            input_area = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.Input_textarea__B9Uh1'))
            )
            driver.execute_script(f"arguments[0].value = '{comment}';", input_area)
            input_area.send_keys(".")
            time.sleep(1)

            try:
                btn_post = pyautogui.locateOnScreen('images/post.jpg', confidence=0.7)
                if btn_post is not None:
                    btn_post_center = pyautogui.center(btn_post)
                    pyautogui.click(btn_post_center)
                time.sleep(2)
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Comment:--Success--')
                COMMENTS_COUNT += 1

            except Exception as ex:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Comment:--Error--: Could not post')
                pass

    except Exception as ex:
        message = str(ex).split('\n')[0]
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Comment:--Error--:{message}')
        pass

    return COMMENTS_COUNT


def tr_com_fol_hot(comments):
    """
        :param url: Account stream url
        :type url: String
        :param comment: Your text for comment
        :type comment: String
    """
    url = 'https://debank.com/stream?tab=hot'
    comment = random.choice(comments)
    LIKES_COUNT = 0

    driver.get(url)
    time.sleep(5)

    try:
        follows = driver.find_elements(By.CSS_SELECTOR, '.Button_button__1yaWD.Button_is_text__1RdGI.Button_is_ghost_'
                                                        '_2b4Vm.FollowButton_followBtnV2__2X4l9[aria-disabled="false"]')
        for follow in follows:
            if follow is not None:
                follow.click()
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Following:--Followed--')
    except NoSuchElementException:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Following:Followed')
    except:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Following:--ERROR--: UNDEFINED')

    while True:
        try:

            containers = driver.find_elements(By.CSS_SELECTOR, '.ArticleContent_rightOps__2j9PM')

            for container in containers:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Trust:--Find--')

                like_buttons = container.find_elements(By.CSS_SELECTOR, '.ArticleContent_operation__1yHNs')


                if like_buttons and not 'ArticleContent_isTrust__2yyvS' in like_buttons[0].get_attribute("class"):
                    like_buttons[0].click()
                    time.sleep(0.5)

                    classes_after_click = like_buttons[0].get_attribute('class')

                    if 'ArticleContent_isTrust__2yyvS' in classes_after_click:
                        print(f'{current_time}:Trust:--Success--')
                        LIKES_COUNT += 1
                    else:
                        print(f'{current_time}:Trust:--Failed--: Possible insufficient balance or other issue')

        except Exception as ex:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = str(ex).split('\n')[0]
            print(f'{current_time}:Trust:--Error--:{message}')
            pass

        time.sleep(2)
        
        try:
            COMMENTS_COUNT = post_comment_with_circle(comment)
        except:
            pass

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Trust:--Success--:Count: {LIKES_COUNT}')
        print(f'{current_time}:Comments:--Success--:Count: {COMMENTS_COUNT}')

        break


def vote(links_count, work_time):
    """
    :param links_count:
    :type links_count: Integer
    :param work_time:
    :type work_time: Float
    """
    NO_CHANGE_COUNT = 0

    driver.get('https://debank.com/proposal?order_dy=-create_at&q=')

    last_height = driver.execute_script("return document.body.scrollHeight")
    start_time = datetime.datetime.now()

    links = []

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{current_time}:Vote:--Parsing Start--')
    while len(links) < 50:
        time.sleep(2)
        votes = driver.find_elements(By.CSS_SELECTOR, 'div[data-index] > a[href]')

        for vote in votes:
            changed_button = vote.find_elements(By.CSS_SELECTOR, '.ProposalMisc_isVote__pQ3Am')
            if changed_button:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Vote:--Voted before. Skipping--')
                continue

            link = vote.get_attribute('href')
            if link not in links:
                links.append(link)

        if len(links) >= links_count:  # >= n - Links count
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Vote:--Parsing Ended--')
            break

        driver.execute_script("window.scrollBy(0, 900);")
        current_time = datetime.datetime.now()
        elapsed_time = (current_time - start_time).seconds
        if elapsed_time > work_time:  # work time
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{current_time}:Vote:--Time limit reached--')
            break
        time.sleep(SCROLL_PAUSE_TIME)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            NO_CHANGE_COUNT += 1
            if NO_CHANGE_COUNT >= 3:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'{current_time}:Vote:--Content not loading--')
                break
        else:
            NO_CHANGE_COUNT = 0

        last_height = new_height

    for link in links[:50]:
        driver.get(link)
        button = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div.ProposalMisc_proposalVote__ziR-S svg.ProposalMisc_voteIcon__1GGau')))

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time}:Vote:--Voting--')

        button.click()
        time.sleep(1)

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{current_time}:Vote:--Voting Ended--')


class DualOutput:
    def __init__(self, original_stdout):
        self.stdout = original_stdout
        self.buffer = StringIO()

    def write(self, message):
        self.stdout.write(message)
        self.buffer.write(message)

    def getvalue(self):
        return self.buffer.getvalue()

    def flush(self):
        self.stdout.flush()


if __name__ == '__main__':
    """
        func: auth
        info: Setup MetaMask --> Auth on Debank.com

        func: registerL2
        info: Register L2 Debank account on BSC Chain ONLY for now.
        
        func: post
        info: Auto-posting.
        
        func: trust_comment() / tr_com_fol_hot()
        info: Trust available posts in link.
              (comment) Comment available posts in link.
              (follow) Following.

        func: vote
        info: Parse ~50 links to voting if they don`t voted. Get pages and Voting.
    """
    original_stdout = sys.stdout
    dual_output = DualOutput(original_stdout)
    sys.stdout = dual_output

    # Upload words
    collections = [
        load_words_from_file('words/collection1.txt'),
        load_words_from_file('words/collection2.txt'),
        load_words_from_file('words/collection3.txt'),
        load_words_from_file('words/collection4.txt'),
        load_words_from_file('words/collection5.txt'),
        load_words_from_file('words/collection6.txt'),
    ]

    # Connect to DB
    conn = sqlite3.connect('accounts.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        mnemonic TEXT NOT NULL,
        link TEXT
    )
    ''')
    conn.commit()

    with open("words/comments.txt", "r") as file:
        comments = [line.strip() for line in file]

    mnemonics = get_all_mnemonics()
    API_KEY = ''  # API-key anti-captcha.com
    CHAIN_ID = 1  # Chain ID (Basic = 1 -- BSC Chain) DON`T TOUCH

    LINKS_COUNT = 15  # vote(links_count, ..)
    WORK_TIME = 15  # vote(.., work_time)
    SCROLL_PAUSE_TIME = 4
    SLEEP_BEFORE_CONFIRM_LOAD = 15  # Can change 8 - 15 sec, lower is dangerous
    SLEEP_AFTER_VERIFY_CLICK = 15  # Can change 8 - 15 sec, lower is dangerous
    count = 1  # Count of global circles (accounts)
    driver = None

    try:
        for mnemonic in mnemonics:
            metamask_path = downloadMetamask(
                'https://github.com/MetaMask/metamask-extension/releases/download/v10.34.0/metamask-chrome-10.34.0.zip')
            driver = setupWebdriver(metamask_path)
            actions = ActionChains(driver)
            wait = WebDriverWait(driver, 10, 1)
            auth(mnemonic, API_KEY, SLEEP_BEFORE_CONFIRM_LOAD, SLEEP_AFTER_VERIFY_CLICK)
            value_element = driver.find_element(By.CLASS_NAME, 'HeaderInfo_totalAssetInner__1mOQs')
            value_text = value_element.text
            cleaned_value_text = value_text.replace('$', '').split('\n')[0]
            value = float(cleaned_value_text)
            if value > 0.15:
                registerL2(CHAIN_ID)
            if value > 100:
                post = generate_post()
                new_post(post)
                urls = get_all_links_except_current(mnemonic)
                for url in urls:
                    trust_comment(url, comments)
                tr_com_fol_hot(comments)
            vote(LINKS_COUNT, WORK_TIME)
            print(f"Account #{count} end work!")
            count += 1
            driver.quit()

    except:
        if driver:
            driver.quit()
        print("Program Stopped")
        pass

    conn.close()

    sys.stdout = original_stdout

    with open("logs.txt", "w") as file:
        file.write(dual_output.getvalue())

    print("---LOGS SAVED TO 'logs.txt'---")
    print("---END---")
