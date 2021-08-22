import http.cookiejar as cookielib
import http.cookiejar as cookielib
from bs4 import BeautifulSoup as bs
from requests import session


def createCookieFile(email, pw):

    headers = {
        "Referer": f"https://m.vk.com/login?role=fast&to=&s=1&m=1&email={email}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
    }

    payload = {    
        'email': email,
        'pass': pw
    }

    with session() as s:
        page = s.get( 'https://m.vk.com/login' )
        soup = bs( page.content, 'lxml' )
        
        # Get login url with query params created by vk
        url = soup.find('form')['action']      
        
        # perform login action
        s.post( url, data=payload, headers=headers )

        # extract cookie 
        cookie_dic = s.cookies.get_dict()

        # build cookie string
        cookie = ''
        for key, value in cookie_dic.items():
            cookie += f'{key}={value};'
            
        with open("cookie.txt", "w") as file:             
            # write to file
            file.write( cookie )