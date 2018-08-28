import requests
from bs4 import BeautifulSoup
import re
import time
import json
import datetime
import traceback
from random import randint
WAREHOUSECOEFF = 0.8
doneTasks = {}
doneTasksDelay = {}
def doOnceInSeconds(delay,function,function_name,*args):
    if not function_name in doneTasks or doneTasks[function_name]+datetime.timedelta(seconds=doneTasksDelay[function_name])<datetime.datetime.now():
        doneTasks[function_name] = datetime.datetime.now()
        doneTasksDelay[function_name] = delay
        function(*args)
def getRegexValue(stringFrom,regex):
    try:
        idbCompile=re.compile(regex,re.S)
        return idbCompile.findall(stringFrom)[0]
    except:
        return None
def getAdventureData(html):
    data = {}
    names = ["send","kid","from","a"]
    for name in names:
        data[name] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    return data
def getFirstMarketplaceData(html):
    data = {}
    names = ["id","t"]
    for name in names:
        data[name] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    data['cmd']='prepareMarketplace'
    data['x2']='1'
    data['ajaxToken']=getRegexValue(html,'return \'([a-z\d]{32})\';')
    return data
def getSecondMarketplaceData(html):
    data = {}
    names = ["id","t","a","sz","kid","c"]
    for name in names:
        data[name] = getRegexValue(html,'name=\\\\"'+name+'\\\\"[^>]+value=\\\\"([^\\\\]*)\\\\"')
    data['cmd']='prepareMarketplace'
    data['x2']='1'
    return data
