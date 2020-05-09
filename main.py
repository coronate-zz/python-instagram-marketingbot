from selenium import webdriver
from time import sleep
from secrets import password
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import requests
import re
import os
import pandas as pd
import pdb
import random
from datetime import date


def sleep_random(time):
    time = time * random.randint(0, 5) + random.random()
    sleep(time)


def iterate_elements_onxpath(xpath, attribute, iterative_elements, filesystem, hashtag, time=3):
    """
    # Since there is ot an easy way to iterate elements with selenium I'm using
    # BeautifulSoup to get dictionaries that conatin all the elements inside a bigger
    # Object. In this case I'm iterating through all posts in xpath_element section.

    xpath: The xpath of the object that contains all the elements we want to iterate
    attribute: the attribute we want to take aout of the xpath elemente. This
    attribute is passed to selenium.
    iterative_elements: HTML element type of the objects we want to iterate over
    """

    xpath_element = my_bot.driver.find_element_by_xpath(xpath)
    attribute_value = xpath_element.get_attribute(attribute)
    print("attribute_value: {}".format(attribute_value))
    # BS4
    html_content = my_bot.driver.page_source
    bsObj = BeautifulSoup(html_content)
    galleries = bsObj.findAll(
        iterative_elements, {attribute: re.compile(attribute_value)})

    for gallery in galleries:
        likeandfollow(gallery, my_bot, filesystem, hashtag, 10, 2)


def likeandfollow(gallery, my_bot, filesystem, hashtag, maxlikes=10, time=2):
    for n, post in enumerate(gallery.find_all("a")):
        if n > maxlikes:  # We dont want to wait all day for liking and following everyone
            break
        post_href = post["href"]
        post_xpath = '//a[@href="' + post_href + '"]'
        # WebDriverWait(my_bot.driver, 10).until(
        #    expected_conditions.visibility_of_element_located((By.XPATH, post_xpath)))
        sleep_random(time)
        my_bot.driver.find_element_by_xpath(post_xpath).click()
        sleep_random(time)
        postid = my_bot.get_postid()
        sleep_random(time)
        username = my_bot.get_username()
        print(
            "username: {} - postid: {} - post_href: {} ".format(username, postid, post_href))

        if not filesystem.detect_follower(username):
            # User is NOT in
            filesystem.insert_following(username, hashtag)
            sleep_random(time)
            my_bot.follow_click()
            print("User not in ... test".format())

        if not filesystem.detect_likedpost(postid):
            # Post NOT in
            filesystem.insert_likedpost(postid, username, hashtag)
            sleep_random(time)
            if random.random() < .4:  # On average we will give 4 likes to each user
                my_bot.like_click()

        sleep_random(time)
        my_bot.close_post()
        # filesystem.validate_user(username)


def find_button_byword(html_content, word):

    return True


def find_pattern(file_name, pattern, button_elements):
    """
    This function looks for a pattern un a text file and then compare the values
    of each match with the elements in the list button_elements.
    The function returns a string with that match the pattern and also mathced
    values

    file_name: txt file name that we will look for patterns
    pattern: python re regular expression
    button_elements_ list of strings that we want to look in each match

    """
    text = open(file_name, "r").read()

    cont_elements = 0
    matches_in_text = re.findall(pattern, text)

    for i, match in enumerate(matches_in_text):
        cont_elements = 0

        print("MATCH with pattern: {} - {} ".format(i, match))
        for element in button_elements:
            if element in match:
                cont_elements += 1

        if cont_elements == len(button_elements):
            print("MATCH with button_elements: {} ".format(match))
            return match
    return False


