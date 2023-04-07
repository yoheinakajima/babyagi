

const items = [];

function addItem(item) {
  items.push(item);
}

function removeItem(item) {
  items.splice(items.indexOf(item), 1);
}

function listItems() {
  console.log(items);
}