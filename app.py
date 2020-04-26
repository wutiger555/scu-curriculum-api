from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from bs4 import BeautifulSoup
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth
import pandas as pd
import requests


app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()


@auth.verify_password
def verify(id, passwd):
    r = requests.post('https://web.sys.scu.edu.tw/login0.asp', data={'id':id,'passwd':passwd})
    if 'Login=ok' in r.headers['Set-Cookie']:
        return True
    else:
        return False

class getUserInfo(Resource):
    def get(self, id, passwd):
        r = requests.post('https://web.sys.scu.edu.tw/login0.asp', data={'id':id,'passwd':passwd})
        if 'Login=ok' in r.headers['Set-Cookie']:
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, 'html.parser')
            body = soup.body

            ary = []
            for i in body.stripped_strings:
                ary = i.replace('：','').replace('\xa0\xa0','\xa0').replace('\xa0',' ').split(' ')
                break
            return ary, 200
        else:
            return 'id not found.', 404

class getTable(Resource):
    @auth.login_required
    def post(self, id, passwd):
        r = requests.post('https://web.sys.scu.edu.tw/login0.asp', data={'id':id,'passwd':passwd})
        if 'Login=ok' in r.headers['Set-Cookie']:
            r.cookies.set('parselimit', 'Infinity')
            n = requests.get('https://web.sys.scu.edu.tw/SelectCar/selcar81.asp', cookies = r.cookies, data={'procsyear':'108', 'procterm':'2'})
            n.encoding = 'big5'
            soup = BeautifulSoup(n.text,"html.parser") #將網頁資料以html.parser
            trs = soup.find_all('tr')

            df = pd.DataFrame(index=['1', '2', '3', '4', 'E', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D'], #處理Rows
                  columns=['禮拜一', '禮拜二', '禮拜三', '禮拜四', '禮拜五', '禮拜六', '禮拜日']) #處理columns
            count = 0

            for tr in trs:
                tds = tr.find_all('td')
                col_count = 0
                if count > 5:
                    trName = str(count - 1)
                else:
                    trName = str(count)
                if count == 5: #非輸字節數處理
                    trName = "E"
                elif count == 11:
                    trName = 'A'
                elif count == 12:
                    trName = 'B'
                elif count == 13:
                    trName = 'C'
                elif count == 14:
                    trName = 'D'

                for td in tds:
                    tdTxt = str(td.text)
                    tdTxt = tdTxt[1:].replace(" 　"," ").replace("\n","(")
                    if col_count == 1:
                        df.at[trName, '禮拜一'] = tdTxt
                    elif col_count == 2:
                        df.at[trName, '禮拜二'] = tdTxt
                    elif col_count == 3:
                        df.at[trName, '禮拜三'] = tdTxt
                    elif col_count == 4:
                        df.at[trName, '禮拜四'] = tdTxt
                    elif col_count == 5:
                        df.at[trName, '禮拜五'] = tdTxt
                    elif col_count == 6:
                        df.at[trName, '禮拜六'] = tdTxt
                    elif col_count == 7:
                        df.at[trName, '禮拜日'] = tdTxt
                    col_count = col_count + 1
                count = count + 1
                
            return df.to_json(force_ascii=False), 200
        else:
            return '', 404





api.add_resource(getUserInfo, '/api/getUserInfo/<string:id>/<string:passwd>')
api.add_resource(getTable, '/api/getTable/<string:id>/<string:passwd>')

if __name__ == '__main__':
    app.run(debug=True)