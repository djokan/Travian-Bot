import requests
from bs4 import BeautifulSoup
import re
import time
import json
import datetime
from random import randint

class travian(object):
    def __init__(self):
        self.config={}
        self.delay=3
        self.vid=0 #village id
        self.getConfig()
	self.proxies = dict(http='socks5://127.0.0.1:9050',https='socks5://127.0.0.1:9050')
        self.session = requests.Session()
        self.loggedIn=False
        self.login()


        while 1:
            try:
                if self.loggedIn==False:
                    self.login()
                self.villages()
            except:
                print('Waiting for internet connection (30 sec)')
                time.sleep(30)
                continue
            sleepDelay = randint(500,800)
            print('Sleeping! Time= ' + str(datetime.datetime.time(datetime.datetime.now())) + ', Delay= ' + str(sleepDelay/60) + ' min ' + str(sleepDelay%60) + ' sec' )
            time.sleep(sleepDelay)


    def villages(self):

        for vid in self.config['vids']:
            self.vid=str(vid)
            try:
                buildType=self.config['villages'][vid]['buildType']
            except:
                self.config['villages'][vid]={}
                buildType='resource'
            print('Village: '+str(vid)+' build type:'+buildType)
            if buildType == '0':
                pass
            elif buildType == 'resource':
                print('Start min Resource Building')
                self.build('resource')
            elif buildType == 'building':
                print('Start to build building '+ str(self.config['villages'][vid]['building']))
                #self.config['villages'][vid]['building']
                fieldId=int( self.config['villages'][vid]['building'])
                if fieldId > 0:
                    self.buildBuilding(fieldId)

    def build(self,type):
        try:
            delay=self.config['villages'][self.vid]['delay']
        except:
            delay=0
        if delay > time.time():
            return False
        html=self.sendRequest(self.config['server']+'dorf1.php?newdid='+self.vid+'&')
        dorf1=self.anlysisDorf1(html)
        print(dorf1)
        self.config['villages'][self.vid]['delay']=dorf1['delay']
        self.config['villages'][self.vid]['resource']=dorf1['resource']
        self.config['villages'][self.vid]['fieldsList']=dorf1['fieldsList']

        if type == 'resource':
            #if dorf1['delay'] == 0:

            #check 

            #stockBarWarehouse=int(dorf1['resource'][8])
            #stockBarGranary=int(dorf1['resource'][11])
            #withoutFoodMaxProduction=int(max([dorf1['resource'][0],dorf1['resource'][1],dorf1['resource'][2]]))
            #foodProduction=int(dorf1['resource'][3])


            #if stockBarWarehouse<withoutFoodMaxProduction*100 and stockBarWarehouse < 10000 or stockBarWarehouse<withoutFoodMaxProduction*10 and stockBarWarehouse < 80000:
            #    print('Start to build WareHouse')
            #    self.buildBuilding(29)
            #    return True
            #if stockBarGranary<foodProduction*100 and stockBarGranary < 10000 or stockBarGranary<foodProduction*10 and stockBarGranary < 80000:
            #    print('Start to build Garanary')
            #    self.buildBuilding(25)
            #    return True

            #find min resource and fieldID

            fieldId=self.buildFindMinField()
            if fieldId:
                self.buildBuilding(fieldId)


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
        try:
            try:
                m=re.search('waiting loop',html)
                if m != None:
                    print 'waiting loop detected!'
                    return False
            except:
                return False
            m=re.search('(?<=&amp;c=)(\w+)',html)
        #maybe not enough resource.
        except:
            return False
        if m == None:
            return False
        c = m.group(0)

        #http://ts20.travian.tw/dorf2.php?a=18&id=31&c=130461
        self.sendRequest(self.config['server']+'dorf'+str(dorf)+'.php?a='+str(filedId)+'&c='+c+'&newdid='+str(self.vid))
        #self.sendRequest(self.server+'dorf2.php?a='+str(filedId)+'&c='+c+'&newdid='+str(self.village))

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

    def buildFindMinFieldModified(self):
        dorf1=self.config['villages'][self.vid]
        resource=[dorf1['resource'][4],dorf1['resource'][5],dorf1['resource'][6],dorf1['resource'][7]]
        fieldsList=dorf1['fieldsList']
        newFieldsList={}
        notTopGidsList=[]
        minlvl = 30
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] < minlvl:
                minlvl = fieldsList[i]['level']
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] == minlvl:
                newFieldsList[i]=fieldsList[i];
                if fieldsList[i]['gid'] not in notTopGidsList:
                    notTopGidsList.append(fieldsList[i]['gid'])
        print(newFieldsList)
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
        if self.lackOfCrop == True:
            minResourceWithoutTopKey = 4
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

    def analysisDorf2(self,html):
        return False
    def anlysisDorf1(self,html):
        dorf1={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        fields = parser.find_all('div', {'class': 'labelLayer'})
        fieldsList = [field.find_parent('div')['class'] for field in fields]
        newFieldList={}
        self.lackOfCrop = False
        for i in range(len(fieldsList)):
            if (len(fieldsList[i])<5):
                self.lackOfCrop = True
            gid=fieldsList[i][len(fieldsList[i])-2].replace('gid','')
            level=fieldsList[i][len(fieldsList[i])-1].replace('level','')
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
        if 'proxies' in self.config:
            self.proxies = dict()
            if 'http' in self.config['proxies']:
                self.proxies['http'] = self.config['proxies']['http']
            if 'https' in self.config['proxies']:
                self.proxies['https'] = self.config['proxies']['https']
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
        villageVidsCompile=re.compile('coordinateX&')
        villageVids = villageVidsCompile.findall(html)
        villageAmount = len(villageVids)
        nationCompile=re.compile('nation(\d)')
        nation = nationCompile.findall(html)[0]
        xCompile=re.compile('coordinateX&quot;&gt;\(&amp;#x202d;(-?\d+)')
        X = xCompile.findall( html)
        yCompile=re.compile('coordinateY&quot;&gt;&amp;#x202d;(-?\d+)')
        Y = yCompile.findall( html)
        ajaxTokenCompile=re.compile('ajaxToken\s*=\s*\'(\w+)\'')
        ajaxToken = ajaxTokenCompile.findall( html)[0]
        x = []
        y = []
        for i in range(villageAmount):
            x.append(X[i])
            y.append(Y[i])
        self.config['villagesAmount']=villageAmount
        self.config['vids'] = []
        for vid in self.config['villages']:
	    self.config['vids'].append(vid) 
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
                if 'proxies' in self.config:
                    html=self.session.get(url,headers = self.config['headers'], proxies=self.proxies)
                else:
                    html=self.session.get(url,headers=self.config['headers'])
            else:
                #print('POST')
                if 'proxies' in self.config:
                    html=self.session.post(url,headers=self.config['headers'],data=data, proxies=self.proxies)
                else:
                    html=self.session.post(url,headers=self.config['headers'],data=data)
        except:
            print('Net problem, cant fetch the URL'+url)
            return False



        if self.loggedIn and not 'ajax.php' in url and not self.config['server']==url:

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
