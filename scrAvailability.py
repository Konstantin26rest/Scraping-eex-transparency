#Import libraries
from selenium import webdriver
import time
import scrDefine
import json
import csv

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
            divProbAvailable = driver.find_element_by_id('Production Availability')
            divLoaded = divProbAvailable.find_element_by_class_name('loaded')
            divTable = divLoaded.find_element_by_class_name('mv-widget')
            time.sleep(1)
            break
        except:
            time.sleep(3)

# parse table record click on next tab button
# loop, loop, loop are required.
def _funcParseNonAvailibiltyData(driver):
    parseResult = []
    LstPageNumbers = []

    bIsMorePage = True

    while bIsMorePage:
        bIsMorePage = False
        divTable = driver.find_element_by_id('c2220')
        divRecPages = divTable.find_element_by_xpath(".//div[contains(@class,'mv-record-pages')]")
        divBtnPages = divRecPages.find_elements_by_tag_name('div')

        for divPage in divBtnPages:
            try:
                svgElement = divPage.find_elements_by_tag_name('svg')[0]
                continue
            except:
                pass

            if divPage.text not in LstPageNumbers:
                LstPageNumbers.append(divPage.text)
                bIsMorePage = True

                # change page number
                divPage.click()
                time.sleep(2)

                # parse it
                divRecord = divTable.find_element_by_class_name('mv-records-panel')
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

                    json_data = json.dumps(parseOneRec)
                    parseResult.append(json_data)

                # search for next page
                break

    # print results to file
    if len(parseResult) > 0:
        with open('D:/result.csv', 'wt') as csvfile:
            for line in parseResult:
                csvfile.write(line)
                csvfile.write("\n")
            print ("Operation Completed")

# main function
if __name__ == '__main__':
    # load page
    webdriver = _funcLoadWebPage(0)

    # hide license agree dialog
    _funcHideAgreeTermsDialog(webdriver)

    # reset filter date to 2010/1/1
    _funcReloadNonAvailibilityDataFrom2010(webdriver)

    # parse None Availibility Data
    _funcParseNonAvailibiltyData(webdriver)

    # sleep
    time.sleep(60000)

    # driver close
    webdriver.close()