import requests
from bs4 import BeautifulSoup
import re
import time
import json
import datetime
import traceback
import subprocess
import random
import numpy
import math
from random import randint
import os.path
from os import path
WAREHOUSECOEFF = 0.8
troopSpeed = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
def parseVillageCoordinates(html):
    data = {}
    temp = getRegexValue(html, 'newdid=(\\d+)[^\\d].{,20}class="active"((?!coordinateX).)*coordinateX">[^;]*;(\\d+)[^\\d][^<]*<((?!coordinateY).)*coordinateY">[^;]*;(\\d+)[^\\d][^<]*<')
    data['x'] = int(temp[2])
    data['y'] = int(temp[4])
    return data

def readDictionaryFromJson(filename):
    if not path.exists(filename):
        f = open(filename, "w")
        f.write("{}")
        f.close()
    with open(filename,'r+') as reportsFile:
        return json.load(reportsFile)

def saveDictionaryToJson(dict, filename):
    with open(filename, 'w') as file:
        json.dump(dict, file)

def parseConstructionFinishTimes(html):
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

def parseResourceData(html):
    productionCompile = re.compile('"l[1-4]":\\s(-?\\d*)')
    prs = productionCompile.findall(html)
    for i in range(len(prs)):
        prs[i] = int(prs[i])
    return {'production': prs[0:4], 'availableResources' : prs[4:8], 'capacity' : prs[8:12]}

def getRegexValues(stringFrom, regex):
    try:
        idbCompile=re.compile(regex,re.S)
        return idbCompile.findall(stringFrom)
    except:
        return None

def getRegexValue(stringFrom,regex):
    temp = getRegexValues(stringFrom, regex)
    if temp == None:
        return None
    else:
        return temp[0]
def getAdventureData(html):
    data = {}
    names = ["send","kid","from","a"]
    for name in names:
        data[name] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    return data
def getAttackData(html):
    data = {}
    names = ["timestamp","timestamp_checksum","b"]
    for name in names:
        data[name] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    return data

def getAttackData2(html):
    data = {}
    names = ["timestamp","timestamp_checksum","id","w","c","kid"]
    names.append('troops\\[0\\]\\[t1\\]')
    names.append('troops\\[0\\]\\[t2\\]')
    names.append('troops\\[0\\]\\[t3\\]')
    names.append('troops\\[0\\]\\[t4\\]')
    names.append('troops\\[0\\]\\[t5\\]')
    names.append('troops\\[0\\]\\[t6\\]')
    names.append('troops\\[0\\]\\[t7\\]')
    names.append('troops\\[0\\]\\[t8\\]')
    names.append('troops\\[0\\]\\[t9\\]')
    names.append('troops\\[0\\]\\[t10\\]')
    if 'troops[0][t11]' in html:
        names.append('troops\\[0\\]\\[t11\\]')
    names.append("currentDid")
    names.append("b")
    names.append("dname")
    names.append("x")
    names.append("y")
    for name in names:
        key = name.replace('\\','')
        data[key] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    return data

def getFirstMarketplaceData(html):
    data = {}
    names = ["id","t"]
    for name in names:
        data[name] = getRegexValue(html,'name="'+name+'"[^>]+value="([^"]*)"')
    data['cmd']='prepareMarketplace'
    data['x2']='1'
    data['ajaxToken']=getRegexValue(html,'return \'([a-z\\d]{32})\';')
    return data
def getSecondMarketplaceData(html):
    data = {}
    names = ["id","t","a","sz","kid","c"]
    for name in names:
        data[name] = getRegexValue(html,'name=\\\\"'+name+'\\\\"[^>]+value=\\\\"([^\\\\]*)\\\\"')
    data['cmd']='prepareMarketplace'
    data['x2']='1'
    return data
def getBattleLinks(html):
    temp = getRegexValues(html,'(berichte.php[^"]*t=\\d*&s=\\d*)"')
    for i in range(len(temp)):
        temp[i] = 	temp[i].replace("&amp;","&")
    return temp
