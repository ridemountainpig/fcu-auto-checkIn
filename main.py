import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import base64
import pytesseract
from PIL import Image
import time
from dotenv import load_dotenv

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://signin.fcu.edu.tw/clockin/login.aspx")


def captchaConversion():

    img = Image.open('./captcha_login.png').convert('L')
    table = []
    for i in range(256):
        if i < 127:
            table.append(0)
        else:
            table.append(1)
    img = img.point(table, '1')
    img.save('./out.png')
    # img.show()

    img = Image.open('./out.png')
    pixel_matrix = img.load()
    for column in range(1, 21):
        for row in range(1, 49):
            if pixel_matrix[row, column] == 0 and pixel_matrix[row, column - 1] == 255 and pixel_matrix[row, column + 1] == 255:
                pixel_matrix[row, column] = 255
            if pixel_matrix[row, column] == 0 and pixel_matrix[row - 1, column] == 255 and pixel_matrix[row + 1, column] == 255:
                pixel_matrix[row, column] = 255

    text = pytesseract.image_to_string(img)
    return "".join(list(filter(str.isdigit, text)))


def downloadImg():
    img_base64 = driver.execute_script(
        '''
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width; cnv.height = ele.height;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    ''', driver.find_element(By.XPATH, '//*[@id="form1"]/div[3]/img[2]'))

    with open("./captcha_login.png", 'wb') as image:
        image.write(base64.b64decode(img_base64))


def checkIn():
    LabelNote = driver.find_element(By.ID, 'LabelNote').text
    if LabelNote == '目前無課程資料或非上課時間':
        print(LabelNote)
        return
    downloadImg()
    verificationCode = captchaConversion()
    validateCode = driver.find_element(By.ID, 'validateCode')
    checkButton = driver.find_element(By.ID, 'Button0')
    checkButtonHtml = checkButton.get_attribute('outerHTML')
    if 'disabled="disabled"' in checkButtonHtml:
        print("本節課已打卡")
        return

    print("code = ", verificationCode)
    validateCode.clear()
    validateCode.send_keys(verificationCode)
    checkButton.click()

    LabelNote = driver.find_element(By.ID, 'LabelNote').text
    print(LabelNote)
    if LabelNote == '驗證碼錯誤，請重新輸入':
        driver.refresh()
        checkIn()


def login():
    username = driver.find_element(By.ID, 'LoginLdap_UserName')
    password = driver.find_element(By.ID, 'LoginLdap_Password')
    login = driver.find_element(By.ID, 'LoginLdap_LoginButton')

    load_dotenv()

    username.send_keys(os.environ["USERNAME"])
    password.send_keys(os.environ["PASSWORD"])

    login.click()
    try:
        checkInButton = driver.find_element(By.ID, 'ButtonClassClockin')
        checkInButton.click()
    except:
        print("login fail.")
        print("please check username and password in secrets is correct or not.")
        return False
    return True


if __name__ == '__main__':
    login_check = login()
    while True:
        if not login_check:
            break
        checkIn()
        time.sleep(10)
        driver.refresh()
        if driver.current_url != 'https://signin.fcu.edu.tw/clockin/ClassClockin.aspx':
            driver.get("https://signin.fcu.edu.tw/clockin/login.aspx")
            login_check = login()
