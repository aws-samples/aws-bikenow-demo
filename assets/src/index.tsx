import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router } from "react-router-dom";
import './index.css';
import App from './App';
import registerServiceWorker from './registerServiceWorker';
import Amplify from "@aws-amplify/core";
import config from "./config";

import 'bootstrap/dist/css/bootstrap.css';

Amplify.configure({
  Auth: {
    mandatorySignIn: true,
    region: config.cognito.REGION,
    userPoolId: config.cognito.USER_POOL_ID,
    identityPoolId: config.cognito.IDENTITY_POOL_ID,
    userPoolWebClientId: config.cognito.APP_CLIENT_ID
  },
  API: {
    endpoints: [
      {
        name: "bikenow",
        endpoint: config.bikenowApi.API_URL,
        region: config.bikenowApi.REGION
      },
      {
        name: "aimlApi",
        endpoint: config.aimlApi.API_URL,
        region: config.aimlApi.REGION
      }
    ]
  }
});

ReactDOM.render(
  <Router>
    <App />
  </Router>,
  document.getElementById('root')
);
registerServiceWorker();
