from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from PIL import Image
from io import BytesIO
import random
from selenium.common.exceptions import TimeoutException


class Bilibili(object):
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.url = "https://passport.bilibili.com/login"
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

    def send_userInfo(self):
        """
        输入账号密码
        :return:
        """
        self.driver.get(url=self.url)
        # self.driver.maximize_window()
        username = self.wait.until(EC.presence_of_element_located((By.ID, "login-username")))
        password = self.wait.until(EC.presence_of_element_located((By.ID, "login-passwd")))
        time.sleep(1)
        username.send_keys(self.account)
        time.sleep(1)
        password.send_keys(self.password)

    def login(self):
        submit = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn btn-login")))
        submit.click()

    def get_button(self):
        """
        获取滑动按钮
        :return: 返回滑动按钮
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "gt_slider_knob")))
        return button

    def get_webscreen(self, btn):
        """
        获取网页两次截图
        1、鼠标移动到滑动按钮时的截图
        2、鼠标点击滑动按钮时的截图
        :return: 返回 web的两次截图
        """
        ActionChains(self.driver).move_to_element(btn).perform()
        screen1 = self.driver.get_screenshot_as_png()
        screen1 = Image.open(BytesIO(screen1))
        ActionChains(self.driver).click_and_hold(btn).perform()
        screen2 = self.driver.get_screenshot_as_png()
        screen2 = Image.open(BytesIO(screen2))
        return screen1, screen2

    def get_imagelocation(self, btn):
        """
        获取验证图片位置
        :param btn:滑动按钮
        :return:
        """
        ActionChains(self.driver).move_to_element(btn).perform()
        image = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gt_box")))
        time.sleep(3)
        location = image.location
        size = image.size
        print(location, size)
        top, bottom, left, right = location['y'], location['y']+size['height'],\
                                   location['x'], location['x']+size['width']
        return top, bottom, left, right

    def get_image(self, btn):
        """
        获取两张验证图片
        1、 获取坐标
        2、获取网页截图
        3、截取获得验证码图片
        :return:
        """
        top, bottom, left, right = self.get_imagelocation(btn)
        print(top, bottom, left, right)
        screen_images = self.get_webscreen(btn)
        screen_images[0].save('11.png')
        screen_images[1].save('22.png')
        # left, upper, right, and lower (Mac电脑 需要都乘上2)
        crop1 = screen_images[0].crop((left*2, top*2, right*2, bottom*2))
        crop1.save("1.png")
        crop2 = screen_images[1].crop((left*2, top*2, right*2, bottom*2))
        crop2.save("2.png")
        return crop1, crop2

    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        :param img1:完整验证码图片
        :param img2:缺口验证码图片
        :param x:x坐标点
        :param y:用坐标点
        :return:
        """
        # 返回坐标的像素值
        print("x:%d--y:%d" % (x, y))
        pixel1 = img1.load()[x, y]
        pixel2 = img2.load()[x, y]
        print('pixel1:', pixel1)
        print('pixel2:', pixel2)
        print("*" * 20)
        threshold = 100
        if (abs(pixel1[0] - pixel2[0]) < threshold) and (abs(pixel1[1] - pixel2[1]) < threshold) and (abs(pixel1[2] - pixel2[2]) < threshold):
            print('True')
            return True
        else:
            print('False')
            return False

    def get_gap(self, img1, img2):
        """
        获取缺口的x轴
        :param img1: 完整验证码图片
        :param img2: 缺口验证码图片
        :return:
        """
        # 忽略第一个块（移动的块）
        left = 125
        print('size:', img1.size, img2.size)
        for i in range(left, img1.size[0]):
            for j in range(0, img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    print('i', i)
                    left = i
                    return left
        return left

    def get_track(self, left):
        """
        获取滑动轨迹
        :return:
        """
        track = []
        current = 0
        left = int(left/2)
        print(left)
        mid = left * 2 / 3
        print(mid)
        # 时间
        t = 0.2
        # 末速度
        v = 0
        while current < left:
            if current < mid:
                # 加速度
                a = random.randint(1, 3)
            else:
                a = -random.randint(3, 5)
            # 初速度
            v0 = v
            # 求末速度 (末速度=初速度+加速度*时间)
            v = v0+a*t
            # 求位移(位移=初速度*时间+0.5*加速度*时间的平方)
            move = v0*t+0.5*a*t*t
            current += move
            track.append(round(move))
        offset = sum(track) - left
        print(offset)
        if offset > 0:
            track.extend([-1 for i in range(int(offset))])
        else:
            track.extend([1 for i in range(int(abs(offset)))])
        print(track)
        print(sum(track))
        return track

    def move_button(self, btn, track):
        """
        移动到指定位置
        :return:
        """
        ActionChains(self.driver).click_and_hold(btn).perform()
        time.sleep(0.8)
        for i in track:
            ActionChains(self.driver).move_by_offset(xoffset=i, yoffset=0).perform()
            time.sleep(0.0006)
        time.sleep(0.5)
        ActionChains(self.driver).release().perform()

    def run(self):
        """
        执行流程
        1、输入账号密码
        2、获取滑动按钮
        3、获取两张验证图片
        4、获取滑动轨迹
        5、滑到指定位置
        :return:
        """
        self.send_userInfo()
        btn = self.get_button()
        images = self.get_image(btn)
        left = self.get_gap(images[0], images[1])
        print("left:", left)
        times = 0
        while times < 3:
            track = self.get_track(left-18)
            self.move_button(btn, track)
            try:
                self.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "gt_info_type"), "验证通过:"))
            except TimeoutException:
                print("失败")
                times += 1
            else:
                print("成功")
                self.login()
                time.sleep(10)
                break
        # <span class="gt_info_type">验证失败:</span>
        # <span class="gt_info_type">验证通过:</span>

    def __del__(self):
        self.driver.close()


if __name__ == '__main__':
    account_in = input("输入账号")
    password_in = input("输入密码")
    bili = Bilibili(account_in, password_in)
    bili.run()
