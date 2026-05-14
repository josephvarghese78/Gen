import random
import threading
import time
import json
import copy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as chrome_options
from selenium.webdriver.edge.options import Options as edge_options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
import getpass
import datetime as dt
from datetime import datetime
import os
import config as cfg
import filemanager as fm
import selfheal as shealEngine
#from SelfHealEngine import self_heal as shealEngine



class webui:

    def __init__(self):
        self.driver = None
        self.driverOptions = None
        self.action = None
        self.browser_type = None
        self.browser_profile = []

        self.data_row = -1
        self.startnewbrowser = False
        self.iterations = True

        self.error_logs = []
        self.info_logs = []
        self.warning_logs = []
        self.status = []
        self.selfheal_flag=True
        self.next_step_name=""
        self.skip_step_flag=False
        self.sh = shealEngine.self_heal()


    def runtestcase(self, name, testcasedef, iterations, datarow_type):
        self.sh.thread_name=name
        self.iterations=iterations

        for iteration in range(1, int(iterations) + 1):
            step_fail_count = 0
            test_report = {}
            test_start_time = datetime.now()
            self.data_row = self.get_datarow(iteration, datarow_type)
            teststeps = testcasedef["steps"]
            #
            test_report["id"] = f"{name}_{iteration}"
            test_report["name"] =f"{name}; {testcasedef.get('name','no-name')}; {self.browser_type}; - {iteration}"
            test_report["author"] = testcasedef.get("author", getpass.getuser())
            test_report["suite"] = testcasedef.get("name", f"name_{iteration}")
            test_report["desc"] = testcasedef.get("desc", f"name_{iteration}")
            test_report["iteration"] = iteration
            test_report["browser"] = self.browser_type
            test_report["start"] = test_start_time.strftime("%Y-%m-%d %H:%M:%S")
            test_report["status"] = ""
            test_report["steps"] = []
            #
            for stepname in teststeps:
                print("*" * 50)
                print(stepname)

                test_report_steps = {}
                stepdef = cfg.steps_data[stepname]

                if self.next_step_name ==stepname and self.skip_step_flag:
                    self.skip_step_flag=False
                    self.next_step_name=""


                if not self.skip_step_flag:
                    if isinstance(stepdef, dict):
                        test_step_start_time = datetime.now()
                        test_report_steps["step_name"] = stepdef["description"]
                        test_report_steps["author"] = test_report["author"]
                        test_report_steps["status"] = ""
                        test_report_steps["start"] = test_step_start_time.strftime("%H:%M:%S")
                        status=self.runstep(name, stepname, iteration, stepdef)
                        test_step_end_time = datetime.now()  # .strftime("%Y-%m-%d %H:%M:%S")
                        diff_seconds = int((test_step_end_time - test_step_start_time).total_seconds())
                        formatted = str(dt.timedelta(seconds=diff_seconds)).rjust(8, "0").split(".")[0]
                        test_report_steps["end"] = test_step_end_time.strftime("%H:%M:%S")
                        test_report_steps["duration"] = formatted
                        test_report_steps["status"] = "PASS" if status else "FAIL"
                        step_fail_count += 0 if status else 1
                        test_report_steps["message"] = ""
                        test_report_steps["info"] = self.info_logs.copy()
                        test_report_steps["error"] = self.error_logs.copy()
                        test_report_steps["warning"] = self.warning_logs.copy()
                        test_report["steps"].append(test_report_steps)
                    elif isinstance(stepdef, list):
                        for steps in stepdef:
                            test_report_steps = {}
                            test_step_start_time = datetime.now()  # .strftime("%Y-%m-%d %H:%M:%S")
                            test_report_steps["step_name"] = steps["description"]
                            test_report_steps["author"] = test_report["author"]
                            test_report_steps["status"] = ""
                            test_report_steps["start"] = test_step_start_time.strftime("%H:%M:%S")
                            status, info_m, warning_m, error_m=self.runstep(name, stepname, iteration, steps)
                            test_step_end_time = datetime.now()  # .strftime("%Y-%m-%d %H:%M:%S")
                            diff_seconds = int((test_step_end_time - test_step_start_time).total_seconds())
                            formatted = str(dt.timedelta(seconds=diff_seconds)).rjust(8, "0").split(".")[0]
                            test_report_steps["end"] = test_step_end_time.strftime("%H:%M:%S")
                            test_report_steps["duration"] = formatted
                            test_report_steps["status"] = "PASS" if status else "FAIL"
                            step_fail_count += 0 if status else 1
                            test_report_steps["message"] = ""
                            test_report_steps["info"] = self.info_logs.copy()
                            test_report_steps["error"] = self.error_logs.copy()
                            test_report_steps["warning"] = self.warning_logs.copy()
                            test_report["steps"].append(test_report_steps)
                    else:
                        print("incorrect step def format")
                        test_step_start_time = datetime.now()#.strftime("%Y-%m-%d %H:%M:%S")
                        test_report_steps["step_name"] = stepdef["description"]
                        test_report_steps["author"] = test_report["author"]
                        test_report_steps["status"] = ""
                        test_report_steps["start"] = test_step_start_time.strftime("%H:%M:%S")
                        test_report_steps["end"] = test_report_steps["start"]
                        test_report_steps["duration"] = f"00:00:00"
                        test_report_steps["status"] = "FAIL"
                        test_report_steps["message"] ="incorrect step def format"
                        test_report_steps["error"] = [f"step is defined as {type(stepdef)}, only dist or list is valid"]
                        test_report_steps["warning"]=[]
                        test_report_steps["info"]=[]
                        print("incorrect step def format")
                        step_fail_count += 1
                        test_report["steps"].append(test_report_steps)
                else:
                    test_step_start_time = datetime.now()
                    test_report_steps["step_name"] = stepdef["description"]
                    test_report_steps["author"] = test_report["author"]
                    test_report_steps["status"] = ""
                    test_report_steps["start"] = test_step_start_time.strftime("%H:%M:%S")
                    #status = self.runstep(name, stepname, iteration, stepdef)
                    test_step_end_time = datetime.now()  # .strftime("%Y-%m-%d %H:%M:%S")
                    diff_seconds = int((test_step_end_time - test_step_start_time).total_seconds())
                    formatted = str(dt.timedelta(seconds=diff_seconds)).rjust(8, "0").split(".")[0]
                    test_report_steps["end"] = test_step_end_time.strftime("%H:%M:%S")
                    test_report_steps["duration"] = formatted
                    test_report_steps["status"] = "PASS"
                    test_report_steps["message"] = "step skipped."
                    test_report_steps["info"] = ["step skipped."]
                    test_report_steps["error"] = []
                    test_report_steps["warning"] = []
                    test_report["steps"].append(test_report_steps)

                print("*" * 50)
                print("")
                print("")

            test_report["status"]= "PASS" if step_fail_count==0 else "FAIL"
            test_end_time = datetime.now()
            diff_seconds = int((test_end_time - test_start_time).total_seconds())
            formatted = str(dt.timedelta(seconds=diff_seconds)).rjust(8, "0").split(".")[0]
            test_report["end"]=test_end_time.strftime("%Y-%m-%d %H:%M:%S")
            cfg.tc_duration+=diff_seconds
            test_report["duration"] = formatted
            cfg.final_test_report.append(test_report)


    def runstep(self, tname, stepname, iteration, stepdef):

        try:
            action = stepdef["action"]
            status=False
            self.error_logs = []
            self.info_logs = []
            self.warning_logs = []

            if action.lower() in ["loadpage", "openwebpage"]:
                if (iteration>1 and self.startnewbrowser) or (iteration==1):
                    status = self.openwebpage(self.browser_type, stepdef)
                elif iteration>1 and not self.startnewbrowser:
                    self.closebrowserflag=False
                    url = stepdef["params"].get("url", "about:blank")
                    status =self.goto_url(url)

            elif action.lower() in ["jump", "jumptostep"]:
                self.selfheal_flag=False
                self.next_step_name=self.jumptostep(stepdef)
                self.selfheal_flag=True

            elif action.lower() in ["settext", "setvalue"]:
                status = self.settext(stepdef)
            elif action.lower() in ["click"]:
                status = self.clickelement(stepdef)
            elif action.lower() in ["uploadfiles"]:
                status = self.uploadfiles(stepdef)
            elif action.lower() in ["smartwait"]:
                status = self.smartwait(stepdef)
            elif action.lower() in ["SwitchToWindow", "SwitchToWindow"]:
                status = self.switchtowindow(stepdef)
            elif action.lower() in ["closebrowser"]:
                status = self.closebrowser(iteration)
            else:
                print(tname, "action not found:", action)
                status=False
                self.error_logs.append(f"{action} not found")

            return status, self.info_logs, self.warning_logs, self.error_logs
        except Exception as e:
            print("Error", stepdef, e)
            self.error_logs.append(str(e))
            return False, self.info_logs, self.warning_logs, self.error_logs

    ####################################### SELENIUM ELEMENT FUNCTIONS ######################################
    def getelement_main(self, objName):
        obj = []
        obj_index = 0
        obj_element=None
        by = None
        value = None
        oldElement = {}
        oe_attrs=""
        ne_attrs=""

        oldElement = copy.deepcopy(self.getObjectDesc(objName))


        # print(oldElement)
        attrs_keys = oldElement.get('attrs', {}).keys()
        selelium_loc_found = any(k in attrs_keys for k in self.sh.selenium_keys)# true or false

        try:
            if selelium_loc_found:# when no selenium locator is found
                for key in oldElement['attrs'].keys():
                    try:
                        by = key
                        value = oldElement['attrs'].get(key)
                        e = []
                        print('By:', by, ' Value:', value)

                        if by.lower() == "id":
                            if "*" in value:
                                value = value.replace("*", "")
                                e = self.driver.find_elements(By.XPATH, f"//*[contains(@id,'{value}')]")
                            e = self.driver.find_elements(By.ID, value)
                        elif by.lower() == "name":
                            if "*" in value:
                                value = value.replace("*", "")
                                e = self.driver.find_elements(By.XPATH, f"//*[contains(@name,'{value}')]")
                            e = self.driver.find_elements(By.NAME, value)
                        elif by.lower() == "xpath":
                            e = self.driver.find_elements(By.XPATH, value)
                        elif by.lower() in ["tag_name", "tag"]:
                            e = self.driver.find_elements(By.TAG_NAME, value)
                        elif by.lower() =="type":
                            e = self.driver.find_elements(By.XPATH, f"//*[@type='{value}']")
                        elif by.lower() in ["class_name", "class"]:
                            if "*" in value:
                                value = value.replace("*", "")
                                e = self.driver.find_elements(By.XPATH, f"//*[contains(@class,'{value}')]")
                            e = self.driver.find_elements(By.XPATH, f"//*[@class='{value}']")
                        elif by.lower() == "css_selector":
                            e = self.driver.find_elements(By.CSS_SELECTOR, value)
                        elif by.lower() == "link_text":
                            if "*" in value:
                                value = value.replace("*", "")
                                e = self.driver.find_elements(By.XPATH, f"//a[contains(text(),'{value}')]")
                            e = self.driver.find_elements(By.LINK_TEXT, value)
                        elif by.lower() == "partial_link_text":
                            if "*" in value:
                                value = value.replace("*", "")
                                e = self.driver.find_elements(By.XPATH, f"//a[contains(text(),'{value}')]")
                            e = self.driver.find_elements(By.PARTIAL_LINK_TEXT, value)
                        elif by.lower() == "index":
                            obj_index = int(value)

                        print(len(e), " elements found in e ")
                        if len(e) > 0:
                            if obj == []:
                                obj = e
                            else:
                                #obj = list(set(obj) & set(e))
                                obj = [el for el in obj if el in e]

                        print(len(obj), " elements found in e ")


                    except:
                        print(f"error in finding element with {by}={value}")
                        pass

                obj_element =self.filter_element(oldElement, obj, obj_index)
                print("obj element")
                p2=self.sh.getAttributes(obj_element, self.driver)
                print(json.dumps(p2, indent=4))

                if obj_element:
                #if len(obj) > 0:#element found with original description

                    if cfg.UPDATE_OBJREPO_ON_NEW_DESC_FOUND:
                        attributes=self.update_or(obj_element, obj_index)

                        if cfg.or_data[objName] != attributes and attributes is not None and (
                                attributes['attrs'] != {} or attributes != {}):
                            print(f"Updating object repository for {objName}")

                            child_element = cfg.or_data[objName].get("child", {})
                            child_keys_exist = True if len(list(child_element.keys())) > 0 else False

                            if child_keys_exist:
                                attributes['child'] = child_element


                            # update the object repo file
                            cfg.or_data[objName] = attributes
                            self.info_logs.append(f"object repo update for '{objName}")

                            self.t_lock=threading.Lock()
                            with self.t_lock:
                                fm.saveor()


                    """
                    if index == -1:
                        index = len(obj) - 1
                        element = obj[-1]
                    elif len(obj) == 1:
                        element = obj[0]
                    elif len(obj) > 0 and index >= 0 and index < len(obj):
                        element = obj[index]
                    else:
                        element = obj[-1]
                    """

                    self.elementmanager(obj_element)
                    self.status.append(True)
                    return obj_element, False, "", ""


                elif len(obj)<=0 and self.selfheal_flag:# element not found with original description, try self healing
                    print(f"object not found {objName},  with description {oldElement}, self healing started")

                    #thread_lock=threading.Lock()

                    #with thread_lock:
                    score, element, attrs, scoreType = self.sh.selfHealEngine(oldElement, self.driver)

                    print(f"Self healing completed with score {score} and type {scoreType}")

                    if element is not None: #element found with self healing, update object repository with new description
                        if cfg.UPDATE_OBJREPO_ON_HEAL:

                            #get index of the element

                            attributes = self.update_or(element, None)
                            oldElement.pop("parent", None)
                            oldElement.pop("pre_sibling", None)
                            oldElement.pop("fol_sibling", None)
                            oe_attrs=json.dumps(oldElement, indent=4)
                            ne_attrs=json.dumps(attrs, indent=4)

                            print(f"Updating object repository for '{objName}'")

                            child_element = cfg.or_data[objName].get("child", {})
                            child_keys_exist = True if len(list(child_element.keys())) > 0 else False

                            if child_keys_exist:
                                attributes['child'] = child_element

                            # update the object repo file
                            cfg.or_data[objName] = attributes
                            self.info_logs.append(f"object self healed for '{objName}'")
                            self.info_logs.append("Before")
                            self.info_logs.append(oe_attrs)
                            self.info_logs.append("After")
                            self.info_logs.append(ne_attrs)

                            self.t_lock=threading.Lock()
                            with self.t_lock:
                                fm.saveor()


                        self.elementmanager(element)
                        self.status.append(True)
                        return element, True, oe_attrs, ne_attrs
                    else:
                        oldElement.pop("parent", None)
                        oldElement.pop("pre_sibling", None)
                        oldElement.pop("fol_sibling", None)
                        oe_attrs = json.dumps(oldElement, indent=4)
                        self.error_logs.append(f"object not found and cannot be healed '{objName}'")
                        self.error_logs.append("Before")
                        self.error_logs.append(oe_attrs)

                        return None, False, "", ""
                else: # selfheal is turned off
                    return None, False, "", ""
            else:# when no selenium locator is found
                element, self_heal_flag, oe_attrs, ne_attrs =self.searchelement(None, objName)
                if element is not None:
                    self.info_logs.append(f"object found using search '{objName}' no selenium locators found")
                    self.elementmanager(element)
                    return element, self_heal_flag, oe_attrs, ne_attrs
                else:
                    self.info_logs.append(f"object not found using search '{objName}' no selenium locators found")
                    return None, False, "", ""
        except Exception as e:
            self.error_logs.append(str(e))
            return None, False, "", ""

    def filter_element(self, oldElement, elements, index):
        valid_elements1 = []
        # Special handling for file input elements - they are always hidden by design
        is_file_input = any(elem.get_attribute('type') == 'file' for elem in elements)

        if is_file_input:
            # For file inputs, skip visibility check - they're inherently hidden
            valid_elements = [element for element in elements if element.is_enabled()]
        else:
            # Normal elements must be displayed and enabled
            valid_elements = [element for element in elements if element.is_displayed() and element.is_enabled()]
        for e in valid_elements:
            p=self.sh.getAttributes(e, self.driver)
            print(json.dumps(p, indent=4))


        if len(valid_elements) == 0:
            print("option-1")
            return None
        elif len(valid_elements) == 1:
            print("option-2")
            p1 = self.sh.getAttributes(valid_elements[0], self.driver)
            print(json.dumps(p1, indent=4))
            return valid_elements[0]
        else:
            print("option-3")
            for element in valid_elements:
                tmp_oldElement=copy.deepcopy(oldElement)
                #for k in ["parent","pre_sibling","fol_sibling","index"]:

                #remove top-level keys safely
                for key in ["parent", "pre_sibling", "fol_sibling", "child"]:
                    tmp_oldElement.pop(key, None)

                #remove index inside attrs safely
                tmp_oldElement.get("attrs", {}).pop("index", None)
                element_desc=self.sh.getAttributes(element, self.driver)
                if element_desc == tmp_oldElement:
                    valid_elements1.append(element)

            valid_elements=valid_elements1

            if len(valid_elements) == 1:
                print("option-4")
                return valid_elements[0]
            elif len(valid_elements)>1 and index >= 0 and index < len(valid_elements):
                print("option-5")

                print("Chosen element index:", index)
                print("Total elements:", len(valid_elements))

                return valid_elements[index]
            elif len(valid_elements)>1:
                print("option-6")
                return valid_elements[cfg.DEFAULT_OBJINDEX]
            else:
                print("option-7")
                return None

    def elementaccesstest(self, element):
        try:
            report=[]
            element_displayed = element.is_displayed()
            element_enabled = element.is_enabled()

            element_viewport =self.driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                """, element)

            element_bocking = self.driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    var x = rect.left + rect.width / 2;
                    var y = rect.top + rect.height / 2;
                    var elementAtPoint = document.elementFromPoint(x, y);
                    if (arguments[0].contains(elementAtPoint) || arguments[0] === elementAtPoint)
                        return null
                    else
                        return elementAtPoint;
                """, element)

            if not element_displayed:
                report.append(False)
                self.warning_logs.append("element not visible")

            if not element_enabled:
                report.append(False)
                self.warning_logs.append("element not clickable")

            if not element_viewport:
                report.append(False)
                self.warning_logs.append("not inside screen area")

            if element_bocking is not None:
                report.append(False)
                blocking_element_desc=self.sh.getAttributes(element_bocking, self.driver)
                self.warning_logs.append(f"element blocked by another element {blocking_element_desc}")


            return all(report)
        except Exception as e:
            self.error_logs.append(str(e))
            return False



    def getelement(self, objname):
        try:
            #return element, info, warning, error
            self_heal_flag=False
            element, self_heal_flag, oe_attrs, ne_attrs=self.getelement_main(objname)

            child_element = cfg.or_data[objname].get("child", {})
            child_keys_exist= True if len(list(child_element.get('child', {}).keys()))>0 else False

            if child_keys_exist and element is not None:
                child_element = self.searchelement(element, objname)
                self.elementmanager(child_element)
                self.elementaccesstest(child_element)
                return child_element
            elif not child_keys_exist and element is not None:
                self.elementaccesstest(element)
                return element
            else:
                self.error_logs.append(f"'{objname}' not found")
                return None
        except Exception as e:
            self.error_logs.append(str(e))
            return None



    def searchelement(self, p, objname):# search elements
        brk = False
        #p=self.driver if p is None else p
        search_child=False
        self_heal_flag=False
        oe_attrs=""
        ne_attrs=""

        try:
            if p is None:
                search_element = copy.deepcopy(self.getObjectDesc(objname))
                p=self.driver
                search_child=False
            else:
                search_element =  copy.deepcopy(self.getObjectDesc(objname).get("child", {}))
                search_child=True

            keys_exist = True if len(list(search_element.keys())) > 0 else False
            if keys_exist:
                score, element, attrs, scoreType = self.sh.selfHealEngine(search_element, p)
                search_element.pop("parent", None)
                search_element.pop("pre_sibling", None)
                search_element.pop("fol_sibling", None)
                self_heal_flag=False if attrs==search_element else True

                if element is not None:
                    if self_heal_flag:
                        oe_attrs = json.dumps(search_element, indent=4)
                        ne_attrs = json.dumps(attrs, indent=4)

                        if not search_child:
                            self.info_logs.append(f"'{objname} self healed")
                        else:
                            self.info_logs.append(f"'child of {objname} self healed")

                        self.info_logs.append(f"Before")
                        self.info_logs.append(oe_attrs)
                        self.info_logs.append(f"After")
                        self.info_logs.append(ne_attrs)

                    print(f"element found {objname} using searchelement")
                    if cfg.UPDATE_OBJREPO_ON_HEAL:
                        attributes = self.update_or(element, None)
                        print(f"Updating object repository {objname}  using searchelement")
                        if search_child:
                            cfg.or_data[objname]['child'] = attributes
                        else:
                            child_element=cfg.or_data[objname].get("child", {})
                            child_keys_exist = True if len(list(child_element.keys())) > 0 else False

                            if child_keys_exist:
                                attributes['child'] = child_element

                            cfg.or_data[objname] = attributes

                        # update the object repo file
                        t_lock = threading.Lock()
                        with t_lock:
                            fm.saveor()

                    return element, self_heal_flag, oe_attrs, ne_attrs
                else:
                    print(f"element not found {objname} using searchelement")
                    self.error_logs.append(f"element not found {objname} using searchelement")
                    return None, False, "", ""
            else:
                print(f"element does not contain key found {objname} using searchelement")
                self.error_logs.append(f"element does not contain key found {objname} using searchelement")
                return None, False, "", ""
        except Exception as e:
            print(f" error in searchelement {str(e)}")
            self.error_logs.append(str(e))
            return None, False, "", ""


    def elementmanager(self, webelement):
        #make sure element is visible
        try:
            WebDriverWait(self.driver, 20).until(ec.visibility_of(webelement))
        except:
            pass

        #make sure element is clickable
        try:
            WebDriverWait(self.driver, 20).until(ec.element_to_be_clickable(webelement))
        except:
            pass

        #move to element
        try:
            self.action.move_to_element(webelement)
        except:
            pass

        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", webelement)
        except:
            pass

        #highligh element
        try:
            org_style=webelement.get_attribute("style")
            for _ in range(cfg.ELEMENT_HIGHLIGHT_BLINK):
                self.driver.execute_script(f"arguments[0].style.border='{cfg.ELEMENT_HIGHLIGHT_SIZE}px solid blue'", webelement)
                time.sleep(.3)
                self.driver.execute_script("arguments[0].style.border='none'", webelement)
                self.driver.execute_script("arguments[0].setAttribute('style', arguments[1])", webelement, org_style)
                time.sleep(.3)
        except:
            #print("error in highlighting element")
            pass

    ####################################### DATA FUNCTIONS ######################################
    def getdatadict(self, dd):
        try:
            colname = dd.get("col", "")

            if self.data_row < 0 or self.data_row >= len(cfg.data_dict):
                self.data_row = random.randint(0, len(cfg.data_dict) - 1)

            if len(colname.strip()) > 0:
                return cfg.data_dict[self.data_row].get(colname, "")
            else:
                return ""
        except Exception as e:
            self.error_logs.append(str(e))

    def get_datarow(self, iteration, datarow_type):
        # types in random=*, sequential=iteration, specific=iteration
        if str(datarow_type).lower() in ['r', 'random', '*']:
            if not cfg.data_dict:
                return 0
            else:
                return random.randint(0, len(cfg.data_dict)-1)
        elif str(datarow_type).lower() in ['i', "iteration"]:
            return iteration-1
        else:
            try:
                return int(datarow_type)-1
            except:
                return random.randint(0, len(cfg.data_dict) - 1)

    ####################################### OR FUNCTIONS ######################################
    def update_or(self, element, obj_index):
        try:
            parent = element.find_element(By.XPATH, "..")
            parent_attributes = self.sh.getAttributes(parent, self.driver)
            # print('parent', parent_attributes)
        except:
            parent_attributes = None

        try:
            pre_sibling = element.find_element(By.XPATH, "preceding-sibling::*[1]")
            pre_sibling_attributes = self.sh.getAttributes(pre_sibling, self.driver)
            # print('pre_sibling', pre_sibling_attributes)
        except:
            pre_sibling_attributes = None

        try:
            fol_sibling = element.find_element(By.XPATH, "following-sibling::*[1]")
            fol_sibling_attributes = self.sh.getAttributes(fol_sibling, self.driver)
            # print('fol_sibling', fol_sibling_attributes)
        except:
            fol_sibling_attributes = None

        element_attributes = self.sh.getAttributes(element, self.driver)
        element_attributes['attrs']['index']=obj_index
        element_attributes['parent'] = parent_attributes
        element_attributes['pre_sibling'] = pre_sibling_attributes
        element_attributes['fol_sibling'] = fol_sibling_attributes

        return element_attributes

    def getObjectDesc(self, objName):
        try:
            #object = cfg.or_data[objName]
            object = cfg.or_data.get(objName, {})
            return object
        except Exception as e:
            self.error_logs.append(str(e))
            return None


