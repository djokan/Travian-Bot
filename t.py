import requests
from bs4 import BeautifulSoup
import re
import time
import json
import datetime
import traceback
import random
from random import randint
WAREHOUSECOEFF = 0.8
doneTasks = {}
doneTasksDelay = {}
def getConstructionFinishTimes(html):
    parser = BeautifulSoup(html, "html5lib")
    constructionTimeFields = parser.find_all('div', {'class': 'buildDuration'})
    constructionFinishTimes = []
    for constructionTimeField in constructionTimeFields:
        remainingTime = int(constructionTimeField.find('span', {'class': 'timer'})['value'])
        constructionFinishTimes.append(remainingTime + time.time())
    return constructionFinishTimes
def mergeDict(d1,d2):
    ret = {}
    for e in d1:
        ret[e] = d1[e]
    for e in d2:
        ret[e] = d2[e]
    return ret
def doOnceInSeconds(delay,function,function_name,*args):
    if not function_name in doneTasks or doneTasks[function_name]+datetime.timedelta(seconds=doneTasksDelay[function_name])<datetime.datetime.now():
        doneTasks[function_name] = datetime.datetime.now()
        doneTasksDelay[function_name] = delay
        function(*args)
def getResourceData(html):
    productionCompile = re.compile('"l[1-4]":\s(-?\d*)')
    prs = productionCompile.findall(html)
    for i in range(len(prs)):
        prs[i] = int(prs[i])
    return {'production': prs[0:4], 'availableResources' : prs[4:8], 'capacity' : prs[8:12]}
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
        self.currentVid=0 #village id
        self.getConfig()
        self.proxies = dict(http='socks5://127.0.0.1:9050', https='socks5://127.0.0.1:9050')
        self.session = requests.Session()
        self.loggedIn=False
        self.login()
        while 1:
            try:
                if self.loggedIn==False:
                    self.login()
                self.checkVillages()
                self.printProductionData()
                
            except Exception as e:
                print(traceback.format_exc())
                print('Waiting for internet connection (30 sec)')
                time.sleep(30)
                self.getConfigViaTemp()
                continue
            sleepDelay = self.getNextSleepDelay()
            print('Sleeping! Time= ' + str(datetime.datetime.time(datetime.datetime.now())) + ', Delay= ' + str(int(sleepDelay/60)) + ' min ' + str(int(sleepDelay%60)) + ' sec' )
            print('Press Ctrl+C if you do not want to wait!')
            try:
                time.sleep(sleepDelay)
            except KeyboardInterrupt:
                pass
            print('Woke up!')
            try:
                self.getConfigViaTemp()
            except Exception as e:
                pass

    def getNextSleepDelay(self):
        now = datetime.datetime.now()

        isNightTime = False
        if now.hour<randint(8,10) and now.hour >= randint(0,2):
            isNightTime = True
        sleepDelay = 0
        if self.getGlobalMinResourceFieldLevel() > 20:
            sleepDelay = randint(1500,4000)
        else:
            if self.getGlobalMinResourceFieldLevel()<3:
                sleepDelay = randint(600,2500)
            else:
                sleepDelay = randint(1500,4000)
        if isNightTime:
            sleepDelay = randint(9000,15000)
        constructionFinishTimes = self.getAllConstructionFinishTimes()
        for constructionFinishTime in constructionFinishTimes:
            constructionFinishDelay = constructionFinishTime - time.time()
            if constructionFinishDelay < sleepDelay*1.4 and constructionFinishDelay > sleepDelay*0.4:
                sleepDelay = constructionFinishDelay + randint(0, 300)
                break
        return sleepDelay

    def getAllConstructionFinishTimes(self):
        constructionFinishTimes = []
        for vid in self.config['villages']:
            try:
                for finishTime in self.config['villages'][str(vid)]['constructionFinishTimes']:
                    constructionFinishTimes.append(finishTime)
            except Exception as e:
                pass
        return constructionFinishTimes
    def printProductionData(self):
        woodProduction=0
        clayProduction=0
        ironProduction=0
        cropProduction=0
        allProduction=0
        for vid in self.config['villages']:
            self.currentVid=str(vid)
            villageData=self.config['villages'][self.currentVid]
            production=None
            try:
                villageProduction = villageData['production']
            except Exception as e:
                self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.currentVid))
                villageProduction = villageData['production']
            woodProduction+=villageProduction[0]
            clayProduction+=villageProduction[1]
            ironProduction+=villageProduction[2]
            cropProduction+=villageProduction[3]
        allProduction += woodProduction + clayProduction + ironProduction + cropProduction
        print('Production: wood-' + str(woodProduction) + ' clay-' + str(clayProduction) + ' iron-' + str(ironProduction) + ' crop-' + str(cropProduction) + ' all-' + str(allProduction))
    def getMinMarketTreshold(self):
        minMarketTreshold= 400
        if 'minMarketTreshold' in self.config:
            minMarketTreshold = self.config['minMarketTreshold']
        return minMarketTreshold

    def holdSmallCelebration(self):
        print('Hold Small Celebration village ' + self.currentVid)
        html = self.goToBuildingByName('Town Hall','a=1&')
    def sendResources(self,x,y,r1,r2,r3,r4,sendifNotEnough):
        html = self.goToBuildingByName('Marketplace','t=5&')
        available = getRegexValue(html,'class="merchantsAvailable">&#x202d;(\d+)')
        available = int(available)
        cancarry = getRegexValue(html,'can carry <b>(\d+)<\/b>')
        cancarry = int(cancarry)
        print('Available merchants:' + str(available))
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
            if tempp%4==0 and int(r1)>50:
                r1 = str(int(r1)-50)
            if tempp%4==1 and int(r2)>50:
                r2 = str(int(r2)-50)
            if tempp%4==2 and int(r3)>50:
                r3 = str(int(r3)-50)
            if tempp%4==3 and int(r4)>50:
                r4 = str(int(r4)-50)
            tempp = tempp+1
        print('Trying to send ' + str(self.currentVid) + ' ('+str(r1)+','+str(r2)+','+str(r3)+','+str(r4)+') to ('+str(x)+'|'+str(y)+')')
        if int(r1)+int(r2)+int(r3)+int(r4)<self.getMinMarketTreshold():
            print('resource amount is too small')
            return
        data = getFirstMarketplaceData(html)
        print('Sending resources from ' + str(self.currentVid) + ' ('+str(r1)+','+str(r2)+','+str(r3)+','+str(r4)+') to ('+str(x)+'|'+str(y)+')')
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
        if 'allowed' in oldhtml:
            print('Exceeded sending resource amount to this player!')
            return
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
            print(data)
    def goToBuildingByName(self,name,linkdata):
        html=self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.currentVid))
        idb = getRegexValue(html,'build.php\?id=(\d+)\'" title="'+name)
        return self.sendRequest(self.config['server']+'build.php?'+linkdata+'id='+idb+'&newdid='+str(self.currentVid))
    def autoAdventure(self):
        print('Starting adventure')
        html=self.sendRequest(self.config['server']+'hero.php?t=3')
        data=getAdventureData(html)
        for key in data:
            if data[key]==None:
                return
        print(data)
        html=self.sendRequest(self.config['server']+'start_adventure.php',data)
    def checkVillages(self):
        for vid in self.config['villages']:
            self.currentVid=str(vid)
            checkPeriod = self.getVillageCheckPeriod(vid)
            doOnceInSeconds(checkPeriod, self.checkVillage, 'checkvill' + self.currentVid, vid)
        if self.adventureExists and 'autoAdventure' in self.config and self.config['autoAdventure'] == 'true':
            doOnceInSeconds(randint(3000,4200)*6,self.autoAdventure,'adventure')
        self.villagesSendResources()
    def checkVillage(self,vid):
        html=self.sendRequest(self.config['server']+'dorf1.php?newdid='+self.currentVid+'&')
        data=self.config['villages'][self.currentVid]

        if 'smallCelebration' in self.config['villages'][vid]:
            doOnceInSeconds(randint(3000,4000),self.holdSmallCelebration,'holdSmallCelebration'+self.currentVid)
        if 'push' in self.config['villages'][vid]:
            pushCoordinates=self.config['villages'][vid]['push']
            pushResourcesAndPeriod=self.config['villages'][vid]['pushparams']

            availableResources=None
            try:
                availableResources=self.config['villages'][vid]['availableResources']
            except Exception as e:
                self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.currentVid))
                availableResources=self.config['villages'][vid]['availableResources']
            if 'holdResources' in self.config['villages'][vid]:
                for i in range(4):
                    tmprs = availableResources[i]
                    availableResources[i]= availableResources[i]-self.config['villages'][vid]['holdResources'][i]
                    if tmprs<availableResources[i]:
                        availableResources[i]=tmprs
                    if availableResources[i]<0:
                        availableResources[i]=0
            sendingSum = 0
            for i in range(4):
                if (availableResources[i]<pushResourcesAndPeriod[i]):
                    pushResourcesAndPeriod[i] = availableResources[i]-availableResources[i]%50
                sendingSum = sendingSum + pushResourcesAndPeriod[i]
            if (sendingSum>=self.getMinMarketTreshold()):
                doOnceInSeconds(pushResourcesAndPeriod[4],self.sendResources,'push '+self.currentVid,pushCoordinates[0],pushCoordinates[1],str(pushResourcesAndPeriod[0]),str(pushResourcesAndPeriod[1]),str(pushResourcesAndPeriod[2]),str(pushResourcesAndPeriod[3]),True)
        if 'requestResourcesFrom' in self.config['villages'][vid]:
            availableResources=data['availableResources']
            
            capacity=data['capacity']
            send = [0,0,0,0]
            sendingSum = 0
            for i in range(4):
                if (capacity[i]*(WAREHOUSECOEFF-0.1)>availableResources[i]):
                    send[i] = capacity[i]*WAREHOUSECOEFF-availableResources[i]
                    send[i] = int(send[i])/len(self.config['villages'][vid]['requestResourcesFrom'])
                    send[i] = send[i] - send[i]%100
                else:
                    send[i] = 0
                sendingSum = sendingSum + send[i]
            timetemp = self.config['villages'][vid]['requestResourcesFromTime'][0]
            for i in range(len(self.config['villages'][vid]['requestResourcesFrom'])):
                if timetemp<self.config['villages'][vid]['requestResourcesFromTime'][i]:
                    timetemp = self.config['villages'][vid]['requestResourcesFromTime'][i]
            for index in range(len(self.config['villages'][vid]['requestResourcesFrom'])):
                fromtemp = self.config['villages'][vid]['requestResourcesFrom'][index]
                if sendingSum>self.getMinMarketTreshold():
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
            self.buildResourceField('resource')
        elif buildType == 'building':
            self.buildBuilding(vid)
        elif buildType == 'both':
            print('Start min Resource Building')
            self.buildResourceField('resource')
            tempDelay = randint(3,7)
            print('sleeping for ' + str(tempDelay) + " seconds")
            time.sleep(tempDelay)
            self.buildBuilding(vid)
        elif buildType == '15c':
            print('Start min Resource Building')
            self.buildResourceField('15c')
            tempDelay = randint(3,7)
            print('sleeping for ' + str(tempDelay) + " seconds")
            time.sleep(tempDelay)
            self.buildBuilding(vid)
    def buildBuilding(self,vid):
        build=False
        for i in range( len(self.config['villages'][vid]['building']  )):
            bid = self.config['villages'][vid]['building'][i]
            if 'dorf2html' not in self.config['villages'][vid]:
                self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.currentVid))
            if self.getBuildingLvl(vid, bid)<self.config['villages'][vid]['buildinglvl'][i]:
                build=True
                break;
        if build:
            print('Start to build building '+ str(bid))
            #self.config['villages'][vid]['building']
            fieldId=int( bid)
            if fieldId > 0:
                self.buildField(fieldId)
    def getBuildingLvl(self, vid, bid):
        if bid <=18:
            html = self.config['villages'][vid]['dorf1html']
        else:
            html = self.config['villages'][vid]['dorf2html']
        return int(getRegexValue(html,'build\.php\?id='+str(bid)+'[^L]*Level (\d+)[^\d]'))
        
    def villagesSendResources(self):
        for vid in self.RequestedResources:
            print('Trying to send' + str(self.RequestedResources[vid]))
            self.currentVid=str(vid)
            availableResources=None
            try:
                availableResources = self.config['villages'][vid]['availableResources']
            except Exception as e:
                self.sendRequest(self.config['server']+'dorf2.php?newdid='+str(self.currentVid))
                availableResources = self.config['villages'][vid]['availableResources']
            if 'holdResources' in self.config['villages'][vid]:
                for i in range(4):
                    tmprs = availableResources[i]
                    availableResources[i]= availableResources[i]-self.config['villages'][vid]['holdResources'][i]+ randint(1,2000)-1000
                    if tmprs<availableResources[i]:
                        availableResources[i]=tmprs
                    if availableResources[i]<0:
                        availableResources[i]=0
            sendingSum = 0
            for i in range(4):
                if (availableResources[i]<self.RequestedResources[vid][i+1]):
                    self.RequestedResources[vid][i+1] = availableResources[i]-availableResources[i]%50
                sendingSum = sendingSum + self.RequestedResources[vid][i+1]
            print('Trying to send' + str(self.RequestedResources[vid]))
            if (sendingSum<self.getMinMarketTreshold()):
                continue
            to = str(self.RequestedResources[vid][0])
            r1 = str(self.RequestedResources[vid][1])
            r2 = str(self.RequestedResources[vid][2])
            r3 = str(self.RequestedResources[vid][3])
            r4 = str(self.RequestedResources[vid][4])
            temptime = self.RequestedResources[vid][5]

            doOnceInSeconds(temptime,self.sendResources,'sendResources['+self.currentVid+']->'+to,self.config['villages'][to]['x'],self.config['villages'][to]['y'],r1,r2,r3,r4,True)
        self.RequestedResources = {}

    def buildResourceField(self,type):
        if type == '15c':
            fieldId=self.buildFindMinFieldCrop()
            if fieldId:
                self.buildField(fieldId)

        if type == 'resource':
            fieldId=self.buildFindMinField()
            if fieldId:
                self.buildField(fieldId)


    def buildField(self, filedId):
        print('Start Building on Village '+ str(self.currentVid) +' field '+str(filedId))
        if filedId <=18:
            dorf=1
        else:
            dorf=2
        html=self.sendRequest(self.config['server']+'build.php?newdid='+str(self.currentVid)+'&id='+str(filedId))
        try:
            try:
                m=re.search('waiting loop',html)
                if m != None:
                    print('waiting loop detected!')
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

        self.sendRequest(self.config['server']+'dorf'+str(dorf)+'.php?a='+str(filedId)+'&c='+c+'&newdid='+str(self.currentVid))

    def buildFindMinField(self):
        data=self.config['villages'][self.currentVid]
        availableResources=data['availableResources']
        fieldsList=data['fieldsList']

        buildableFieldList={}
        buildableResourceTypes=[]
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] <10:
                buildableFieldList[i] = fieldsList[i];
                if fieldsList[i]['gid'] not in buildableResourceTypes:
                    buildableResourceTypes.append(fieldsList[i]['gid'])

        minAvailableResource=999999999999999
        desiredResourceType=999999999999999  #always less then 5
        for i in range(len(availableResources)):
            if i in buildableResourceTypes:
                if(availableResources[i]<minAvailableResource):
                    minAvailableResource=availableResources[i]
                    desiredResourceType=i
        if desiredResourceType > 4:
            return False
        if data['villageHasGreyField'] == True and data['stockBarFreeCrop']<10:
            desiredResourceType = 3 #crop
        desiredFieldLevel=999999999999
        desiredFieldIndex=99999999999

        for i in buildableFieldList:
            if buildableFieldList[i]['gid'] == desiredResourceType:
                if buildableFieldList[i]['level'] <desiredFieldLevel:
                    desiredFieldLevel = buildableFieldList[i]['level']
                    desiredFieldIndex = i

        if desiredFieldIndex < 18: #it always less then 18
            return desiredFieldIndex+1;
        return False;

    def getMinResourceFieldLevel(self, vid):
        data=self.config['villages'][self.currentVid]
        if 'fieldsList' not in data:
            return 30
        fieldsList=data['fieldsList']

        minResourceFieldLevel = 30
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] < minResourceFieldLevel:
                minResourceFieldLevel = fieldsList[i]['level']
        return minResourceFieldLevel

    def getGlobalMinResourceFieldLevel(self):
        globalMinResourceFieldLevel = 30
        for vid in self.config['villages']:
            if globalMinResourceFieldLevel > self.getMinResourceFieldLevel(vid):
                globalMinResourceFieldLevel = self.getMinResourceFieldLevel(vid)
        return globalMinResourceFieldLevel

    def getVillageCheckPeriod(self, vid):
        if  self.getMinResourceFieldLevel(vid) < 3:
            return 600
        return 1500

    def buildFindMinFieldCrop(self):
        data=self.config['villages'][self.currentVid]
        availableResources=data['availableResources']
        fieldsList=data['fieldsList']

        desiredResourceType = 3 # crop
        desiredFieldLevel = 999999999999
        desiredFieldIndex = 99999999999

        for i in fieldsList:
            if fieldsList[i]['gid'] == desiredResourceType:
                if fieldsList[i]['level'] < desiredFieldLevel:
                    desiredFieldLevel= fieldsList[i]['level']
                    desiredFieldIndex=i

        if desiredFieldIndex < 18: #it always less then 18
            return desiredFieldIndex+1;
        return False;

    def analysisBuild(self,html):
        data={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))

        data = mergeDict(data, getResourceData(html))

        return data

    def analysisDorf2(self,html):
        data={}
        if not html:
            return False
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))
        
        data = mergeDict(data, getResourceData(html))

        data['constructionFinishTimes'] = getConstructionFinishTimes(html)
        return data

    def analysisDorf1(self,html):
        data={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        fields = parser.find_all('div', {'class': 'labelLayer'})
        fieldsList = [field.find_parent('div')['class'] for field in fields]
        newFieldList={}
        data['villageHasGreyField'] = False
        for i in range(len(fieldsList)):
            isFieldGray = True
            for ii in fieldsList[i]:
                if (ii[0:4] == 'good'):
                    isFieldGray = False
                if (ii[0:6] == 'notNow'):
                    isFieldGray = False
            if isFieldGray == True:
                data['villageHasGreyField'] = True
            for ii in fieldsList[i]:
                if (ii[0:3] == 'gid'):
                    gid=ii.replace('gid','')
            for ii in fieldsList[i]:
                if (ii[0:5] == 'level'):
                    level = ii.replace('level','')
            newFieldList[i] = {'gid':int(gid)-1,'level':int(level)}
        data['fieldsList'] = newFieldList
        self.adventureExists = False
        productionCompile = re.compile('class="content">(\d+)<',re.S)
        prs = productionCompile.findall(html)
        if len(prs)>0:
            if int(prs[0])>0:
                self.adventureExists = True
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\.\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))

        data = mergeDict(data, getResourceData(html))

        data['constructionFinishTimes'] = getConstructionFinishTimes(html)
        return data

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
                            'w': '1440:900',
                            'login': login
                        }
        html=self.sendRequest( self.config['server'] + 'login.php', data)
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
        
        ajaxTokenCompile=re.compile('ajaxToken\s*=\s*\'(\w+)\'')
        ajaxToken = ajaxTokenCompile.findall( html)[0]
        self.config['villagesAmount']=villageAmount
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
        if 'newdid=' in url:
            vid = getRegexValue(url,'newdid=(\d+)')
            data = {}
            if 'dorf1.php' in url:
                data = self.analysisDorf1(html.text)
                self.config['villages'][vid]['dorf1html']=html.text
            if 'dorf2.php' in url:
                data = self.analysisDorf2(html.text)
                self.config['villages'][vid]['dorf2html']=html.text
            if 'build.php' in url:
                data = self.analysisBuild(html.text)
            self.config['villages'][vid] = mergeDict(self.config['villages'][vid], data)         

        return html.text

travian();