class FileSystem:
    """
    The file system is compoused by multiple csv files that allow us to
    work with instagram users.
    """

    def __init__(self, project_folder):
        self.project_folder = project_folder
        self.dirpath = os.getcwd()
        self.followers_path = self.dirpath + "/" + \
            self.project_folder + "/followers.csv"
        self.following_path = self.dirpath + "/" + \
            self.project_folder + "/following.csv"
        self.posts_path = self.dirpath + "/" + self.project_folder + "/posts.csv"
        self.df_following = pd.read_csv(self.followers_path)
        self.df_following = pd.read_csv(self.following_path)
        self.df_posts = pd.read_csv(self.posts_path)

    def insert_followdata(self, following, followers, not_following_back):
        for user in following:
            if user not in self.df_following.username.unique():
                self.insert_following(self, user, "#previousdata")
        for user in followers:
            if user not in self.df_followers.username.unique():
                self.insert_followers(self, user, "#previousdata")

    def detect_follower(self, username):
        return username in self.df_following.username.unique()

    def detect_likedpost(self, postid):
        return postid in self.df_posts.postid.unique()

    def prepare_stage2(self):
        """
        Returns a list of all the followed people who are still in stage 1
        i.e We only followed them but now we want to engage giving likes
        """
        return self.df_following[self.df_following.stage == 1]["username"].unique()

    def insert_likedpost(self, postid, username, hashtag):
        next_obs = self.df_posts.index.max() + 1
        self.df_posts.loc[next_obs, "postid"] = postid
        self.df_posts.loc[next_obs, "username"] = username
        self.df_posts.loc[next_obs, "hashtag"] = hashtag
        self.df_posts.loc[next_obs, "date"] = date.today()
        self.df_posts.to_csv(self.posts_path, index=False)
        print("\tInstagram post insertes in filesystem")

    def insert_following(self, username, hashtag):
        next_obs = self.df_following.index.max() + 1
        self.df_following.loc[next_obs, "username"] = username
        self.df_following.loc[next_obs, "stage"] = 1
        self.df_following.loc[next_obs, "hashtag"] = hashtag
        self.df_following.loc[next_obs, "date"] = date.today()
        self.df_following.to_csv(self.followers_path, index=False)
        print("\tInstagram following inserted in filesystem")

    def insert_followers(self, username, hashtag):
        next_obs = self.df_following.index.max() + 1
        self.df_following.loc[next_obs, "username"] = username
        self.df_following.loc[next_obs, "stage"] = 1
        self.df_following.loc[next_obs, "hashtag"] = hashtag
        self.df_following.loc[next_obs, "date"] = date.today()
        self.df_following.to_csv(self.followers_path, index=False)
        print("\tInstagram follower inserted in filesystem")

    def advance_stage(username):
        current_stage = df_following[df_following.username ==
                                     username, "stage"]
        df_following[df_following.username ==
                     username, "stage"] = current_stage + 1
        self.df_following.to_csv(self.followers_path, index=False)
        print("Stage updated: {}".format(username))
        if current_stage == 1:
            df_following[df_following.username ==
                         username, "secondstage_date"] = date.today()


