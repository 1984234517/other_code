import requests
import hashlib
import time
import logging

sess = requests.session()

# 每次发送请求的时间(这个请求是用来涮新视频的播放时间，单位为秒)，不可过短
send_time = 60
# md5加密
def hex_md5(key):
    h1 = hashlib.md5()
    h1.update(key.encode(encoding='utf-8'))
    return h1.hexdigest()

# type=1表示，需要设置cookie，
# type=2表示，get请求
# type=3表示，post请求
# type=4表示，需要为cookie设置额外的值
def get_url(url, type=2, data={}):
    headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://study.enaea.edu.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
    }
    if type == 3:
        res = sess.post(url, headers=headers, data=data)
    else:
        res = sess.get(url, headers=headers)
    if res.status_code == 200:
        # print(res.status_code)
        if type == 1:
            sess.cookies = res.cookies
        elif type == 4:
            add_cookies = res.headers.get('Set-Cookie')
            add_cookies = str(add_cookies).split('=')
            temp = add_cookies[1].split(';')
            add_cookies[1] = temp[0]
            add_cookies.insert(2, temp[1])
            sess.cookies[add_cookies[0]] = add_cookies[1]
        return res
    else:
        print(res.text)
        exit(-1)

# login
def login(username, password):
    t = int(time.time() * 1000)
    url = 'https://passport.enaea.edu.cn/login.do?ajax=true&j_username={}&j_password={}&_acegi_security_remember_me=false&_={}'.format(username, hex_md5(password), t)
    res = get_url(url, type=1).json()
    if(res.get('success')==None or not res['success']):
        logging.info("登陆失败，请检查你的用户或者密码")
        exit(-1)
    logging.info("登陆成功")

# 首先获取需要涮的课程
def get_all():
    t = int(time.time()*1000)
    url = 'https://study.enaea.edu.cn/circleIndex.do?action=getMyClass&start=0&limit=25&isCompleted=&circleId=150345&syllabusId=912062&categoryRemark=all&_={}&_={}'.format(t, t)
    res = get_url(url).json()
    print(res)
    # 未成功涮完的课程id
    all_course_id = []
    # 未成功涮完的课程名称
    all_course_name = []
    for item in res['result']['list']:
        if item['studyCenterDTO']['studyProgress'] != '100':
            all_course_id.append(item['studyCenterDTO']['courseId'])
            all_course_name.append(item['studyCenterDTO']['courseTitle'])
    return all_course_id, all_course_name

# 挨个涮没有刷的视频
def start_work(course_ids, course_names):
    for id, couser_name in zip(course_ids, course_names):
        logging.info("正在开涮课程：{}".format(couser_name))
        t = int(time.time()*1000)
        url = 'https://study.enaea.edu.cn/course.do?action=getCourseContentList&courseId={}&circleId=150345&_={}'.format(id, t)
        res = get_url(url).json()
        for j in range(len(res['result']['list'])):
            # print('sdfsd', res['result']['list'][j])
            if res['result']['list'][j]['studyProgress'] != '100':
                url = 'https://study.enaea.edu.cn/course.do?action=statisticForCCVideo&courseId={}&coursecontentId={}&circleId=150345&_={}'.format(id, res['result']['list'][j]['id'], t)
                resp = get_url(url, type=4).json()
                if resp['success']:
                    logging.info("{}视频读取成功，等待开涮".format(res['result']['list'][j]['filename']))
                    while process_video(res['result']['list'][j]['id']):
                        pass
                    logging.info("{}视频成功涮完".format(res['result']['list'][j]['filename']))
                else:
                    logging.info("视频读取失败，请重新尝试")
                    exit(-1)

# 按照传入的id进行视频的学习
def process_video(id):
    t = int(time.time()*1000)
    data = {
        'id': id,
        'circleId': '150345',
        'finish': 'false',
        'ct': t,
    }
    url = 'https://study.enaea.edu.cn/studyLog.do'
    # 延时发送
    time.sleep(send_time)
    res = get_url(url, type=3, data=data).json()
    # print(res)
    logging.info(res)
    if (not res.get('progress')) or res['progress'] != 100:
        if res.get('progress'):
            logging.info("涮取进度为：{}%".format(res['progress']))
        else:
            logging.info("涮取进度为：0%")
        return 1
    else:
        return 0
if __name__ == '__main__':
    # 控制台输出相关信息
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    login('账号', '密码')
    couser_ids, course_names = get_all()
    start_work(couser_ids, course_names)