####################################### STEP FUNCTIONS ######################################
    def openwebpage(self,  browser_type, stepdef):
        try:
            browser = browser_type
            if browser.lower() in ["chrome", "edge"]:
                browser_def = cfg.steps_data[browser]

                #browser = stepdef["params"].get("browser", "chrome")
                url = stepdef["params"].get("url", "about:blank")
                wait = int(stepdef["params"].get("wait", 5))
                browser_options = stepdef["params"].get("options", [])
                experimental_options = stepdef["params"].get("experimentalOptions", [])
                #driver_path = stepdef["params"].get("driverPath")

                driver_options_flag = False

                if browser.lower() == "chrome":
                    self.driverOptions = chrome_options()
                else:
                    self.driverOptions = edge_options()


                if browser_options is not None and browser_options != []:
                    driver_options_flag = True
                    for option in browser_options:
                        try:
                            self.driverOptions.add_argument(option)
                        except:
                            pass

                if experimental_options is not None and experimental_options != []:
                    if browser_options is None or browser_options == []:
                        driver_options_flag = True
                    for option in experimental_options:
                        try:
                            self.driverOptions.add_experimental_option(option['key'], option['value'])
                        except:
                            pass

                if browser.lower() == "chrome":
                    if driver_options_flag:
                        self.driver = webdriver.Chrome(options=self.driverOptions)
                    else:
                        self.driver = webdriver.Chrome()
                elif browser.lower() == "edge":
                    if driver_options_flag:
                        self.driver = webdriver.Edge(options=self.driverOptions)
                    else:
                        self.driver = webdriver.Edge()

                cfg.action = ActionChains(self.driver)
                self.driver.get(url)
                time.sleep(wait)
                return True
            else:
                self.error_logs.append(f"{browser_type} not supported")
        except Exception as e:
            self.error_logs.append(str(e))
            return False

    def goto_url(self, url):
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            self.error_logs.append(str(e))
            return False


    def closebrowser(self, iteration):
        try:
            if self.startnewbrowser or iteration==self.iterations:
                self.driver.quit()

            return True
        except Exception as e:
            self.error_logs.append(str(e))
            return False

    def uploadfiles(self, obj):
        try:
            # Extract all params from obj
            button_objectname = obj['params'].get("button_objectname", "Browse_your_files")
            file_input_objectname = obj['params'].get("file_input_objectname", "Input_Files")
            file_paths = obj['params'].get("file_paths", [])
            wait = int(obj.get("wait", 5))

            # Step 1: Get the file input element (retry if not found)
            file_input = None
            max_retries = 3
            for attempt in range(max_retries):
                file_input = self.getelement(file_input_objectname)
                if file_input is not None:
                    break
                print(f"File input not found, retry attempt {attempt + 1}/{max_retries}")
                time.sleep(1)

            if file_input is None:
                print(f"File input element '{file_input_objectname}' not found after {max_retries} attempts.")
                self.error_logs.append(f"File input element '{file_input_objectname}' not found")
                return False

            # Step 2: Convert file paths to absolute paths and validate
            valid_file_paths = []
            for file_path in file_paths:
                abs_path = os.path.abspath(file_path)
                if os.path.exists(abs_path):
                    valid_file_paths.append(abs_path)
                    print(f"File found: {abs_path}")
                else:
                    print(f"File not found: {abs_path}")
                    self.warning_logs.append(f"File not found: {abs_path}")

            if not valid_file_paths:
                print("No valid files found to upload")
                self.error_logs.append("No valid files found for upload")
                return False

            # Step 3: Send files - use newline separator (CORRECT)
            # For multiple files, use newline separator
            files_to_upload = "\n".join(valid_file_paths)
            file_input.send_keys(files_to_upload)
            print(f"Files sent to input: {valid_file_paths}")
            self.info_logs.append(f"Files uploaded: {valid_file_paths}")

            time.sleep(wait)
            return True

        except Exception as e:
            print(f"Error in uploadfiles: {str(e)}")
            self.error_logs.append(str(e))
            return False

    # switch to window
    def switchtowindow(self, obj):
        try:
            wait = int(obj.get("wait", 2))
            window_id = obj.get("windowid", None)
            window_name = str(obj.get("windowname", "")).lower()
            switched = False
            WebDriverWait(self.driver, wait).until(lambda d: len(d.window_handles) > 1)
            current_handle = self.driver.current_window_handle

            if len(self.driver.window_handles) > 1:
                if window_id:
                    if 0 <= int(window_id) < len(self.driver.window_handles):
                        self.driver.switch_to.window(self.driver.window_handles[window_id])
                        switched = True
                elif window_name:
                    for handle in self.driver.window_handles:
                        self.driver.switch_to.window(handle)
                        if window_name in self.driver.title.lower():
                            switched = True
                            break

                if not switched:
                    self.driver.switch_to.window(current_handle)

            return True
        except Exception as e:
            print('Error in switchTpParent', e)
            self.error_logs.append(str(e))
            return False

    # switch back to parent window
    def switchtoparent(self, obj):
        try:
            wait = int(obj.get("wait", 2))

            self.driver.switch_to.default_content()
            time.sleep(wait)

            return True
        except Exception as e:
            print('Error in switchTpParent', e)
            self.error_logs.append(str(e))
            return False

    # handle alert
    def selectalert(self, obj):
        try:
            accept_alert = obj['params']["acceptalert"]
            wait = int(obj.get("wait", 2))

            alert = self.driver.switch_to.alert

            if accept_alert:
                alert.accept()
            else:
                alert.dismiss()
            time.sleep(wait)

            return True
        except Exception as e:
            print('Error in selectAlert', e)
            self.error_logs.append(str(e))
            return False


    #select frame
    def selectframe(self, obj):
        try:
            frame=obj['params']["frame"]
            wait = int(obj.get("wait", 2))

            self.driver.switch_to.frame(frame)
            time.sleep(wait)
            return True
        except Exception as e:
            print('Error in selectFrame', e)
            self.error_logs.append(str(e))
            return False


    #select radio group
    def selectradiogroup(self, obj):
        try:
            webobject=obj['params']["objectname"]
            wait = int(obj.get("wait", 2))
            value = obj['params']["value"]
            repeat=int(obj.get("repeat", 1))

            webelement  = self.getelement(webobject)
            radio_buttons = self.driver.find_elements(By.NAME, webelement.get_attribute("name"))
            for rb in radio_buttons:
                if rb.get_attribute("value") == value:
                    rb.click()
                    break
            time.sleep(wait)
            return True
        except Exception as e:
            print('Error in selectRadioGroup', e)
            self.error_logs.append(str(e))
            return False

    #select radio
    def selectradiobutton(self, obj):
        try:
            webobject=obj['params']["objectname"]
            wait = int(obj.get("wait", 2))
            repeat=int(obj.get("repeat", 1))

            webelement  = self.getelement(webobject)
            webelement.click()
            time.sleep(wait)
            return True
        except Exception as e:
            print('Error in selectRadioButton', e)
            self.error_logs.append(str(e))
            return False


    #chgeck checkbox
    def checkcheckbox(self, obj):
        try:
            webobject=obj['params']["objectname"]
            check = obj['params']["value"]
            wait = int(obj.get("wait", 2))
            repeat=int(obj.get("repeat", 1))

            webelement  = self.getelement(webobject)
            is_checked = webelement.is_selected()
            if check and not is_checked:
                webelement.click()
            elif not check and is_checked:
                webelement.click()
            time.sleep(wait)
            return True
        except Exception as e:
            print('Error in checkCheckbox', e)
            self.error_logs.append(str(e))
            return False


    #select from dropdown
    def selectdropdown(self, obj):
        try:
            webobject=obj['params']["objectname"]
            selectby=obj['params']["selectby"]
            value = obj['params']["value"]
            wait = int(obj.get("wait", 2))
            repeat=int(obj.get("repeat", 1))

            webelement  = self.getelement(webobject)
            select = Select(webelement)

            for i in range(repeat):
                if selectby.lower()=="value":
                    select.select_by_value(value)
                elif selectby.lower()=="text":
                    select.select_by_visible_text(value)
                elif selectby.lower()=="index":
                    select.select_by_index(int(value))

            time.sleep(wait)
            return True
        except Exception as e:
            print('Error in selectDropdown', e)
            self.error_logs.append(str(e))
            return False


    #click
    def clickelement(self, obj):
        try:
            webobject=obj['params']["objectname"]
            wait = int(obj.get("wait", 2))
            repeat=int(obj.get("repeat", 1))
            webelement  = self.getelement(webobject)

            for i in range(repeat):
                webelement.click()
                time.sleep(wait)

            return True
        except Exception as e:
            print('Error in click', e)
            self.error_logs.append(str(e))
            return False

    # send keys
    def sendkeys(self, obj, keys):
        try:
            m = []
            for k in keys:
                if k in cfg.KEY_MAP.keys():
                    if k == 'ctrl' and cfg.osName == 'MAC':
                        k = "cmd"

                    m.append(cfg.KEY_MAP.get(k))
                else:
                    m.append(k)
            if m:
                obj.send_keys(*m)
            return True
        except Exception as e:
            self.error_logs.append(str(e))
            return False


    #set text
    def settext(self, obj):
        try:
            webobject=obj['params']["objectname"]
            text=obj['params'].get("value", "")

            if isinstance(text, dict):
                text=self.getdatadict(text)

            if isinstance(text, list):
                text=random.choice(text)

            keys=obj['params'].get("keys", [])
            wait = int(obj.get("wait", 2))
            repeat=int(obj.get("repeat", 1))

            webelement  = self.getelement(webobject)

            if len(keys)==0 and len(text.strip())==0:
                self.warning_logs.append(f"text/value/keys not given for '{webobject}'")


            for i in range(repeat):
                webelement.clear()
                if len(keys)>0:
                    self.sendkeys(webelement, keys)
                else:
                    webelement.send_keys(text)
                time.sleep(wait)

            return True
        except Exception as e:
            self.error_logs.append(str(e))
            return False

    def smartwait(self, o):
        try:
            obj = o['params']['objectname']
            exitwhenfound = o['params'].get('exitwhenfound', False)
            wait_timeout = int(o.get("wait", 60))  # Get wait time from step (default 60s)
            check_interval = 2  # Check every 2 seconds

            # Disable self-healing during wait to prevent false positives
            original_selfheal_flag = self.selfheal_flag
            self.selfheal_flag = False

            start_time = time.time()

            try:
                while True:
                    # Check if timeout exceeded
                    elapsed_time = time.time() - start_time
                    if elapsed_time > wait_timeout:
                        print(f"SmartWait timeout after {wait_timeout} seconds")
                        self.warning_logs.append(f"SmartWait timeout waiting for '{obj}' after {wait_timeout} seconds")
                        break

                    # Try to find element
                    element = self.getelement(obj)

                    if exitwhenfound:
                        if element:
                            print(f"Element '{obj}' found after {elapsed_time:.1f} seconds")
                            self.info_logs.append(f"SmartWait: '{obj}' found after {elapsed_time:.1f} seconds")
                            break
                    else:
                        if not element:
                            print(f"Element '{obj}' disappeared after {elapsed_time:.1f} seconds")
                            self.info_logs.append(f"SmartWait: '{obj}' disappeared after {elapsed_time:.1f} seconds")
                            break

                    # Wait before next check
                    time.sleep(check_interval)

            finally:
                # Always restore the original selfheal flag
                self.selfheal_flag = original_selfheal_flag

            return True
        except Exception as e:
            self.error_logs.append(str(e))
            return False


    def jumptostep(self, stepdef):
        try:
            objects = stepdef.get("objects", [])
            if len(objects) > 0:
                for obj in objects:
                    element, self_heal_flag, oe_attrs, ne_attrs = self.getelement_main(obj.get("objectname", ""))
                    if element:
                        return obj.get("stepname", "")
            return None
        except Exception as e:
            self.error_logs.append(str(e))
            return None


###################################### HELPER FUNCTIONS ######################################
    def takescreenshot(self, v):
        try:
            filename = v['params'].get('filename', 'screenshot')
            outputpath = v['params'].get('outputpath', './screenshots')

            # Normalize path
            outputpath = os.path.normpath(outputpath)
            print(outputpath)
            if not os.path.exists(outputpath):
                os.makedirs(outputpath)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(outputpath, f"{filename}_{timestamp}.png")

            print(f"Saving screenshot to: {filepath}")
            success = self.driver.save_screenshot(filepath)

            if success:
                print(f"Screenshot saved successfully at: {filepath}")
            else:
                print("Screenshot failed!")
                self.error_logs.append("unable to take screenshot")
        except Exception as e:
            self.error_logs.append(str(e))