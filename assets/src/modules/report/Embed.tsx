import React from 'react';
import { Spinner } from "react-bootstrap";
import API from '@aws-amplify/api';
import Auth from '@aws-amplify/auth';

var QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

const Embed = ({}) => {
    
  var jwtToken : string;
  var payloadSub : any;
  var email : any;
  
  Auth.currentSession()
    .then(data => { 
      jwtToken = data.getIdToken().getJwtToken(); 
      payloadSub = data.getIdToken().payload.sub;
      email = data.getIdToken().payload.email;
    } )
    .catch(err => console.log(err));
  
  async function loadDashboard(e : any) {
    let myInit = { 
        headers: {},
        response: true,
        queryStringParameters: { 
            jwtToken: jwtToken,
            payloadSub: payloadSub,
            email: email
        }
    }
    const data = await API.get('bikenow', '/report', myInit);

    var containerDiv = document.getElementById("dashboardContainer");
    var dashboard;
    var options = {
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
    dashboard = QuickSightEmbedding.embedDashboard(options);
  }

  window.addEventListener('load', loadDashboard);

  return (
    <>
      <div id="dashboardContainer"><Spinner animation="border" className="center-spinner" /></div>
    </>
  );
}

export default Embed;