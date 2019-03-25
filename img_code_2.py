import random
from io import BytesIO
import time
from urllib.request import urlretrieve
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
import PIL.Image as image
from bs4 import BeautifulSoup
import re


class Crack:

    def __init__(self, username, password):
        self.url = 'https://passport.bilibili.com/login'
        self.browser = webdriver.Chrome('chromedriver')
        self.wait = WebDriverWait(self.browser, 100)
        self.username = username
        self.password = password
        self.BORDER = 6

    def open(self):
        """
        打开浏览器，并输入查询内容
        """
        self.browser.get(self.url)
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
        username.send_keys(self.username)
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'login-passwd')))
        password.send_keys(self.password)

    def __del__(self):
        time.sleep(10)
        self.browser.close()

    def get_screenshot(self):
        """
        获取网页截图
        :return:
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))

        return screenshot

    def get_images(self, bg_filename='bg.jpg', fullbg_filename='fullbg.jpg'):
        """
        获取验证码图片
        :param bg_filename:
        :param fullbg_filename:
        :return:
        """
        bg = []
        fullbg = []
        while bg ==[] and fullbg == []:
            bf = BeautifulSoup(self.browser.page_source, 'lxml')
            bg = bf.find_all('div', class_='gt_cut_bg_slice')
            fullbg = bf.find_all('div', class_='gt_cut_fullbg_slice')

        bg_url = re.findall(r"url\(\"(.*)\"\);", bg[0].get('style'))[0].replace('webp', 'jpg')
        fullbg_url = re.findall(r"url\(\"(.*)\"\);", fullbg[0].get('style'))[0].replace('webp', 'jpg')
        bg_location_list = []
        fullbg_location_list = []

        for each_bg in bg:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][1])
            bg_location_list.append(location)
        for each_fullbg in fullbg:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullbg.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullbg.get('style'))[0][1])
            fullbg_location_list.append(location)
        urlretrieve(url=bg_url, filename=bg_filename)
        print('缺口图片下载完成')
        urlretrieve(url=fullbg_url, filename=fullbg_filename)
        print('背景图片下载完成')

        return bg_location_list, fullbg_location_list

    def get_merge_image(self, filename, location_list):
        """
        合并图像，并还原图像
        :return:
        """
        im = image.open(filename)
        new_im = image.new('RGB', (260, 116))  # width 260px, height 116px

        im_list_upper = []
        im_list_down = []
        for location in location_list:
            if location['y'] == -58:
                im_list_upper.append(im.crop((abs(location['x']), 58, abs(location['x'])+10, 166)))
            if location['y'] == 0:
                im_list_down.append(im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        x_offset = 0
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]
        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]
        new_im.save(filename)
        time.sleep(1)
        return new_im

    def get_slider(self):
        """
        获取滑块
        :return:
        """
        while True:
            try:
                slider = self.browser.find_element_by_xpath("//div[@class='gt_slider_knob gt_show']")
                break
            except:
                time.sleep(0.5)
        return slider

    def get_pag(self, img1, img2):
        """
        获取偏移量
        :param img1:不带缺口
        :param img2:带缺口
        :return:
        """
        left = 43
        for i in range(left, img1.size[0]):
            for j in range(img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        :param img1:
        :param img2:
        :param x: 位置x
        :param y: 位置y
        :return:
        """
        # 取两张图片的像素点
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        threshold = 60
        if (abs(pix1[0] - pix2[0] < threshold) and abs(pix1[1] - pix2[1] < threshold) and abs(
            pix1[2] - pix2[2] < threshold)):
            return True
        else:
            return False

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance:
        :return:
        """
        distance += 24
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阀值
        mid = distance * 3 / 5
        # 计算阀值
        t = 0.2
        # 计算初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度
                a = 2
            else:
                # 加速度为-3
                a = -3
            # 初速度为
            v0 = v
            # 移动距离x = v0t+1/2*a^2
            move = v0*t + 1/2*a*t*t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
            # 速度已到达v，该速度作为下次的初速度
            v = v0 + a*t
        # track = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        while track:
            x = random.choice(track)
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
            track.remove(x)
        tracks = [-3, -3, -3, -2, -2, -2, -2, -2, -1, -1, -1, -1]
        time.sleep(0.5)

        for track in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=track, yoffset=0).perform()
        # 小范围震荡一下，进一步迷惑极验后台，这一步可以极大地提高成功率
        ActionChains(self.browser).move_by_offset(xoffset=-1, yoffset=0).perform()
        ActionChains(self.browser).move_by_offset(xoffset=1, yoffset=0).perform()

        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def crack(self):
        self.open()
        bg_list, fbg_list = self.get_images()
        bg_img = self.get_merge_image('bg.jpg', bg_list)
        fullbg_img = self.get_merge_image('fullbg.jpg', fbg_list)

        # 缺口位置
        gap = self.get_pag(fullbg_img, bg_img)

        track = self.get_track(gap - self.BORDER)
        print('滑动滑块')
        print(track)

        # 点按呼出缺口
        slider = self.get_slider()
        # 拖动滑块到缺口处
        self.move_to_gap(slider, track)

    def run(self, crack):
        print('开始验证...')
        self.browser.implicitly_wait(3)
        crack.crack()
        while True:
            try:
                self.browser.find_element_by_class_name('gt_success')
                ActionChains(self.browser).release().perform()
                break
            except Exception as f:
                ActionChains(self.browser).release().perform()
                # refresh_button = driver.find_element_by_class_name("gt_refresh_tips")
                # refresh_button.click()
                time.sleep(5)
                crack.crack()
        signin = self.browser.find_element_by_class_name('btn-login')
        signin.click()


crack = Crack('*', '*')
crack.run(crack)