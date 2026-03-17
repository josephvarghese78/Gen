def che(e):
    element_viewport = c.driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                """, e)





    element_intreactable = c.driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            var x = rect.left + rect.width / 2;
            var y = rect.top + rect.height / 2;
            var elementAtPoint = document.elementFromPoint(x, y);
            return arguments[0].contains(elementAtPoint) || arguments[0] === elementAtPoint;
        """, e)






    element_b = c.driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            var x = rect.left + rect.width / 2;
            var y = rect.top + rect.height / 2;
            var elementAtPoint = document.elementFromPoint(x, y);
            if (arguments[0].contains(elementAtPoint) || arguments[0] === elementAtPoint)
                return null
            else
                return elementAtPoint;
        """, e)
