import sys
from mc.webtab.WebTab import WebTab
from mc.app.MainApplication import MainApplication
from acom.test.tcbase import assertEqual, assertNotEqual

class Test(object):
    def __init__(self):
        MainApplication.setTestModeEnabled(True)
        self.app = MainApplication(sys.argv)

    def parentChildTabsTest(self):
        tab1 = WebTab()
        tab2 = WebTab()
        tab3 = WebTab()
        tab4 = WebTab()
        tab5 = WebTab()
        tab6 = WebTab()

        tab1.addChildTab(tab2)
        assertEqual(tab1.childTabs(), [tab2, ])
        assertEqual(tab2.parentTab(), tab1)
        assertEqual(tab2.childTabs(), [])

        tab1.addChildTab(tab3)
        assertEqual(tab1.childTabs(), [tab2, tab3])
        assertEqual(tab3.parentTab(), tab1)
        assertEqual(tab3.childTabs(), [])

        tab1.addChildTab(tab4, 1)
        assertEqual(tab1.childTabs(), [tab2, tab4, tab3])
        assertEqual(tab4.parentTab(), tab1)
        assertEqual(tab4.childTabs(), [])

        tab4.addChildTab(tab5)
        tab4.addChildTab(tab6)

        tab4.attach(self.app.getWindow())
        tab4.detach()

    def work(self):
        self.parentChildTabsTest()

def main():
    Test().work()

if __name__ == '__main__':
    main()
