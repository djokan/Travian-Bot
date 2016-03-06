import requests
from bs4 import BeautifulSoup
import re
import time
import json


class travian(object):
    def __init__(self):
        self.config={}
        self.delay=3
        self.vid=0 #village id
        self.getConfig()
        self.session = requests.Session()
        self.loggedIn=False
        self.login()


        while 1:
            try:
                time.sleep(10)

                if self.loggedIn:
                    print(time.time())
                    self.villages()
                else:
                    print('not login try login again.')
                    self.login()
            except:
                self.login()


    def villages(self):
        for vid in self.config['vids']:
            self.vid=str(vid)
            try:
                buildType=self.config['villages'][vid]['buildType']
            except:
                buildType='resource'
            print(buildType)
            if buildType == '0':
                pass
            elif buildType == 'resource':
                print('Start min Resource Building')
                self.build('resource')

    def build(self,type):
        try:
            delay=self.config['villages'][self.vid]['delay']
        except:
            delay=0
        if delay > time.time():
            return False
        html=self.sendRequest(self.config['server']+'dorf1.php?newdid='+self.vid+'&')
        dorf1=self.anlysisDorf1(html)
        self.config['villages'][self.vid]['delay']=dorf1['delay']
        self.config['villages'][self.vid]['resource']=dorf1['resource']
        self.config['villages'][self.vid]['fieldsList']=dorf1['fieldsList']
        print(dorf1)
        if type == 'resource':
            #if dorf1['delay'] == 0:

            #check Storage
            stockBarWarehouse=int(dorf1['resource'][8])
            stockBarGranary=int(dorf1['resource'][11])
            withoutFoodMaxProduction=int(max([dorf1['resource'][0],dorf1['resource'][1],dorf1['resource'][2]]))
            foodProduction=int(dorf1['resource'][3])


            if stockBarWarehouse<withoutFoodMaxProduction*5:
                print('Start to build WareHouse')
                self.buildBuilding(29)
                return True
            if stockBarWarehouse<foodProduction*5:
                print('Start to build Garanary')
                self.buildBuilding(25)
                return True

            #find min resource and fieldID

            fieldId=self.buildFindMinField()
            if fieldId:
                self.buildBuilding(fieldId)

    def buildFindMinField(self):
        dorf1=self.config['villages'][self.vid]
        resource=[dorf1['resource'][4],dorf1['resource'][5],dorf1['resource'][6],dorf1['resource'][7]]
        fieldsList=dorf1['fieldsList']
        newFieldsList={}
        notTopGidsList=[]
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] <10:
                newFieldsList[i]=fieldsList[i];
                if fieldsList[i]['gid'] not in notTopGidsList:
                    notTopGidsList.append(fieldsList[i]['gid'])

        #the resource list removed the all 10 level
        newResource={}
        minResourceWithoutTop=999999999999999
        minResourceWithoutTopKey=999999999999999  #always less then 5
        for i in range(len(resource)):
            if i+1 in notTopGidsList:
                if(resource[i]<minResourceWithoutTop):
                    minResourceWithoutTop=resource[i]
                    minResourceWithoutTopKey=i+1
        if minResourceWithoutTopKey > 5:
            return False
        minLevel=999999999999
        minLevelKey=99999999999

        for i in newFieldsList:
            if newFieldsList[i]['gid'] == minResourceWithoutTopKey:
                if newFieldsList[i]['level'] <minLevel:
                    minLevel= newFieldsList[i]['level']
                    minLevelKey=i

        if minLevelKey < 18: #it always less then 18
            return minLevelKey+1;
        return False;



    def buildBuilding(self, filedId):
        print('Start Building on Village '+ str(self.vid) +' field '+str(filedId))
        if filedId <=18:
            dorf=1
        else:
            dorf=2
        #upgrade
        #http://ts20.travian.tw/build.php?id=29
        html=self.sendRequest(self.config['server']+'build.php?newdid='+str(self.vid)+'&id='+str(filedId))

        #print(self.config['server']+'build.php?newdid='+str(self.vid)+'&id='+str(filedId))
        m=re.search('(?<=&amp;c=)(\w+)',html)

        #maybe not enough resource.
        if not m:
            return False
        c = m.group(0)
        #http://ts20.travian.tw/dorf2.php?a=18&id=31&c=130461
        self.sendRequest(self.config['server']+'dorf'+str(dorf)+'.php?a='+str(filedId)+'&c='+c+'&newdid='+str(self.vid))
        #self.sendRequest(self.server+'dorf2.php?a='+str(filedId)+'&c='+c+'&newdid='+str(self.village))

    def anlysisDorf1(self,html):
        dorf1={}
        parser = BeautifulSoup(html, "html5lib")
        fields = parser.find_all('div', {'class': 'labelLayer'})
        fieldsList = [field.find_parent('div')['class'] for field in fields]
        newFieldList={}
        for i in range(len(fieldsList)):
            if fieldsList[i][3] == 'underConstruction':
                gid=fieldsList[i][4].replace('gid','')
                level=fieldsList[i][5].replace('level','')
            else:
                gid=fieldsList[i][3].replace('gid','')
                level=fieldsList[i][4].replace('level','')

            newFieldList[i]={'gid':int(gid),'level':int(level)}
        dorf1['fieldsList']=newFieldList


        productionCompile=re.compile('"l[1-4]":\s(-?[1-9]\d*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            prs[i]=int(prs[i])
        dorf1['resource'] =prs
        isUnderConstruction = parser.find('div', {'class': 'buildDuration'})


        dorf1['delay']=0
        if isUnderConstruction == None:
            underConstruction=False
        else:
            underConstruction=True
            timer1=parser.find('span',{'id':'timer1'})
            try:
                timer1a=timer1.text.split(':')
                #delay for current building
                dorf1['delay']=60*60*int(timer1a[0])+60*int(timer1a[1])+int(timer1a[2])+time.time()
            except:
                pass
        return dorf1



    def getConfig(self):
        with open('config.json','r+') as configFile:
            self.config=json.load(configFile)
            configFile.close()
    def saveConfig(self):
         with open('config.json','r+') as configFile:
            self.config=json.load(configFile)
            configFile.seek(0)
            json.dump(self.config, configFile)
            configFile.close()
    def login(self):
        print('Start Login')
        html = self.sendRequest(self.config['server'])
        if html==False:
            return False
        parser = BeautifulSoup(html, "html5lib")
        s1 = parser.find('button', {'name': 's1'})['value'].encode('utf-8')
        login = parser.find('input', {'name': 'login'})['value']
        #start login
        data = {
			    'name' : self.config['username'],
			    'password': self.config['password'],
			    's1': s1,
			    'w': '1366:768',
			    'login': login
			}
        html=self.sendRequest( self.config['server'] + 'dorf1.php', data)
        if html==False:
            return False
        self.loggedIn=True
        #soup=BeautifulSoup(h.text, "html5lib")
        #print(soup.prettify())
        self.getInfo(html)

    def getInfo(self, html):
        villageVidsCompile=re.compile('\?newdid=(\d+)')
        villageVids = villageVidsCompile.findall(html)
        villageAmount = len(villageVids)
        nationCompile=re.compile('nation(\d)')
        nation = nationCompile.findall(html)[0]
        xCompile=re.compile('coordinateX">\(&#x202d;&(#45;)*&*#x202d;(\d+)')
        X = xCompile.findall( html)
        yCompile=re.compile('coordinateY">&#x202d;&(#45;)*&*#x202d;(\d+)')
        Y = yCompile.findall( html)
        ajaxTokenCompile=re.compile('ajaxToken\s*=\s*\'(\w+)\'')
        ajaxToken = ajaxTokenCompile.findall( html)[0]
        x = []
        y = []
        for i in range(villageAmount):
            if '#45' in X[i][0]:
                x.append('-%s' %X[i][1])
            else:
                x.append(X[i][1])
            if '#45' in Y[i][0]:
                y.append('-%s' %Y[i][1])
            else:
                y.append(Y[i][1])
        self.config['villagesAmount']=villageAmount
        self.config['vids']=villageVids
        self.config['x']=x
        self.config['y']=y
        self.config['nation']=nation
        self.config['ajaxToken']=ajaxToken
        print(self.config)
        #self.saveConfig()
    def getVillages(self):
        pass

    def sendRequest(self,url,data={}):
        time.sleep(self.delay)
        #print(url)
        #print(len(data))
        try:
            if len(data) == 0:
                #print('get')
                #html = requests.get(url,headers=self.headers,cookies=self.cookies)
                html=self.session.get(url,headers=self.config['headers'])
            else:
                #print('POST')
                html=self.session.post(url,headers=self.config['headers'],data=data)
        except:
            print('Net problem, cant fetch the URL'+url)
            return False



        if self.loggedIn and not 'ajax.php' in url:
            if 'playerName' not in html.text:

                #log.warn('Suddenly logged off')
                print('Suddenly logged off')
                self.loggedIn = False
                reconnects = 0
                tryAgain = True
                while reconnects <= 2 and tryAgain:
                    try:
                        self.login()
                        html = self.sendRequest(url, data)
                        tryAgain = False
                    except self.UnableToLogIn:
                        reconnects += 1
                        #log.error('Could not relogin %d time' %reconnects)
                        print(('Could not relogin %d time' %reconnects))
                        time.sleep(self.delay)
        return html.text

travian();