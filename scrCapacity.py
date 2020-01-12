#Import libraries
import scrDefine
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time
import pymongo
from datetime import datetime

# Initialize ChromeDriver
# Load web page for selected country
def _funcLoadWebPage(country_id):
    driver = webdriver.Chrome()
    link_url = scrDefine.URL_POWER + scrDefine.COUNTRIES[country_id] + scrDefine.URL_CAPACITY
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

# proceed selection action to show only necessary item
def _funcSelectOnlyRequiredCheckbox(driver, i):
    divTableLabels = driver.find_elements_by_xpath("//*[@class='mv-widget mv-header-table']")[1]
    tdLabels = divTableLabels.find_elements_by_tag_name('td')

    # deselect all except desired columns
    for lbIdx in range(0, len(tdLabels)):
        if lbIdx is not i:
            tdLabels[lbIdx].click()
            time.sleep(1)

# click on a certain column in chart
def _funcClickOnChart(driver, i):
    divChart = driver.find_elements_by_xpath("//*[@class='mv-widget mv-chart-panel']")[1]
    divPane = divChart.find_element_by_class_name('mv-pane-surface')
    arrRects = divPane.find_elements_by_xpath("//*[local-name()='svg']//*[local-name()='g']//*[local-name()='rect']")

    nCntEqualStyles = 0
    for rect in arrRects:
        try:
            style = rect.get_attribute('style')
            if style == scrDefine.LBSTYLES[i]:
                if nCntEqualStyles > 0:
                    actions = ActionChains(driver)
                    actions.move_to_element(rect)
                    actions.click(rect)
                    actions.perform()
                    break
                nCntEqualStyles = nCntEqualStyles + 1
        except:
            pass

# wait until data get loaded
def _funcWaitUntilDataGetLoaded(driver):
    divUnit = driver.find_element_by_id('unittable')
    while True:
        divClass = divUnit.get_attribute('class')
        if divClass != 'loaded':
            time.sleep(1)
        else:
            break

# parse data
def _funcParseFuelData(driver, i):
    divUnit = driver.find_element_by_id('unittable')
    tBody = divUnit.find_element_by_tag_name('tbody')
    arrRecords = tBody.find_elements_by_tag_name('tr')

    parseResult = []

    mycol = _funcGetConectionToMongoDB(i)

    for k in range(1, len(arrRecords)):
        record = arrRecords[k]
        arrColumns = record.find_elements_by_tag_name('td')

        parseOneRec = {}
        parseOneRec['Company']  = arrColumns[0].text
        parseOneRec['Facility'] = arrColumns[1].text
        parseOneRec['Unit']     = arrColumns[2].text
        parseOneRec['Installed Capacity (MW)'] = arrColumns[3].text

        # json_data = json.dumps(parseOneRec)
        # parseResult.append(json_data)
        parseResult.append(parseOneRec)

    # save records to mongodb
    # print results to file
    if len(parseResult) > 0:
        for line in parseResult:
            mycol.insert_one(line)
        print("Scraping of Page " + scrDefine.LABELS[i] + " has completed.")
    parseResult.clear()

# get connection to appropriate database
def _funcGetConectionToMongoDB(i):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[scrDefine.CAP_DBNAMES[i]]

    now = datetime.now()
    colName = "DB" + now.strftime("%Y-%m-%d-%H-%M-%S")
    mycol = mydb[colName]

    return mycol

# main function
if __name__ == '__main__':
    # load page
    webdriver = _funcLoadWebPage(0)

    # hide license agree dialog
    _funcHideAgreeTermsDialog(webdriver)

    for i in range(0, len(scrDefine.LABELS)):
        # select only required checkbox to select column from chart
        _funcSelectOnlyRequiredCheckbox(webdriver, i)
        time.sleep(1)

        # click on chart
        _funcClickOnChart(webdriver, i)
        time.sleep(1)

        # waits until data get loaded
        _funcWaitUntilDataGetLoaded(webdriver)
        time.sleep(1)

        # parse current data
        _funcParseFuelData(webdriver, i)
        time.sleep(1)

        # Click on chart again to refresh chart status
        _funcClickOnChart(webdriver, i)

        time.sleep(2)

    # print result
    print ("Operation has completed")

    # driver close
    webdriver.close()