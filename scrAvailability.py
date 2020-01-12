#Import libraries
import scrDefine
from selenium import webdriver
import time
import pymongo
from datetime import datetime

# Initialize ChromeDriver
# Load web page for selected country
def _funcLoadWebPage(country_id):
    driver = webdriver.Chrome()
    link_url = scrDefine.URL_POWER + scrDefine.COUNTRIES[country_id] + scrDefine.URL_AVAILIVILITY
    driver.get(link_url)
    return driver

# Hide license agree dialog if it is shown
def _funcHideAgreeTermsDialog(driver):
    try:
        divParent = driver.find_element_by_id('et-askprivacy-container')
        divOverlay = divParent.find_element_by_id('et-askprivacy-overlay')
        divEnButtons = divOverlay.find_element_by_xpath(".//div[contains(@class,'et-actions')]")
        btnAgree = divEnButtons.find_elements_by_tag_name('a')[2]
        driver.execute_script('arguments[0].click();', btnAgree)
        time.sleep(1)
    except:
        pass

# change start date to 2010/1/1
def _funcChangeDateTo20100101(driver):
    divDates = driver.find_element_by_xpath(".//div[contains(@class,'input-daterange')]")
    inFromDate = divDates.find_elements_by_tag_name('input')[0]

    # change date
    inFromDate.click()
    time.sleep(1)

    # click on date
    divDay = driver.find_element_by_xpath(".//div[contains(@class,'datepicker-days')]")
    dayHead = divDay.find_elements_by_tag_name('thead')[0]
    dayTr = dayHead.find_elements_by_tag_name('tr')[1]
    dayTh = dayTr.find_elements_by_tag_name('th')[1]
    dayTh.click()
    time.sleep(1)

    # click on month
    divMonth = driver.find_element_by_xpath(".//div[contains(@class,'datepicker-months')]")
    monHead = divMonth.find_elements_by_tag_name('thead')[0]
    monTr = monHead.find_elements_by_tag_name('tr')[1]
    monTh = monTr.find_elements_by_tag_name('th')[1]
    monTh.click()
    time.sleep(1)

    # click on year, 2010
    divYear = driver.find_element_by_xpath(".//div[contains(@class,'datepicker-years')]")
    yearBody = divYear.find_elements_by_tag_name('tbody')[0]
    yearTd = yearBody.find_elements_by_tag_name('td')[0]
    yearSpan = yearTd.find_elements_by_tag_name('span')[1]
    yearSpan.click()
    time.sleep(1)

    # Select Jan, 1
    monthBody = divMonth.find_elements_by_tag_name('tbody')[0]
    monthTd = monthBody.find_elements_by_tag_name('td')[0]
    monthSpan = monthTd.find_elements_by_tag_name('span')[0]
    monthSpan.click()
    time.sleep(1)

    # Select Day 1
    dayBody = divDay.find_elements_by_tag_name('tbody')[0]
    dayTr = dayBody.find_elements_by_tag_name('tr')[0]
    dayTd = dayTr.find_elements_by_tag_name('td')[5]
    dayTd.click()
    time.sleep(1)

    # remove opened calendar
    divDates.click()
    time.sleep(1)

# Set filter date for Non-availivility report data
def _funcReloadNonAvailibilityDataFrom2010(driver):
    _funcChangeDateTo20100101(driver)

    # click on refresh button
    divButtons = driver.find_element_by_xpath(".//div[contains(@class,'frame-type-dce_dceuid15')]")
    btnRefresh = divButtons.find_elements_by_tag_name('button')[0];
    # driver.execute_script('arguments[0].click();', btnRefresh)
    btnRefresh.click()

    # wait for new data to be reloaded
    time.sleep(1)
    while 1:
        try:
            divProbAvailable = driver.find_element_by_xpath("//*[@class='frame frame-default frame-type-text frame-layout-0']")
            divLoaded = divProbAvailable.find_element_by_class_name('loaded')
            divTable = divLoaded.find_element_by_class_name('mv-widget')
            time.sleep(1)
            break
        except:
            time.sleep(3)

