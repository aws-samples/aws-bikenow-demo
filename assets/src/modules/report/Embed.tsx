import React from 'react';
import { Spinner } from "react-bootstrap";
import API from '@aws-amplify/api';
import Auth from '@aws-amplify/auth';

import QuickSightEmbedding from 'amazon-quicksight-embedding-sdk';
//import QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

const Embed = (_) => {
    
  let jwtToken : string;
  let payloadSub : any;
  let email : any;
  
  Auth.currentSession()
    .then(data => { 
      jwtToken = data.getIdToken().getJwtToken(); 
      payloadSub = data.getIdToken().payload.sub;
      email = data.getIdToken().payload.email;
    } )
    .catch(err => console.log(err));
  
  async function loadDashboard(e : any) {
    const myInit = { 
        headers: {},
        response: true,
        queryStringParameters: { 
            jwtToken: jwtToken,
            payloadSub: payloadSub,
            email: email
        }
    }
    const data = await API.get('bikenow', '/report', myInit);

    const containerDiv = document.getElementById("dashboardContainer");
    //let dashboard;
    const options = {
        url: data.data.data.EmbedUrl,
        container: containerDiv,
        parameters: {
            country: "United States"
        },
        scrolling: "no",
        height: "AutoFit",
        loadingHeight: "480px",
        width: "100%"
    };
    if (containerDiv) {
      containerDiv.innerHTML = "";
    }
    const dashboard = QuickSightEmbedding.embedDashboard(options);
  }

  window.addEventListener('load', loadDashboard);

  return (
    <>
      <div id="dashboardContainer"><Spinner animation="border" className="center-spinner" /></div>
    </>
  );
}

export default Embed;