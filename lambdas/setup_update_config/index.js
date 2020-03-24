'use strict'; const https = require('https'); const url = require('url');
var AWS = require('aws-sdk'),
  codecommit = new AWS.CodeCommit();

exports.handler = function (event, context, callback) {
  console.log('Received event:', JSON.stringify(event, null, 2));
  if (event.RequestType === 'Create') {
    getBranchInfo().then(function (data) {
      var parentCommitId = data.branch.commitId;
      updateConfigFile(parentCommitId).then(function (data) {
        sendResponse(event, callback, context.logStreamName, 'SUCCESS');
      }).catch(function (err) {
        var responseData = { Error: 'Updating config file failed ' + err };
        sendResponse(event, callback, context.logStreamName, 'FAILED', responseData);
      });
    }).catch(function (err) {
      var responseData = { Error: 'Updating config file failed ' + err };
      sendResponse(event, callback, context.logStreamName, 'FAILED', responseData);
    });
  } else {
    sendResponse(event, callback, context.logStreamName, 'SUCCESS');
  }
};

function getConfigFile() {
  return `export default {
  MAX_ATTACHMENT_SIZE: 5000000,
  bikenowApi: {
    REGION: "${process.env.REGION}",
    API_URL: "${process.env.DB_API_URL}",
  },
  aimlApi: {
    REGION: "${process.env.REGION}",
    API_URL: "${process.env.ML_API_URL}"
  },
  cognito: {
    REGION: "${process.env.REGION}",
    USER_POOL_ID: "${process.env.USER_POOL_ID}",
    APP_CLIENT_ID: "${process.env.APP_CLIENT_ID}",
    IDENTITY_POOL_ID: "${process.env.IDENTITY_POOL_ID}"
  }
};`
}

function updateConfigFile(parentCommitId) {
  var params = {
    branchName: process.env.BRANCH_NAME,
    fileContent: new Buffer(getConfigFile()),
    filePath: 'src/config.js',
    repositoryName: process.env.REPOSITORY_NAME,
    commitMessage: 'Updating config.js with backend variables',
    fileMode: "NORMAL",
    name: 'UploadConfigLambda',
    parentCommitId: parentCommitId
  };
  return codecommit.putFile(params).promise();
}

function getBranchInfo() {
  var params = {
    branchName: process.env.BRANCH_NAME,
    repositoryName: process.env.REPOSITORY_NAME
  };
  return codecommit.getBranch(params).promise();
}

function sendResponse(event, callback, logStreamName, responseStatus, responseData) {
  const responseBody = JSON.stringify({
    Status: responseStatus,
    Reason: `See the details in CloudWatch Log Stream: ${logStreamName}`,
    PhysicalResourceId: logStreamName,
    StackId: event.StackId,
    RequestId: event.RequestId,
    LogicalResourceId: event.LogicalResourceId,
    Data: responseData,
  });

  console.log('RESPONSE BODY:\n', responseBody);

  const parsedUrl = url.parse(event.ResponseURL);
  const options = {
    hostname: parsedUrl.hostname,
    port: 443,
    path: parsedUrl.path,
    method: 'PUT',
    headers: {
      'Content-Type': '',
      'Content-Length': responseBody.length,
    },
  };

  const req = https.request(options, (res) => {
    console.log('STATUS:', res.statusCode);
    console.log('HEADERS:', JSON.stringify(res.headers));
    callback(null, 'Successfully sent stack response!');
  });

  req.on('error', (err) => {
    console.log('sendResponse Error:\n', err);
    callback(err);
  });

  req.write(responseBody);
  req.end();
}