class InstaBot:
    def __init__(self, username, pw):
        self.driver = webdriver.Chrome(
            "/home/alejandrocoronado/Dropbox/Github/ig-followers/Drivers/chromedriver_78")

        self.username = username
        self.driver.get("https://instagram.com")
        sleep_random(2)

        sleep_random(2)
        self.driver.find_element_by_xpath(
            "//input[@name=\"username\"]").send_keys(username)

        self.driver.find_element_by_xpath(
            "//input[@name=\"password\"]").send_keys(pw)

        # En caso de que cambien los valores del Log In será necesario tomar otra salida
        # instagram_firstpage_content = self.driver.page_source
        # file_name = "sample.txt"
        # text_file = open(file_name, "w")
        # text_file.write(instagram_firstpage_content)
        # text_file.close()

        # bsObj = BeautifulSoup(instagram_firstpage_content)
        # buttons = bsObj.find_all('button')
        # for button in buttons:
        #    print(button.text)
        #    if button.text == "Log In":
        #        button_elements = button.get("class")
        # button_elements = '"' + button_elements + '"'
        # pattern = re.compile('class="[^"]*"')

        # for element in button_elements:
        #    pattern += '.*' + element

        # button_name = find_pattern(file_name, pattern, button_elements)

        self.driver.find_element_by_xpath('//button[.="Log In"]')\
            .click()
        sleep_random(4)

        self.driver.find_element_by_xpath('//button[.="Not Now"]')\
            .click()

        # self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]")\
        #    .click()
        # sleep_random(2)

        # XPATHS:
        self.timewait = 4
        self._dislike_xpath = "/html/body/div[4]/div[2]/div/article/div[2]/section[1]/span[1]/button"
        self._like = "/html/body/div[4]/div[2]/div/article/div[2]/section[1]/span[1]/button"
        self._follow_xpath = '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button'
        self._unfollow_xpath = '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button'
        self._user_xpath = "/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/a"
        self._scrollbox_xpath = "/html/body/div[4]/div/div[2]"
        self._closefollowersscrollbox_xpath = "/html/body/div[4]/div/div[1]/div/div[2]/button"
        self._closepost_xpath = "/html/body/div[4]/div[3]/button"
        self._cancel_unfollow = "/html/body/div[5]/div/div/div[3]/button[2]"

        self._user_postsnumber = '//*[@id="react-root"]/section/main/div/header/section/ul/li[1]/span/span'
        self._user_followers = '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span'
        self._user_following = '//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a/span'
        self._user_website = '//*[@id="react-root"]/section/main/div/header/section/div[2]/a'
        self._user_profilename = '//*[@id="react-root"]/section/main/div/header/section/div[2]/h1'
        self._user_bio = '//*[@id="react-root"]/section/main/div/header/section/div[2]/span'

    def get_userinfo():
        """
        This fuction can only be executed after being redirected to the userf prfile site
        (you can user go_user_url function).
        The function read all the basic informmation of the user and then saves that
        information in a dictionary
        """
        userdata = dict()
        userdata["postnumber"] = self.driver.find_element_by_xpath(
            self._user_postsnumber).text
        userdata["followers"] = self.driver.find_element_by_xpath(
            self._user_followers).text
        userdata["following"] = self.driver.find_element_by_xpath(
            self._user_following).text
        userdata["website"] = self.driver.find_element_by_xpath(
            self._user_website).get_attribute("href")
        userdata["profilename"] = self.driver.find_element_by_xpath(
            self._user_profilename).text
        userdata["bio"] = self.driver.find_element_by_xpath(
            self._user_bio).text

        return userdata

    def close_post(self):
        self.driver.find_element_by_xpath(self._closepost_xpath)\
            .click()

    def cancel_unfollow(self):
        self.driver.find_elements_by_tag_name(self._cancel_unfollow).click()

    def get_postid(self):
        url = self.driver.current_url
        postid = url.replace('https://www.instagram.com/p/', "")
        postid = postid[:-1]
        return postid

    def get_followersfollwing_data(self):
        self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(self.username))\
            .click()
        sleep_random(self.timewait)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        sleep_random(self.timewait)
        following = self._scroll_down()
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]")\
            .click()
        sleep_random(self.timewait)
        followers = self._scroll_down()

        not_following_back = [
            user for user in following if user not in followers]
        self.following = following
        self.followers = followers
        self.not_following_back = not_following_back

        print(not_following_back)

        return following, followers, not_following_back

    def likeorfollow_click(self, xpath, neg_xpath, type):
        """ Most elements in instagram can be click but after they are clicked
        the element xpath will change. This function handles that error
        """
        try:
            my_bot.driver.find_element_by_xpath(xpath).click()
        except Exception as e:
            print("Testing already " + type + " error handle.")
            my_bot.driver.find_element_by_xpath(neg_xpath).click()
            sleep_random(2)
            my_bot.driver.find_element_by_xpath(xpath).click()

    def like_click(self):
        self.likeorfollow_click(
            xpath=self._like, neg_xpath=self._dislike_xpath, type="Like")

    def follow_click(self):
        self.likeorfollow_click(
            xpath=self._follow_xpath, neg_xpath=self._unfollow_xpath, type="Follow")

    def get_username(self):
        return my_bot.driver.find_element_by_xpath(self._user_xpath).text

    def go_hashtag_url(self, hashtag):
        """ Opens the instagram url with posts related to a particular hashtag
        """
        hashtag_url = "https://www.instagram.com/explore/tags/" + hashtag + "/"
        self.driver.get(hashtag_url)

    def go_user_url(self, username):
        """ Opens the instagram url with posts related to a particular hashtag
        """
        user_html_url = "https://www.instagram.com/" + username
        self.driver.get(user_html_url)

    def _scroll_down(self):
        sleep_random(2)
        sugs = self.driver.find_element_by_xpath(
            '//a[contains(text(), Suggestions)]')
        # sugs = self.driver.find_element_by_xpath(
        #    '//a[contains(text(), Suggestions)]')
        sugs = self.driver.find_element_by_xpath(
            '//a[.="See All Suggestions"]')

        self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        sleep_random(2)
        scroll_box = self.driver.find_element_by_xpath(self._scrollbox_xpath)
        last_ht, ht = 0, 1
        while last_ht != ht:
            last_ht = ht
            sleep_random(self.timewait)
            ht = self.driver.execute_script("""
                    arguments[0].scrollTo(0, arguments[0].scrollHeight);
                    return arguments[0].scrollHeight;
                    """, scroll_box)
        links = scroll_box.find_elements_by_tag_name('a')
        names = [name.text for name in links if name.text != '']
        self.driver.find_element_by_xpath(self._closefollowersscrollbox_xpath)\
            .click()
        return names


#----------------------BOT--------------------------
yourusername = "hoyxtimx"
my_bot = InstaBot(yourusername, password)
project_folder = "ProjectFolder"
filesystem = FileSystem(project_folder='ProjectFolder')
# Let us include all the people you been following
following, followers, not_following_back = my_bot.get_followersfollwing_data()
filesystem.insert_followdata(following, followers, not_following_back)

hashtag = "arbol"
my_bot.go_hashtag_url(hashtag)


allposts = '//*[@id="react-root"]/section/main/article/div[1]/div/div'
# We identify posts using this attrtibute (beacuse it works)
attribute = "style"
# iterate_elements_onxpath(allposts, attribute,
#                         "div", filesystem, hashtag, time=2)


stage2_users = filesystem.prepare_stage2()
for username in stage2_users:
    my_bot.go_user_url(username)
    allposts_user = '//*[@id="react-root"]/section/main/div/div[3]/article/div[1]/div'
    iterate_elements_onxpath(allposts_user, attribute,
                             "div", filesystem, hashtag, time=5)
    filesystem.advance_stage(username)
    raise ValueError()
