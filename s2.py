        element_viewport =self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            """, element)
        element_intreactable=self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                var x = rect.left + rect.width / 2;
                var y = rect.top + rect.height / 2;
                var elementAtPoint = document.elementFromPoint(x, y);
                return arguments[0].contains(elementAtPoint) || arguments[0] === elementAtPoint;
            """, element)