# parse table record click on next tab button
# loop, loop, loop are required.
def _funcParseNonAvailibiltyData(driver, i):
    parseResult = []
    LstPageNumbers = []

    mycol = _funcGetConectionToMongoDB(i)

    bIsMorePage = True
    while bIsMorePage:
        bIsMorePage = False
        divProbAvailable = driver.find_element_by_xpath("//*[@class='frame frame-default frame-type-text frame-layout-0']")
        divRecPages = divProbAvailable.find_element_by_xpath(".//div[contains(@class,'mv-record-pages')]")
        divBtnPages = divRecPages.find_elements_by_class_name('mv-button')

        curPageNumber = '0'
        for divPage in divBtnPages:
            if divPage.text not in LstPageNumbers:
                LstPageNumbers.append(divPage.text)
                curPageNumber = divPage.text

                bIsMorePage = True

                # change page number
                divPage.click()
                time.sleep(2)

                # parse it
                divRecord = divProbAvailable.find_element_by_class_name('mv-records-panel')
                arrDataBody = divRecord.find_elements_by_tag_name('tbody')[0]
                arrDataRows = arrDataBody.find_elements_by_tag_name('tr')

                for row in arrDataRows:
                    arrTdRecords = row.find_elements_by_tag_name('td')

                    cols = ['','','','','','','','','','','']
                    for i in range(len(arrTdRecords)):
                        if i == 0 or i == 8:
                            continue
                        if i == 1:
                            rec = arrTdRecords[1]
                            cols[0] = rec.find_elements_by_tag_name('div')[0].text
                            continue
                        rec = arrTdRecords[i]
                        if i < 8:
                            cols[i-1] = rec.text;
                        elif i > 8:
                            cols[i-2] = rec.text;

                    parseOneRec = {}
                    parseOneRec['Market Participant-Affected Asset-Affected Unit'] = cols[0]
                    parseOneRec['Bidding Zone'] = cols[1]
                    parseOneRec['Fuel Type'] = cols[2]
                    parseOneRec['Event Start'] = cols[3]
                    parseOneRec['Event Stop'] = cols[4]
                    parseOneRec['Unavailable Capacity(MW)'] = cols[5]
                    parseOneRec['Reason'] = cols[6]
                    parseOneRec['Message ID'] = cols[7]
                    parseOneRec['Publication date/time'] = cols[8]

                    # json_data = json.dumps(parseOneRec)
                    # parseResult.append(json_data)
                    parseResult.append(parseOneRec)

                # search for next page
                break

        # print results to file
        if len(parseResult) > 0:
            for line in parseResult:
                mycol.insert_one(line)
            print("Scraping of Page " + curPageNumber + " has completed.")
        parseResult.clear()
        parseResult = []

    print ("Operation Completed")

# get connection to appropriate database
def _funcGetConectionToMongoDB(i):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[scrDefine.AVAIL_DBNAMES[i]]

    now = datetime.now()
    colName = "DB" + now.strftime("%Y-%m-%d-%H-%M-%S")
    mycol = mydb[colName]

    return mycol

# main function
if __name__ == '__main__':
    # Print Description to use
    print ("0:Austria, 1:Belgium, 2:Czech Republic, 3:France, 4:Germany, 5:Great Britain, 6:Hungary, 7:Italy, 8:Netherlands, 9:Switzerland")
    n = input("Press appropriate number to select country...\n")

    # load page
    webdriver = _funcLoadWebPage( int(n))

    # hide license agree dialog
    _funcHideAgreeTermsDialog(webdriver)

    # reset filter date to 2010/1/1
    _funcReloadNonAvailibilityDataFrom2010(webdriver)

    # parse None Availability Data
    _funcParseNonAvailibiltyData(webdriver, int(n))

    # driver close
    webdriver.close()