class travian(object):
    def __init__(self):
        self.RequestedResources = {}
        self.config={}
        self.delay=3
        self.vid=0 #village id
        self.getConfig()
        self.minlvl = -1
	self.proxies = dict(http='socks5://127.0.0.1:9050',https='socks5://127.0.0.1:9050')
        self.session = requests.Session()
        self.loggedIn=False
        self.login()
        while 1:
            try:
                if self.loggedIn==False:
                    self.login()
                self.villages()
                self.getConfigViaTemp()
            except Exception as e:
                print(traceback.format_exc())
                print('Waiting for internet connection (30 sec)')
                time.sleep(30)
                continue
            if self.minlvl == -1:
                sleepDelay = randint(500,800)
            else:
                if self.minlvl<4:
                    sleepDelay = randint(100,300)
                elif self.minlvl<6:
                    sleepDelay = randint(300,500)
                else:
                    sleepDelay = randint(500,800)
            print('Sleeping! Time= ' + str(datetime.datetime.time(datetime.datetime.now())) + ', Delay= ' + str(sleepDelay/60) + ' min ' + str(sleepDelay%60) + ' sec' )
            time.sleep(sleepDelay)
    def getMinMarketTreshold(self):
        minMarketTreshold= 400
        if 'minMarketTreshold' in self.config:
            minMarketTreshold = self.config['minMarketTreshold']
        return minMarketTreshold

    def holdSmallCelebration(self):
        print('Hold Small Celebration village ' + self.vid)
        html = self.goToBuildingByName('Town Hall','a=1&')
    def sendResources(self,x,y,r1,r2,r3,r4,sendifNotEnough):
        html = self.goToBuildingByName('Marketplace','t=5&')
        available = getRegexValue(html,'class="merchantsAvailable">&#x202d;(\d+)')
        available = int(available)
        cancarry = getRegexValue(html,'can carry <b>(\d+)<\/b>')
        cancarry = int(cancarry)
        print('AVAILABLE:' + str(available))
	if sendifNotEnough==False and int(r1)+int(r2)+int(r3)+int(r4)>available*cancarry:
            return
        if int(r1)+int(r2)+int(r3)+int(r4)>available*cancarry:
            coeff = 1.0*available*cancarry/(int(r1)+int(r2)+int(r3)+int(r4))
            r1 = int(int(r1)*coeff)
            r2 = int(int(r2)*coeff)
            r3 = int(int(r3)*coeff)
            r4 = int(int(r4)*coeff)
            r1 = r1-r1%50
            r2 = r2-r2%50
            r3 = r3-r3%50
            r4 = r4-r4%50
            r1 = str(r1)
            r2 = str(r2)
            r3 = str(r3)
            r4 = str(r4)
        tempp = 0
        while (int(r1)+int(r2)+int(r3)+int(r4))%cancarry>0 and (int(r1)+int(r2)+int(r3)+int(r4))%cancarry<cancarry*0.85 and int(r1)+int(r2)+int(r3)+int(r4)>self.getMinMarketTreshold():
            print(r1+','+r2+','+r3+','+r4)
            if tempp%4==0 and int(r1)>50:
                r1 = str(int(r1)-50)
            if tempp%4==1 and int(r2)>50:
                r2 = str(int(r2)-50)
            if tempp%4==2 and int(r3)>50:
                r3 = str(int(r3)-50)
            if tempp%4==3 and int(r4)>50:
                r4 = str(int(r4)-50)
            tempp = tempp+1
        print('Trying to send ' + str(self.vid) + ' ('+r1+','+r2+','+r3+','+r4+') to ('+x+'|'+y+')')
        print('a ' + str(int(r1)+int(r2)+int(r3)+int(r4)) + ' ' + str(self.getMinMarketTreshold()))
        if int(r1)+int(r2)+int(r3)+int(r4)<self.getMinMarketTreshold():
            return
        data = getFirstMarketplaceData(html)
        print('Sending resources from ' + str(self.vid) + ' ('+r1+','+r2+','+r3+','+r4+') to ('+x+'|'+y+')')
        data['r1'] = r1
        data['r2'] = r2
        data['r3'] = r3
        data['r4'] = r4
        data['x'] = x
        data['y'] = y
        data['dname'] = ''
        token = data['ajaxToken']
        olddata= data
        html = self.sendRequest(self.config['server']+'ajax.php?cmd=prepareMarketplace',data)
        oldhtml = html
        data = getSecondMarketplaceData(html)
        data['r1'] = r1
        data['r2'] = r2
        data['r3'] = r3
        data['r4'] = r4
        data['ajaxToken'] = token
        html=self.sendRequest(self.config['server']+'ajax.php?cmd=prepareMarketplace',data)
        if not 'Resources have been dispatched' in html:
            print('MarketDebugInfo:')
            print(oldhtml)
            print(olddata)
            print('MarketDebugInfo2:')
            print(html)
            print(data)
    def goToBuildingByName(self,name,linkdata):
        html=self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.vid))
        idb = getRegexValue(html,'build.php\?id=(\d+)\'" title="'+name)
        return self.sendRequest(self.config['server']+'build.php?'+linkdata+'id='+idb+'&newdid='+str(self.vid))
    def autoAdventure(self):
        print('Starting adventure')
        html=self.sendRequest(self.config['server']+'hero.php?t=3')
        link = getRegexValue(html,'href="([^"]+)">To the adventure')
        if link==None:
            return
        link = link.replace("&amp;","&")
        print(link)
        html=self.sendRequest(self.config['server']+link)
        data=getAdventureData(html)
        for key in data:
            if data[key]==None:
                return
        print(data)
        html=self.sendRequest(self.config['server']+'start_adventure.php',data)
    def villages(self):
        self.minlvl = -1
        for vid in self.config['vids']:
            self.vid=str(vid)
            html=self.sendRequest(self.config['server']+'dorf1.php?newdid='+self.vid+'&')
            dorf1=self.config['villages'][self.vid]
            if self.adventureExists and 'autoAdventure' in self.config:
                doOnceInSeconds(randint(3000,4200)*6,self.autoAdventure,'adventure')
            if 'smallCelebration' in self.config['villages'][vid]:
                doOnceInSeconds(randint(3000,4000),self.holdSmallCelebration,'holdSmallCelebration'+self.vid)
            if 'requestResourcesFrom' in self.config['villages'][vid]:
                resource=[dorf1['resource'][4],dorf1['resource'][5],dorf1['resource'][6],dorf1['resource'][7]]
                capacity=[dorf1['resource'][8],dorf1['resource'][9],dorf1['resource'][10],dorf1['resource'][11]]
                send = [0,0,0,0]
                tempsum = 0
		for i in range(4):
                    if (capacity[i]*(WAREHOUSECOEFF-0.1)>resource[i]):
                        send[i] = capacity[i]*WAREHOUSECOEFF-resource[i]
                        send[i] = int(send[i])
                        send[i] = send[i] - send[i]%100
                    else:
                        send[i] = 0
                    tempsum = tempsum + send[i]
                index = randint(0,len(self.config['villages'][vid]['requestResourcesFrom'])-1)
                fromtemp = self.config['villages'][vid]['requestResourcesFrom'][index]
                timetemp = self.config['villages'][vid]['requestResourcesFromTime'][index]
                
                if tempsum>self.getMinMarketTreshold():
                    self.RequestedResources[fromtemp] = [vid,send[0],send[1],send[2],send[3],timetemp]
                #self.requestResourcesIfNeeded()
            try:
                buildType=self.config['villages'][vid]['buildType']
            except:
                self.config['villages'][vid]={}
                buildType='0'
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
                if 'building2' in self.config['villages'][vid]:
                    tempDelay = randint(5,15)
                    print('sleeping for ' + str(tempDelay) + " seconds")
                    time.sleep(tempDelay)
                    print('Start to build other building '+ str(self.config['villages'][vid]['building2']))
                    #self.config['villages'][vid]['building']
                    fieldId=int( self.config['villages'][vid]['building2'])
                    if fieldId > 0:
                        self.buildBuilding(fieldId)
            elif buildType == 'both':
                print('Start min Resource Building')
                self.build('resource')
                tempDelay = randint(3,7)
                print('sleeping for ' + str(tempDelay) + " seconds")
                time.sleep(tempDelay)
                print('Start to build building '+ str(self.config['villages'][vid]['building']))
                #self.config['villages'][vid]['building']
                fieldId=int( self.config['villages'][vid]['building'])
                if fieldId > 0:
                    self.buildBuilding(fieldId)
                if 'building2' in self.config['villages'][vid]:
                    tempDelay = randint(3,7)
                    print('sleeping for ' + str(tempDelay) + " seconds")
                    time.sleep(tempDelay)
                    print('Start to build other building '+ str(self.config['villages'][vid]['building2']))
                    #self.config['villages'][vid]['building']
                    fieldId=int( self.config['villages'][vid]['building2'])
                    if fieldId > 0:
                        self.buildBuilding(fieldId)
        for vid in self.RequestedResources:
            print('Trying to send' + str(self.RequestedResources[vid]))
            self.vid=str(vid)
            resource=[self.config['villages'][vid]['resource'][4],self.config['villages'][vid]['resource'][5],self.config['villages'][vid]['resource'][6],self.config['villages'][vid]['resource'][7]]
            if 'holdResources' in self.config['villages'][vid]:
                for i in range(4):
                    resource[i]= resource[i]-self.config['villages'][vid]['holdResources'][i]
                    if resource[i]<0:
                        resource[i]=0
            tempsum = 0
            for i in range(4):
                if (resource[i]<self.RequestedResources[vid][i+1]):
                    self.RequestedResources[vid][i+1] = resource[i]-resource[i]%50
                tempsum = tempsum + self.RequestedResources[vid][i+1]
            print('Trying to send' + str(self.RequestedResources[vid]))
            if (tempsum<self.getMinMarketTreshold()):
                continue
            to = str(self.RequestedResources[vid][0])
            r1 = str(self.RequestedResources[vid][1])
            r2 = str(self.RequestedResources[vid][2])
            r3 = str(self.RequestedResources[vid][3])
            r4 = str(self.RequestedResources[vid][4])
            temptime = self.RequestedResources[vid][5]

            doOnceInSeconds(temptime,self.sendResources,'sendResources'+to,self.config['villages'][to]['x'],self.config['villages'][to]['y'],r1,r2,r3,r4,True)
        self.RequestedResources = {}

    def build(self,type):
        try:
            delay=self.config['villages'][self.vid]['delay']
        except:
            delay=0
        if delay > time.time():
            return False
        
            
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
        minlvl = 30
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] < minlvl:
                minlvl = fieldsList[i]['level']
        if self.minlvl == -1 or self.minlvl>minlvl:
            self.minlvl = minlvl
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
        if self.greyField == True and dorf1['stockBarFreeCrop']<10:
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
    def analysisBuild(self,html):
        build={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            build['stockBarFreeCrop']=int(prs[i].replace(".",""))
        productionCompile=re.compile('"l[1-4]":\s(-?[1-9]\d*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            prs[i]=int(prs[i])
        
        build['resource'] =prs
        isUnderConstruction = parser.find('div', {'class': 'buildDuration'})
        build['delay']=0
        if isUnderConstruction == None:
            underConstruction=False
        else:
            underConstruction=True
            timer1=parser.find('span',{'id':'timer1'})
            try:
                timer1a=timer1.text.split(':')
                #delay for current building
                build['delay']=60*60*int(timer1a[0])+60*int(timer1a[1])+int(timer1a[2])+time.time()
            except:
                pass
        return build
    def analysisDorf2(self,html):
        dorf2={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            dorf2['stockBarFreeCrop']=int(prs[i].replace(".",""))
        productionCompile=re.compile('"l[1-4]":\s(-?[1-9]\d*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            prs[i]=int(prs[i])
        
        dorf2['resource'] =prs
        isUnderConstruction = parser.find('div', {'class': 'buildDuration'})


        dorf2['delay']=0
        if isUnderConstruction == None:
            underConstruction=False
        else:
            underConstruction=True
            timer1=parser.find('span',{'id':'timer1'})
            try:
                timer1a=timer1.text.split(':')
                #delay for current building
                dorf2['delay']=60*60*int(timer1a[0])+60*int(timer1a[1])+int(timer1a[2])+time.time()
            except:
                pass
        return dorf2
    def analysisDorf1(self,html):
        dorf1={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        fields = parser.find_all('div', {'class': 'labelLayer'})
        fieldsList = [field.find_parent('div')['class'] for field in fields]
        newFieldList={}
        self.greyField = False
        for i in range(len(fieldsList)):
            if (len(fieldsList[i])<5):
                self.greyField = True
            gid=fieldsList[i][len(fieldsList[i])-2].replace('gid','')
            level=fieldsList[i][len(fieldsList[i])-1].replace('level','')
            newFieldList[i]={'gid':int(gid),'level':int(level)}
        dorf1['fieldsList']=newFieldList
        self.adventureExists = False
        if 'class="speechBubbleContainer' in html:
            self.adventureExists = True
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            dorf1['stockBarFreeCrop']=int(prs[i].replace(".",""))
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


    def getConfigViaTemp(self):
        with open('config.json','r+') as configFile:
            self.tempconfig=json.load(configFile)
            configFile.close()
            self.config = self.tempconfig
        if 'proxies' in self.config:
            self.proxies = dict()
            if 'http' in self.config['proxies']:
                self.proxies['http'] = self.config['proxies']['http']
            if 'https' in self.config['proxies']:
                self.proxies['https'] = self.config['proxies']['https']
        html=self.sendRequest( self.config['server'] + 'dorf1.php', {})
        if html==False:
            return False
        self.loggedIn=True
        #soup=BeautifulSoup(h.text, "html5lib")
        #print(soup.prettify())
        self.getInfo(html)
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
        #print(self.config)
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
        temphtml = html.text
        if 'newdid=' in url:
            tempvid = getRegexValue(url,'newdid=(\d+)')
            if 'dorf1.php' in url:
                dorf1 = self.analysisDorf1(temphtml)
                self.config['villages'][tempvid]['delay']=dorf1['delay']
                self.config['villages'][tempvid]['resource']=dorf1['resource']
                self.config['villages'][tempvid]['fieldsList']=dorf1['fieldsList']
                self.config['villages'][tempvid]['stockBarFreeCrop']=dorf1['stockBarFreeCrop']
            if 'dorf2.php' in url:
                dorf2 = self.analysisDorf2(temphtml)
                self.config['villages'][tempvid]['delay']=dorf2['delay']
                self.config['villages'][tempvid]['resource']=dorf2['resource']
                self.config['villages'][tempvid]['stockBarFreeCrop']=dorf2['stockBarFreeCrop']
            if 'build.php' in url:
                build = self.analysisBuild(temphtml)
                self.config['villages'][tempvid]['delay']=build['delay']
                self.config['villages'][tempvid]['resource']=build['resource']
                self.config['villages'][tempvid]['stockBarFreeCrop']=build['stockBarFreeCrop']
                

        return html.text

travian();
