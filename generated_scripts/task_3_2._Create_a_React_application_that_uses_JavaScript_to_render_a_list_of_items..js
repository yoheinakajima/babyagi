

//import React and ReactDOM 
import React from 'react';
import ReactDOM from 'react-dom';

//create a functional component 
const List = () => {
  //create an array of items
  const items = ["Apple", "Banana", "Cherry", "Date", "Eggplant"];
  //map through the array and return the list of items 
  const listItems = items.map(item => <li>{item}</li>);
  //return the list items
  return listItems;
};

//render the List component in the DOM
ReactDOM.render(<List />, document.getElementById("root"));