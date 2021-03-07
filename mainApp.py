'''Import dependencies''' 
import urllib
import json
import requests
# import dateutil.parser
from datetime import datetime
import websockets
import asyncio
# import pyodbc
import nest_asyncio



class OrderZone:
    def __init__(self):
        self.confFile = "trash/config.txt"
        self.faCredential = self.getConfFileV()
        self.getAccessTokenStart()

        upResponse = self.userPrincipals()
        # print(upResponse)

        self.connectWebSocket(upResponse)



        # self.getAccount()
        # self.placeOrder()
        # self.getOrders()
        # self.cancelOrder()

    def connectWebSocket(self, upResponse):
        # nest_asyncio.apply()
        loginJson, dataJson = self.requestDict(upResponse)
        loop = asyncio.get_event_loop()
        connection = loop.run_until_complete(self.connect(upResponse))
        tasks = [
            asyncio.ensure_future(self.receiveMessage(connection)),
            asyncio.ensure_future(self.sendMessage(loginJson)),
            asyncio.ensure_future(self.receiveMessage(connection)),
            asyncio.ensure_future(self.sendMessage(dataJson)),
            asyncio.ensure_future(self.receiveMessage(connection))
        ]

        loop.run_until_complete(asyncio.wait(tasks))





    async def connect(self, upResponse):
        uri = "wss://" + upResponse['streamerInfo']['streamerSocketUrl'] + "/ws"

        self.connection = await websockets.client.connect(uri)
        if self.connection.open:
            print("Connection established")
            return self.connection

    async def sendMessage(self, message):
        await self.connection.send(message)

    async def receiveMessage(self, connection):
        while True:
            try:
                message = await connection.recv()
                message_decoded = json.loads(message)
                print(message_decoded)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break

    async def heartbeat(self, connection):
        while True:
            try:
                await connection.send('ping')
                await asyncio.sleep(5)
            except websockets.exceptions.ConnectionClosed:
                print('connection with server closed')
                break
































    def requestDict(self, upResponse):
        '''Login and data dict to make requests to streamer api'''

        # grab the token timestamp and convert it to milliseconds
        tokenTs = upResponse['streamerInfo']['tokenTimestamp']
        tokenTsM = self.tokenTimestamp(tokenTs)

        creds = {
            'userid':upResponse['accounts'][0]['accountId'],
            'token':upResponse['streamerInfo']['token'],
            'company':upResponse['accounts'][0]['company'],
            'segment':upResponse['accounts'][0]['segment'],
            'cddomain':upResponse['accounts'][0]['accountCdDomainId'],
            'usergroup':upResponse['streamerInfo']['userGroup'],
            'accesslevel':upResponse['streamerInfo']['accessLevel'],
            'authorized':'Y',
            'timestamp':int(tokenTsM),
            'appid':upResponse['streamerInfo']['appId'],
            'acl':upResponse['streamerInfo']['acl']
        }


        loginCreds = {
            "requests":[
                {
                    "service":"ADMIN",
                    "command":"LOGIN",
                    "requestid":"0",
                    "account":upResponse['accounts'][0]['accountId'],
                    "source":upResponse['streamerInfo']['appId'],
                    "parameters":{
                        "credential":urllib.parse.urlencode(creds),
                        "token":upResponse['streamerInfo']['token'],
                        "version":"1.0"
                    }
                }
            ]
        }



        dataRequest = {
            "requests":[
                {
                    "service":"ACTIVES_NASDAQ",
                    "requestid":"1",
                    "command":"SUBS",
                    "account":upResponse['accounts'][0]['accountId'],
                    "source":upResponse['streamerInfo']['appId'],
                    "parameters":{
                        "keys":"NASDAQ-60",
                        "fields":"0,1"
                    }
                },
                                {
                    "service":"LEVELONE_FUTURES",
                    "requestid":"2",
                    "command":"SUBS",
                    "account":upResponse['accounts'][0]['accountId'],
                    "source":upResponse['streamerInfo']['appId'],
                    "parameters":{
                        "keys":"/ES",
                        "fields":"0,1,2,3,4"
                    }
                }
            ]
        }


        # turn the dict to JSON string:
        loginJson = json.dumps(loginCreds)
        dataJson = json.dumps(dataRequest)

        return loginJson, dataJson


    def tokenTimestamp(self, tokenTs):
        '''Convert token timestamp to epoch milliseconds'''
        closeTime = str(tokenTs).split('+', 1)[0]
        etUTC = datetime.strptime(closeTime, "%Y-%m-%dT%H:%M:%S")
        etEpoch = (etUTC - datetime(1970, 1, 1)).total_seconds()*1000
        return etEpoch


    def userPrincipals(self):
        '''Get user principals credentials'''
        endPoint = "https://api.tdameritrade.com/v1/userprincipals"
        header = {'Authorization':'Bearer {}'.format(self.accessToken), 'Connection':'close'}
        response = requests.get(endPoint, timeout = 100, headers = header, params = {"fields":'streamerSubscriptionKeys,streamerConnectionInfo'})
        upResponse = response.json()
        return upResponse















































    def cancelOrder(self):
        endpoint = 'https://api.tdameritrade.com/v1/accounts/{Account_Number}/orders/{Order_ID}'
        mainEndpoint = endpoint.format(Account_Number = self.faCredential['Account_Number'], Order_ID = 2208096601)
        print(mainEndpoint)
        header = {'Authorization':'Bearer {}'.format(self.accessToken), 'Connection':'close'}
        response = requests.delete(mainEndpoint, timeout = 100, headers = header)
        print(json.dumps(response.json(), sort_keys = True, indent = 4))




    def getOrders(self):
        endpoint = 'https://api.tdameritrade.com/v1/accounts/{account_number}/orders'
        mainEndpoint = endpoint.format(account_number = self.faCredential['Account_Number'])
        print(mainEndpoint)
        header = {'Authorization':'Bearer {}'.format(self.accessToken), 'Connection':'close'}
        param = {"maxResults":10, "fromEnteredTime":"2021-02-19", "toEnteredTime":"2021-02-19", "status":""}
        response = requests.get(mainEndpoint, timeout = 100, headers = header, params = param)
        print(json.dumps(response.json(), sort_keys = True, indent = 4))


    def getAccount(self):
        endpoint = 'https://api.tdameritrade.com/v1/accounts/{account_number}'
        mainEndpoint = endpoint.format(account_number = self.faCredential['Account_Number'])
        print(mainEndpoint)
        header = {'Authorization':'Bearer {}'.format(self.accessToken), 'Connection':'close'}
        response = requests.get(mainEndpoint, timeout = 100, headers = header, params = {"fields":["positions", "orders"]})
        print(json.dumps(response.json(), sort_keys = True, indent = 4))


    def placeOrder(self):
        # print("working on orders:", self.accessToken)
        currentSymbol = "MSFT"
        order_templates = {
            "complexOrderStrategyType": "NONE",
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                "instruction": "SELL",
                "quantity": 1,
                "instrument": {
                    "symbol": "GOOGL",
                    "assetType": "EQUITY"
                    }
                }
            ]
        }
    


        order_template = {
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "complexOrderStrategyType": "NONE",
            "requestedDestination": "AUTO",
            "price":2.85,
            "orderLegCollection": [
            {
                "orderLegType": "EQUITY",
                "instrument": {
                "assetType": "EQUITY",
                "symbol": "MNDO"
                },
                "instruction": "BUY",
                "quantity": 1
            }
            ],
            "orderStrategyType": "SINGLE",
            "cancelable": 'false',
            "editable": 'false',
            "statusDescription": "You do not have enough available cash/buying power for this order."
        }
        #     "orderType": "LIMIT",
        #     "session": "NORMAL",
        #     "duration": "DAY",
        #     "price": 10.0,
        #     "orderStrategyType": "SINGLE",
        #     "orderLegCollection": [
        #         {
        #             "instruction": "BUY",
        #             "quantity": 10,
        #             "instrument": {
        #                 "symbol": "GOOGL",
        #                 "assetType": "EQUITY"
        #             }
        #         }
        #     ]
        # }


        # {


        endpoint = 'https://api.tdameritrade.com/v1/accounts/{account_number}/orders'
        mainEndpoint = endpoint.format(account_number = self.faCredential['Account_Number'])

        header = {'Authorization':'Bearer {}'.format(self.accessToken)}
        response = requests.post(mainEndpoint, timeout = 100, headers = header, json = order_template)
        print(response.text)


    def price_history_minute(self, currentSymbol):
        header = {'Authorization':'Bearer {}'.format(self.accessToken)}
        url = "https://api.tdameritrade.com/v1/marketdata/{}/pricehistory".format(currentSymbol)
        dataM = requests.get(url, timeout = 20, headers=header, params=self.individualParam)
        data1 = dataM.json()
        dataM.close()

        data2 = self.afterStartTime(data1)
        return data2























    def getAccessTokenStart(self):
        try:
            headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
            data = { 'grant_type': 'refresh_token',  'refresh_token': self.faCredential['refresh_token'], 'client_id': self.faCredential['TDAmeritrade_API_consumerKey'], 'redirect_uri': self.faCredential['redirect_uri']}
            authReplyM = requests.post('https://api.tdameritrade.com/v1/oauth2/token', headers=headers, data=data)
            authReply = authReplyM.json()
            authReplyM.close()
            self.accessToken = authReply['access_token']
        except Exception as e:
            dError = traceback.format_exc()
            updatetb = '>Error:\n{}'.format(e)
            self.updateStatus(updatetb)
            updatetl = '>Error:\n{}'.format(dError)
            self.logger.warning(updatetl)
            print(dError)
            raise Exception('Unable to get the access token')

    def getConfFileV(self):
        with open(self.confFile, 'r', encoding="UTF-8") as f:
            content = f.readlines()
        faCredentials = {}
        for i in content:
            i1 = i.strip()
            i2 = i1.split('==>')
            i3 = i2[0].strip()
            i4 = i2[1].strip()
            faCredentials[i3] = i4
        return faCredentials



if __name__ == "__main__":
    oz = OrderZone()