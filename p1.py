def getAttributes(e):
   obj={}
   try:
      if e is None:
            return None
      attributes = c.driver.execute_script("""
            var items = {}; 
            for (index = 0; index < arguments[0].attributes.length; ++index) {
                 items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value
            }; 
            return items;
       """, e)
      t=e.get_attribute("value")
      if t is not None:
         obj['text'] =t
      t=e.get_attribute('innerText')
      if t is not None:
         obj['innertext'] = t
      obj['tag'] = e.tag_name
      obj['attrs'] = attributes
      #print("attributes extracted:", obj)
      return obj
   except Exception as ex:
      print(f"Exception in getAttributes: {ex}")
      return None


def compare_element(ee, ae):
    try:
        comp=False
        for key in ee.keys():
            if key=="tag":
                comp=str(ee.get('tag', '')).lower()==str(ae.get('tag','')).lower()
                if not comp:
                    return comp
            else:
                comp=str(ee.get(key, '')).lower()==str(ae['attrs'].get(key,'')).lower()
                if not comp:
                    return comp
        return comp
    except:
        return False

brk=False
index=-1
path=""
element_p={
    "tag": "svg",
    "id": "icons",
    "xmlns": "http://www.w3.org/2000/svg1",
    "viewBox" : "0 0 60 55"
}

elements=c.driver.find_elements(By.ID, "dislike-icon")
"""
if index is not None:
    element = c.driver.find_elements(By.ID, "dislike-icon")[index]
    if len(path)>0:
        elements=element.find_elements(By.XPATH, path)
""


for e in elements:
    children=e.find_elements(By.XPATH, ".//*")
    for ce in children:
        obj_p=getAttributes(ce)
        res=compare_element(element_p, obj_p)
        print(res)
        if res:
            brk=True
            ce.click()
            break
    if brk:
        break

time.sleep(60)

#/html/body/div/div[3]/div[1]/svg