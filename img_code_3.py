# -*- coding: utf-8 -*-
import time
import random
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from io import BytesIO


class Bilibili(object):
    """docstring for Bilibili"""
    js = """var keys=document.cookie.match(/[^ =;]+(?=\=)/g);
        if (keys) {
        for (var i = keys.length; i--;)
        document.cookie=keys[i]+'=0;expires=' + new Date( 0).toUTCString()
        } """

    def __init__(self):
        """构造函数"""
        super(Bilibili, self).__init__()
        self.browser = webdriver.Chrome()
        self.browser.set_page_load_timeout(20)
        self.browser.implicitly_wait(10)

    def __del__(self):
        """析构函数"""
        if self.browser is not None:
            self.browser.quit()

    def logging(self, username, password):

        self.browser.get("https://passport.bilibili.com/login")
        dom_input_id = self.browser.find_element_by_id("login-username")
        dom_input_keyword = self.browser.find_element_by_id("login-passwd")
        dom_btn_log = self.browser.find_element_by_xpath('//*[@class="btn-box"]/a[1]')
        # pdb.set_trace()
        dom_input_id.send_keys(username)
        dom_input_keyword.send_keys(password)

        flag_success = False
        while not flag_success:
            image_full_bg = self.get_image("gt_cut_fullbg_slice")
            # 下载完整的验证图
            image_bg = self.get_image("gt_cut_bg_slice")
            # 下载有缺口的验证图
            diff_x = self.get_diff_x(image_full_bg, image_bg)
            # pdb.set_trace()
            track = self.get_track(diff_x)
            result = self.simulate_drag(track)
            print(result)

            if u'验证通过' in result:
                flag_success = True
            elif u'出现错误:' in result:
                self.browser.execute_script('location.reload()')
            elif u'再' in result:
                time.sleep(4)
                continue
            elif u'吃' in result:
                time.sleep(5)
            else:
                break

        if flag_success:
            time.sleep(random.uniform(1.5, 2))
            self.browser.execute_script(self.js)

    def get_image(self, class_name):
        """
        下载并还原极验的验证图
        Args:
            class_name: 验证图所在的html标签的class name
        Returns:
            返回验证图
        Errors:
            IndexError: list index out of range. ajax超时未加载完成，导致image_slices为空
        """
        image_slices = self.browser.find_elements_by_class_name(class_name)
        # pdb.set_trace()
        if len(image_slices) == 0:
            print('No such a class')
        div_style = image_slices[0].get_attribute('style')
        # pdb.set_trace()
        image_url = re.findall("background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;", div_style)[0][0]
        image_url = image_url.replace("webp", "jpg")
        # image_filename = urlparse.urlsplit(image_url).path.split('/')[-1]
        location_list = list()
        for image_slice in image_slices:
            location = dict()
            location['x'] = int((re.findall("background-position: (.*)px (.*)px;", image_slice.get_attribute('style'))[0])[0])
            location['y'] = int((re.findall("background-position: (.*)px (.*)px;", image_slice.get_attribute('style'))[0])[1])
            location_list.append(location)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
        response = requests.get(image_url, headers=headers)
        
        image = Image.open(BytesIO(response.content))
        image = self.recover_image(image, location_list)
        return image

    def recover_image(self, image, location_list):
        """
        还原验证图像
        Args:
            image: 打乱的验证图像（PIL.Image数据类型）
            location_list: 验证图像每个碎片的位置
        Returns:
           还原过后的图像
        """
        new_im = Image.new('RGB', (260, 116))
        im_list_upper = []
        im_list_down = []
        for location in location_list:
            if location['y'] == -58:
                im_list_upper.append(image.crop((abs(location['x']), 58, abs(location['x']) + 10, 116)))
            if location['y'] == 0:
                im_list_down.append(image.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        x_offset = 0
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]

        return new_im

    def get_diff_x(self, image1, image2):
        """
            计算验证图的缺口位置（x轴）
            两张原始图的大小都是相同的260*116，那就通过两个for循环依次对比每个像素点的RGB值，
            如果RGB三元素中有一个相差超过50则就认为找到了缺口的位置
            Args:
                image1: 图像1
                image2: 图像2
            Returns:
                x_offset
        """
        for x in range(0, 260):
            for y in range(0, 116):
                if not self.__is_similar(image1, image2, x, y):
                    return x

    def __is_similar(self, image1, image2, x_offset, y_offset):
        """
        判断image1, image2的[x, y]这一像素是否相似，如果该像素的RGB值相差都在50以内，则认为相似。
        Args:
            image1: 图像1
            image2: 图像2
            x_offset: x坐标
            y_offset: y坐标
        Returns:
           boolean
        """
        pixel1 = image1.getpixel((x_offset, y_offset))
        pixel2 = image2.getpixel((x_offset, y_offset))
        for i in range(0, 3):
            if abs(pixel1[i] - pixel2[i]) >= 50:
                return False
        return True

    def get_track(self, x_offset):

        track = list()
        length = x_offset - 6
        x = random.randint(1, 5)
        while length - x > 4:
            track.append([x, 0, 0])
            length = length - x
            x = random.randint(1, 15)

        for i in range(length):
            if x_offset > 47:
                track.append([1, 0, random.randint(10, 12) / 100.0])
            else:
                track.append([1, 0, random.randint(13, 14) / 100.0])
        return track

    def simulate_drag(self, track):

        dom_div_slider = self.browser.find_element_by_xpath('//*[@id="gc-box"]/div/div[3]/div[2]')

        ActionChains(self.browser).click_and_hold(on_element=dom_div_slider).perform()

        for x, y, z in track:
            ActionChains(self.browser).move_to_element_with_offset(
                to_element=dom_div_slider,
                xoffset=x + 22,
                yoffset=y + 22).perform()
            time.sleep(z)

        time.sleep(0.9)
        ActionChains(self.browser).release(on_element=dom_div_slider).perform()
        time.sleep(1)
        dom_div_gt_info = self.browser.find_element_by_class_name('gt_info_type')
        return dom_div_gt_info.text


if __name__ == '__main__':
    bilibili = Bilibili()
    bilibili.logging('username', 'password')
