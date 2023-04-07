
from react import Component

class ItemList(Component):
    def __init__(self, items):
        self.items = items
    
    def render(self):
        return (
            <ul>
                {
                    [
                        <li>{item}</li>
                        for item in self.items
                    ]
                }
            </ul>
        )
      
# Usage example
items = ["Apples", "Oranges", "Bananas"]
list = ItemList(items)