def getNextBattlePage(html):
    exist = getRegexValue(html,'next page[^>]*>')
    if 'next disabled' in exist:
        return None
    pages = getRegexValues(html,'(berichte.php.t=\\d*&amp;page=\\d*)"')
    return pages[len(pages) - 2].replace("&amp;","&")
def getBattleId(url):
    return getRegexValue(url,'id=([^%]*)%')
def getVillageCoordinatesFromD(d):
    coords = {}
    coords['x'] = (d-1)%801 - 400
    coords['y'] = 400 - (int((d-1)/801))
    return coords
class travian(object):
    def __init__(self):
        self.RequestedResources = {}
        self.config={}
        self.getConfig(True) # shutdown if error
        self.proxies = dict(http='socks5://127.0.0.1:9050', https='socks5://127.0.0.1:9050')
        self.session = requests.Session()
        self.startingTimestamp = time.time()
        self.loggedIn=False
        self.doneTasks = readDictionaryFromJson('doOnceInSeconds.json')
        self.adventureExists = False
        self.login()
        while 1:
            self.getConfig(False) # don't shutdown if error
            try:
                if self.loggedIn==False:
                    self.login()

                self.readOffensiveReports()
                self.checkVillages()
                self.printProductionData()
            except Exception as e:
                print(traceback.format_exc())
                print('Waiting for internet connection (30 sec)')
                time.sleep(30)
                continue
            sleepDelay = self.getNextSleepDelay()
            print('Sleeping! Time= ' + str(datetime.datetime.time(datetime.datetime.now())) + ', Delay= ' + str(int(sleepDelay/60)) + ' min ' + str(int(sleepDelay%60)) + ' sec' )
            print('Press Ctrl+C if you do not want to wait!')
            try:
                time.sleep(sleepDelay)
            except KeyboardInterrupt:
                pass
            print('Woke up!')
            time.sleep(1)

    def doOnceInSeconds(self, delay, function, function_name, *args):
        if not function_name in self.doneTasks or self.doneTasks[function_name] < time.time():
            if function(*args) == True:
                self.doneTasks[function_name] = time.time() + delay
                saveDictionaryToJson(self.doneTasks, 'doOnceInSeconds.json')
            else:
                return False
        return True

    def readOffensiveReports(self):
        nextBattlePage = 'berichte.php?t=1'
        if 'reports' not in self.config:
            self.readReportsFile()
        while True:
            time.sleep(0.1*randint(10,30))
            html = self.sendRequest(self.config['server'] + nextBattlePage, {}, False)

            battles = getBattleLinks(html)

            foundExistingReport = False
            for battle in battles:
                if getBattleId(battle) in self.config['reports']:
                    foundExistingReport = True
                    break
                time.sleep(0.01*randint(10,50))
                self.readBattleReport(battle)
            if foundExistingReport:
                break

            nextBattlePage = getNextBattlePage(html)
            if nextBattlePage == None:
                break
        self.saveReportsFile()

    def readBattleReport(self, battle):

        html = self.sendRequest(self.config['server'] + battle, {}, False)
        report = {}

        report['type'] = int(getRegexValue(battle, 't=(\\d+)[^\\d]'))

        date = getRegexValue(html, '<div class="time">[^>]*>([^<]*)<')

        timestamp = int(time.mktime(datetime.datetime.strptime(date, "%d.%m.%y, %H:%M:%S").timetuple()))

        report['timestamp'] = timestamp

        troops = getRegexValues(html,'class="unit[^>]*>\\d+</td>')

        lastIndexes = []

        for i in range(len(troops)):
            if 'last' in troops[i]:
                lastIndexes.append(i+1)
        report['source'] = {}
        report['source']['sent'] = []
        report['source']['dead'] = []
        report['destination'] = {}
        report['destination']['sent'] = []
        report['destination']['dead'] = []

        for i in range(0, lastIndexes[0]):
            report['source']['sent'].append(int(getRegexValue(troops[i],'>(\\d+)<')))
        for i in range(lastIndexes[0], lastIndexes[1]):
            report['source']['dead'].append(int(getRegexValue(troops[i],'>(\\d+)<')))
        for i in range(lastIndexes[1], lastIndexes[2]):
            report['destination']['sent'].append(int(getRegexValue(troops[i],'>(\\d+)<')))
        for i in range(lastIndexes[2], lastIndexes[3]):
            report['destination']['dead'].append(int(getRegexValue(troops[i],'>(\\d+)<')))

        villages = getRegexValues(html,'karte.php.d=(\\d*)"')

        report['source'] = mergeDict(report['source'], getVillageCoordinatesFromD(int(villages[0])))
        report['destination'] = mergeDict(report['destination'], getVillageCoordinatesFromD(int(villages[1])))

        lost = getRegexValues(html,'resources_medium">[^&]*&#x202d;([^&]*)&')
        report['source']['lost'] = int(lost[0].replace(',',''))
        report['destination']['lost'] = int(lost[1].replace(',',''))


        stolen = getRegexValue(html,'title="carry" />&#x202d;&#x202d;(\\d*)&')
        report['stolen'] = int(stolen)
        capacity = getRegexValue(html,'title="carry" />&#x202d;&#x202d;\\d*&#x202c;/&#x202d;(\\d*)&')
        report['capacity'] = int(capacity)

        self.config['reports'][getBattleId(battle)] = report

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
                if self.getGlobalMinResourceFieldLevel()<7:
                    sleepDelay = randint(900,2700)
                else:
                    sleepDelay = randint(1500,4000)
        if isNightTime:
            sleepDelay = randint(9000,15000)
        constructionFinishTimes = self.getAllConstructionFinishTimes()
        constructionFinishTimes.sort()
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
                for finishTime in self.config['villages'][vid]['constructionFinishTimes']:
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
            production=None
            try:
                villageProduction = self.config['villages'][vid]['production']
            except Exception as e:
                self.sendRequest(self.config['server'] + 'dorf2.php?newdid=' + vid)
                villageProduction = self.config['villages'][vid]['production']
            print('Village: ' + vid + ' resource fields level sum - ' + str(self.resourceFieldLevelsSum(vid)))
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

    def holdSmallCelebration(self, vid):
        print('Hold Small Celebration village ' + vid)
        html = self.goToBuildingByName(vid, 'Town Hall','a=1&')
        return True

    def sendResources(self, vid, x, y, r1, r2, r3, r4, sendifNotEnough):
        html = self.goToBuildingByName(vid, 'Marketplace','t=5&')
        available = getRegexValue(html,'class="merchantsAvailable">&#x202d;(\\d+)')
        available = int(available)
        cancarry = getRegexValue(html,'can carry <b>(\\d+)<\\/b>')
        cancarry = int(cancarry)
        print('Available merchants:' + str(available))
        if sendifNotEnough==False and int(r1) + int(r2) + int(r3) + int(r4) > available*cancarry:
            return False
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
        print('Trying to send ' + vid + ' ('+str(r1)+','+str(r2)+','+str(r3)+','+str(r4)+') to ('+str(x)+'|'+str(y)+')')
        if int(r1)+int(r2)+int(r3)+int(r4)<self.getMinMarketTreshold():
            print('resource amount is too small')
            return False
        data = getFirstMarketplaceData(html)
        print('Sending resources from ' + vid + ' ('+str(r1)+','+str(r2)+','+str(r3)+','+str(r4)+') to ('+str(x)+'|'+str(y)+')')
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
            return False
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
            return False
        return True

    def goToBuildingByName(self, vid, name, linkdata):
        html=self.sendRequest(self.config['server']+'dorf2.php?newdid=' + vid)
        idb = getRegexValue(html,'build.php\\?id=(\\d+)\'" title="'+name)
        return self.sendRequest(self.config['server'] + 'build.php?' + linkdata + 'id=' + idb + '&newdid=' + vid)

    def autoAdventure(self):
        print('Starting adventure')
        html=self.sendRequest(self.config['server']+'hero.php?t=3')
        data=getAdventureData(html)
        for key in data:
            if data[key]==None:
                return False
        print(data)
        html=self.sendRequest(self.config['server']+'start_adventure.php',data)
        return True

    def checkVillages(self):
        for vid in self.config['villages']:
            checkPeriod = self.getVillageCheckPeriod(vid)
            self.doOnceInSeconds(checkPeriod, self.checkVillage, 'checkvill' + vid, vid)
        if self.adventureExists and 'autoAdventure' in self.config and self.config['autoAdventure'] == 'true':
            self.doOnceInSeconds(randint(3000,4200)*6,self.autoAdventure,'adventure')
        self.sendRequestedResources(vid)

    def checkVillage(self, vid):
        html=self.sendRequest(self.config['server'] + 'dorf1.php?newdid=' + vid + '&')
        data=self.config['villages'][vid]
        if 'autoFarming' in self.config['villages'][vid] and self.config['villages'][vid]['autoFarming'] == 'true':
            self.farm(vid)
        if ('smallCelebration' in self.config['villages'][vid]) and self.config['villages'][vid]['smallCelebration'] == 'true':
            self.doOnceInSeconds(randint(3000,4000), self.holdSmallCelebration, 'holdSmallCelebration' + vid, vid)
        if ('push' in self.config['villages'][vid]) and len(self.config['villages'][vid]['push']) == 2:
            pushCoordinates=self.config['villages'][vid]['push']
            pushResourcesAndPeriod=self.config['villages'][vid]['pushparams']

            availableResources=None
            try:
                availableResources=self.config['villages'][vid]['availableResources']
            except Exception as e:
                self.sendRequest(self.config['server'] + 'dorf2.php?newdid=' + vid)
                availableResources=self.config['villages'][vid]['availableResources']
            if ('holdResources' in self.config['villages'][vid]) and len(self.config['villages'][vid]['holdResources']) == 4:
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
            if (sendingSum >= self.getMinMarketTreshold()):
                self.doOnceInSeconds(pushResourcesAndPeriod[4], self.sendResources, 'push ' + vid, vid, pushCoordinates[0], pushCoordinates[1], str(pushResourcesAndPeriod[0]), str(pushResourcesAndPeriod[1]), str(pushResourcesAndPeriod[2]), str(pushResourcesAndPeriod[3]), True)
        if ('requestResourcesFrom' in self.config['villages'][vid]) and len(self.config['villages'][vid]['requestResourcesFrom']) > 0:
            availableResources=data['availableResources']
            
            capacity=data['capacity']
            send = [0,0,0,0]
            sendingSum = 0
            for i in range(4):
                if (capacity[i]*(WAREHOUSECOEFF-0.1)>availableResources[i]):
                    send[i] = capacity[i]*WAREHOUSECOEFF-availableResources[i]
                    send[i] = int(send[i])/len(self.config['villages'][vid]['requestResourcesFrom'])
                    send[i] = int(send[i]) - int(send[i])%100
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
        print('Village: ' + vid + ' build type:'+buildType)
        if buildType == '0':
            pass
        elif buildType == 'resource':
            print('Start min Resource Building')
            self.buildResourceField(vid, 'resource')
        elif buildType == 'building':
            self.buildBuilding(vid)
        elif buildType == 'both':
            print('Start min Resource Building')
            self.buildResourceField(vid, 'resource')
            tempDelay = randint(3,7)
            print('sleeping for ' + str(tempDelay) + " seconds")
            time.sleep(tempDelay)
            self.buildBuilding(vid)
        elif buildType == 'cropandbuilding':
            print('Start min Resource Building')
            self.buildResourceField(vid, 'cropandbuilding')
            tempDelay = randint(3,7)
            print('sleeping for ' + str(tempDelay) + " seconds")
            time.sleep(tempDelay)
            self.buildBuilding(vid)
        return True

    def travelTime(self, vid, farm):
        return math.sqrt((self.config['villages'][vid]['x']-farm['x'])**2 + (self.config['villages'][vid]['y']-farm['y'])**2)*2*3600/6

    def calculateFarmPeriods(self, vid, farms):

        for farm in farms:
            if (not 'period' in farm) or farm['period'] == -1:
                farm['period'] = self.travelTime(vid, farm)
        for reportKey in self.config['reports']:
            report = self.config['reports'][reportKey]

            if report['timestamp'] > time.time() - 20 * 3600: # 20 hours
                print(report)
                for farm in farms:
                    if farm['x'] == report['destination']['x'] and farm['y'] == report['destination']['y']:
                        if 'stolen' not in farm:
                            farm['stolen'] = 0
                            farm['capacity'] = 0
                            farm['attacksNumber'] = 0
                        farm['stolen'] += report['stolen']
                        farm['capacity'] += report['capacity']
                        farm['attacksNumber'] += 1
        
        avgCoefficient = 0
        numOfCoefficients = 0
        for farm in farms:
            if 'stolen' in farm:
                farm['coefficient'] = 0.0000000001 + farm['stolen'] / (self.travelTime(vid, farm) * farm['attacksNumber'])
                if farm['stolen']/farm['capacity'] > 0.9:
                    farm['coefficient'] *= 1.1
                farm['period'] /= farm['coefficient']
                avgCoefficient += farm['coefficient']
                numOfCoefficients += 1
        if numOfCoefficients > 0:
            avgCoefficient /= numOfCoefficients
        else:
            avgCoefficient = 1
        for farm in farms:
            if 'stolen' not in farm:
                farm['coefficient'] = avgCoefficient
                farm['period'] /= farm['coefficient']

        farms = sorted(farms, key = lambda i: i['period'])

        numberOfFarms = len(farms)
        while farms[numberOfFarms - 1]['period'] > 12*3600:
            numberOfFarms -= 1
            self.alignPeriod(vid, farms, numberOfFarms)
        for farm in farms:
            farm['period'] = int(farm['period'])
            del farm['coefficient']
        return True

    def alignPeriod(self, vid, farms, numberOfFarms):
        troopsNeeded = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(numberOfFarms):
            farm = farms[i]
            troopsNeeded = numpy.add(troopsNeeded, numpy.multiply(self.config['villages'][vid]['farmTroops'], self.travelTime(vid, farm) / farm['period']))
        troopsNeeded = troopsNeeded.tolist()

        periodAlign = 0
        for i in range(len(troopsNeeded)):
            if self.config['villages'][vid]['troopCapacity'][i] > 0:
                periodAlign = max(periodAlign, troopsNeeded[i]/self.config['villages'][vid]['troopCapacity'][i])

        for farm in farms:
            farm['period'] *= periodAlign

    def farm(self, vid):
        self.readFarmsFile(vid)
        self.doOnceInSeconds(3600 * 24, self.calculateFarmPeriods, 'calculateFarmPeriods' + vid, vid, self.config['villages'][vid]['farms'])
        for farm in self.config['villages'][vid]['farms']:
            if farm['period'] > 12 * 3600:
                continue
            attackData = {}
            attackData['vid'] = vid
            attackData['troops'] = self.config['villages'][vid]['farmTroops']
            attackData['x'] = farm['x']
            attackData['y'] = farm['y']
            attackData['type'] = 'raid'
            print('attack[' + vid + ']->(' + str(farm['x']) + '/' + str(farm['y']) + ')')
            print(farm['period'])
            if not self.doOnceInSeconds(farm['period'], self.attack, 'attack[' + vid + ']->(' + str(farm['x']) + '/' + str(farm['y']) + ')', attackData):
                if not self.doesHaveEnoughTroops(vid, attackData['troops']):
                    break
        self.saveFarmsFile(vid)

    def resourceFieldLevelsSum(self, vid):

        if 'fieldsList' not in self.config['villages'][vid]:
            self.sendRequest(self.config['server'] + 'dorf1.php?newdid=' + vid)

        data=self.config['villages'][vid]
        fieldsList=data['fieldsList']

        levelsSum = 0
        for i in range(len(fieldsList)):
            levelsSum = levelsSum + fieldsList[i]['level']
        return levelsSum

    def buildBuilding(self, vid):
        build=False
        for i in range( len(self.config['villages'][vid]['building']  )):
            buildingId = self.config['villages'][vid]['building'][i]
            self.sendRequest(self.config['server'] + 'dorf2.php?newdid=' + vid)
            targetLevel = self.config['villages'][vid]['buildinglvl'][i]
            if (buildingId==0 and self.resourceFieldLevelsSum(vid) < targetLevel) or (buildingId>0 and self.getBuildingLvl(vid, buildingId) < targetLevel):
                build=True
                break
        if build:
            if buildingId == 0:
                self.buildResourceField(vid, 'resource')
                return
            print('Start to build building ' + str(buildingId))
            if buildingId > 0:
                self.buildField(vid, buildingId)

    def getBuildingLvl(self, vid, buildingId):
        if buildingId <=18:
            html = self.config['villages'][vid]['dorf1html']
        else:
            html = self.config['villages'][vid]['dorf2html']
        if getRegexValue(html,'build\\.php\\?id='+str(buildingId)+'[^L]*Level (\\d+)[^\\d]') == None:
            print('There is no building on field ' + str(buildingId))
            return 30
        return int(getRegexValue(html,'build\\.php\\?id='+str(buildingId)+'[^L]*Level (\\d+)[^\\d]'))
        
    def sendRequestedResources(self, vid):
        for vid in self.RequestedResources:
            print('Trying to send' + str(self.RequestedResources[vid]))
            availableResources=None
            try:
                availableResources = self.config['villages'][vid]['availableResources']
            except Exception as e:
                self.sendRequest(self.config['server'] + 'dorf2.php?newdid=' + vid)
                availableResources = self.config['villages'][vid]['availableResources']
            if ('holdResources' in self.config['villages'][vid]) and len(self.config['villages'][vid]['holdResources']) == 4:
                for i in range(4):
                    tmprs = availableResources[i]
                    availableResources[i]= availableResources[i] - self.config['villages'][vid]['holdResources'][i] + randint(1,2000)-1000
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
            period = self.RequestedResources[vid][5]

            self.doOnceInSeconds(period, self.sendResources, 'sendResources[' + vid + ']->' + to, vid, self.config['villages'][to]['x'], self.config['villages'][to]['y'], r1, r2, r3, r4, True)
        self.RequestedResources = {}

    def buildResourceField(self, vid, type):
        if type == 'cropandbuilding':
            fieldId=self.buildFindMinFieldCrop(vid)
            if fieldId:
                self.buildField(vid, fieldId)

        if type == 'resource':
            fieldId=self.buildFindMinField(vid)
            if fieldId:
                self.buildField(vid, fieldId)


    def buildField(self, vid, filedId):
        print('Start Building on Village ' + vid + ' field ' + str(filedId))
        if filedId <= 18:
            dorf = 1
        else:
            dorf = 2
        html = self.sendRequest(self.config['server'] + 'build.php?newdid=' + vid + '&id=' + str(filedId))
        try:
            try:
                m=re.search('waiting loop', html)
                if m != None:
                    print('waiting loop detected!')
                    return False
            except:
                return False
            m = re.search('(?<=&amp;c=)(\\w+)', html)
        #maybe not enough resource.
        except:
            return False
        if m == None:
            return False
        c = m.group(0)

        self.sendRequest(self.config['server'] + 'dorf' + str(dorf) + '.php?a=' + str(filedId) + '&c=' + c + '&newdid=' + vid)

    def buildFindMinField(self, vid):
        data=self.config['villages'][vid]
        availableResources=data['availableResources']
        fieldsList=data['fieldsList']

        buildableFieldList={}
        buildableResourceTypes=[]
        for i in range(len(fieldsList)):
            if fieldsList[i]['level'] <10:
                buildableFieldList[i] = fieldsList[i]
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
            return desiredFieldIndex+1
        return False

    def getMinResourceFieldLevel(self, vid):
        data=self.config['villages'][vid]
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
        minConstructionFinishDelay = 1500
        if 'constructionFinishTimes' in self.config['villages'][vid]:
            for constructionFinishTime in self.config['villages'][vid]['constructionFinishTimes']:
                minConstructionFinishDelay = min(minConstructionFinishDelay, constructionFinishTime - time.time())
        if self.getMinResourceFieldLevel(vid) < 3:
            return min(600, minConstructionFinishDelay)
        if self.getMinResourceFieldLevel(vid) < 7:
            return min(900, minConstructionFinishDelay)
        return min(1500, minConstructionFinishDelay)

    def buildFindMinFieldCrop(self, vid):
        data=self.config['villages'][vid]
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
            return desiredFieldIndex+1
        return False

    def doesHaveEnoughTroops(self, vid, troopsToSend):
        for i in range(len(troopsToSend)):
            if troopsToSend[i] > self.config['villages'][vid]['availableTroops'][i]:
                return False
        return True

    # attackData = {'vid' : xxx, 'troops' : [xx, xx, xx, ...], 'sendHero'(optional) : True/False, 'villageName'(optional): '', 'x'(optional): xx, 'y'(optional): xx, 'type' : 'raid'/'normal'}
    def attack(self, attackData):

        html = self.sendRequest(self.config['server'] + 'build.php?tt=2&id=39', {}, False, attackData['vid'])

        if not self.doesHaveEnoughTroops(attackData['vid'], attackData['troops']):
            return False

        data = getAttackData(html)
        data['currentDid'] = attackData['vid']
        for i in [1, 4, 7, 9, 2, 5, 8, 10, 3, 6]:
            if (attackData['troops'][i - 1] > 0):
                data['troops[0][t' + str(i) + ']'] = str(attackData['troops'][i - 1])
            else:
                data['troops[0][t' + str(i) + ']'] = ''
        if 'troops[0][t11]' in html:
            if 'sendHero' in attackData and attackData['sendHero'] == True:
                data['troops[0][t11]'] = '1'
            else:
                data['troops[0][t11]'] = ''
        if 'villageName' in attackData:
            data['dname'] = attackData['villageName']
        else:
            data['dname'] = ''
        if 'x' in attackData:
            data['x'] = attackData['x']
        else:
            data['x'] = ''
        if 'y' in attackData:
            data['y'] = attackData['y']
        else:
            data['y'] = ''
        if attackData['type'] == 'raid':
            data['c'] = '4'
        else:
            data['c'] = '3' # normal
        data['s1'] = 'ok'
        html = self.sendRequest(self.config['server'] + 'build.php?gid=16&tt=2', data, False)
        time.sleep(0.1*randint(3, 6))
        if 'There is no village at these coordinates.' in html and 'farms' in self.config['villages'][attackData['vid']]:
            self.config['villages'][attackData['vid']]['farms'] = [farm for farm in self.config['villages'][attackData['vid']]['farms'] if attackData['x'] != farm['x'] or attackData['y'] != farm['y']]
            return False

        data = {}
        data['redeployHero'] = ''
        data = mergeDict(data, getAttackData2(html))
        data['a'] = getRegexValue(html,'value="([^"]*)" name="a" id="btn_ok"')
        for key in data:
            if data[key] == None:
                print(html)
                print('attacking failed')
                return False
        print('Attacking village (' + data['x'] + '|' + data['y'] + ')' + ' with troops ' + str(attackData['troops']))
        self.sendRequest(self.config['server'] + 'build.php?gid=16&tt=2', data, False)
        time.sleep(0.1*randint(3, 6))
        return True

    def analysisSendTroops(self, html):
        data = {}
        troops = getRegexValues(html, 'troops\\[0\\]\\[t\\d+\\]"[^<]*<[^>]*>&#x202d;([^&]*)&')
        troops = [int(troop) for troop in troops]
        data['availableTroops'] = troops
        return data

    def analysisBuild(self, html):
        data={}
        if not html:
            return False
        parser = BeautifulSoup(html, "html5lib")
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\\.\\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))

        data = mergeDict(data, parseResourceData(html))

        return data

    def analysisDorf2(self,html):
        data={}
        if not html:
            return False
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\\.\\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))
        
        data = mergeDict(data, parseResourceData(html))

        data = mergeDict(data, parseVillageCoordinates(html))

        data['constructionFinishTimes'] = parseConstructionFinishTimes(html)
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
        productionCompile = re.compile('class="content">(\\d+)<',re.S)
        prs = productionCompile.findall(html)
        if len(prs)>0:
            if int(prs[0])>0:
                self.adventureExists = True
        productionCompile=re.compile('stockBarFreeCrop" class="value">&#x202d;([\\.\\d]*)')
        prs = productionCompile.findall(html)
        for i in range(len(prs)):
            data['stockBarFreeCrop']=int(prs[i].replace(".",""))

        data = mergeDict(data, parseResourceData(html))

        data = mergeDict(data, parseVillageCoordinates(html))

        data['constructionFinishTimes'] = parseConstructionFinishTimes(html)
        return data

    def readFarmsFile(self, vid):
        self.config['villages'][vid]['farms'] = readDictionaryFromJson('farms_' + vid + '.json')['farms']

    def saveFarmsFile(self, vid):
        saveDictionaryToJson({'farms': self.config['villages'][vid]['farms']}, 'farms_' + vid + '.json')

    def readReportsFile(self):
        self.config['reports'] = readDictionaryFromJson('reports.json')

    def saveReportsFile(self):
        saveDictionaryToJson(self.config['reports'], 'reports.json')


    def getConfig(self, shutdownIfError):
        try:
            with open('config.json','r+') as configFile:
                tempconfig =json.load(configFile)
                configFile.close()
                self.updateConfig(tempconfig)
            if 'proxies' in self.config:
                self.proxies = dict()
                if 'http' in self.config['proxies']:
                    self.proxies['http'] = self.config['proxies']['http']
                if 'https' in self.config['proxies']:
                    self.proxies['https'] = self.config['proxies']['https']
        except Exception as e:
            if shutdownIfError:
                raise e

    def updateConfig(self, new1):
        for element1 in new1:
            if (not isinstance(new1[element1], dict)) or (element1 not in self.config):
                self.config[element1] = new1[element1]
            else:
                for element2 in new1[element1]:
                    if (not isinstance(new1[element1][element2], dict)) or (element2 not in self.config[element1]):
                        self.config[element1][element2] = new1[element1][element2]
                    else:
                        for element3 in new1[element1][element2]:
                            if (not isinstance(new1[element1][element2][element3], dict)) or (element3 not in self.config[element1][element2]):
                                self.config[element1][element2][element3] = new1[element1][element2][element3]
                            else:
                                for element4 in new1[element1][element2][element3]:
                                    self.config[element1][element2][element3][element4] = new1[element1][element2][element3][element4]

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
        
        ajaxTokenCompile=re.compile('ajaxToken\\s*=\\s*\'(\\w+)\'')
        ajaxToken = ajaxTokenCompile.findall( html)[0]
        self.config['villagesAmount']=villageAmount
        self.config['ajaxToken']=ajaxToken

    def sendRequest(self, url, data={}, delay=True, vid="-1"):
        if delay:
            time.sleep(randint(1,5))
        html = None
        try:
            if len(data) == 0:
                if 'proxies' in self.config:
                    html=self.session.get(url,headers = self.config['headers'], proxies=self.proxies)
                else:
                    html=self.session.get(url,headers=self.config['headers'])
            else:
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
                        time.sleep(randint(1,5))
        if 'newdid=' in url or vid != "-1":
            if vid == "-1":
                vid = getRegexValue(url,'newdid=(\\d+)')
            data = {}
            if 'dorf1.php' in url:
                data = self.analysisDorf1(html.text)
                self.config['villages'][vid]['dorf1html']=html.text
            if 'dorf2.php' in url:
                data = self.analysisDorf2(html.text)
                self.config['villages'][vid]['dorf2html']=html.text
            if 'build.php' in url:
                data = self.analysisBuild(html.text)
            if 'build.php?tt=2&id=39' in url:
                data = self.analysisSendTroops(html.text)
            self.config['villages'][vid] = mergeDict(self.config['villages'][vid], data)         

        return html.text

subprocess.check_output("git stash --all", shell=True)
ret = subprocess.check_output("git pull", shell=True)
subprocess.check_output("git stash pop", shell=True)
if str(ret)[2:21] != 'Already up to date.':
    print('A script is updated, please start again!')
    exit(1)
travian()
