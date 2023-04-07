

//Create React App
const { createReactApp } = require('react-scripts');

//Create a folder for your React app
const fs = require('fs');
const folderName = 'my-react-app';
fs.mkdirSync(folderName);

//Create your React app
createReactApp(folderName);

//Install dependencies
const { exec } = require('child_process');
exec('cd my-react-app && npm install', (err, stdout, stderr) => {
    if (err) {
        console.error(err);
        return;
    }
    console.log(stdout);
});

//Start your React app
exec('cd my-react-app && npm start', (err, stdout, stderr) => {
    if (err) {
        console.error(err);
        return;
    }
    console.log(stdout);
});