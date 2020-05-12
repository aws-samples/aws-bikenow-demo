var express = require('express')
var bodyParser = require('body-parser')
var awsServerlessExpressMiddleware = require('aws-serverless-express/middleware')

var AWS = require('aws-sdk');
var AmazonCognitoIdentity = require('amazon-cognito-identity-js');
const https = require('https');

// declare a new express app
var app = express()
app.use(bodyParser.json())
app.use(awsServerlessExpressMiddleware.eventContext())

// Enable CORS for all methods
app.use(function (req, res, next) {
  res.header("Access-Control-Allow-Origin", "*")
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
  next()
});

var ROLE_ARN = process.env.ROLE_ARN;
var IDENTITY_POOL_ID = process.env.IDENTITY_POOL_ID;
var USER_POOL_ID = process.env.USER_POOL_ID;
var ACCOUNT_ID = process.env.ACCOUNT_ID;
var DASHBOARD_ID = process.env.DASHBOARD_ID;
var REGION = process.env.REGION;

app.get('/report', function (req, res) {

  var roleArn = ROLE_ARN; 
  var cognitoUrl = 'cognito-idp.' + REGION + '.amazonaws.com/' + USER_POOL_ID;

  AWS.config.region = REGION;

  var sessionName = req.query.payloadSub;
  var cognitoIdentity = new AWS.CognitoIdentity();
  var stsClient = new AWS.STS();
  var params = {
    IdentityPoolId: IDENTITY_POOL_ID, 
    Logins: {
      [cognitoUrl]: req.query.jwtToken
    }
  };

  cognitoIdentity.getId(params, function (err, data) {
    if (err) {
      console.log(err, err.stack);
      }
    else {
      data.Logins = {
        [cognitoUrl]: req.query.jwtToken
      };

      cognitoIdentity.getOpenIdToken(data, function (err, openIdToken) {
        if (err) {
          console.log(err, err.stack);
          res.json({
            err
          })
        } 
        else {
          let stsParams = {
            RoleSessionName: sessionName,
            WebIdentityToken: openIdToken.Token,
            RoleArn: roleArn
          }
          stsClient.assumeRoleWithWebIdentity(stsParams, function (err, data) {
            if (err) {
              console.log(err, err.stack);
              res.json({
                err
              })
            } 
            else {
              AWS.config.update({
                region: REGION,
                credentials: {
                  accessKeyId: data.Credentials.AccessKeyId,
                  secretAccessKey: data.Credentials.SecretAccessKey,
                  sessionToken: data.Credentials.SessionToken,
                  expiration: data.Credentials.Expiration
                }
              });
              var registerUserParams = {
                AwsAccountId: ACCOUNT_ID,
                Email: req.query.email,
                IdentityType: 'IAM',
                Namespace: 'default',
                UserRole: 'READER',
                IamArn: roleArn,
                SessionName: sessionName
              };
              var qsClient = new AWS.QuickSight();
              qsClient.registerUser(registerUserParams, function (err, data) {
                if (err) {
                  console.log(err, err.stack); 
                  if (err.code && err.code === 'ResourceExistsException') {
                    var getDashboardParams = {
                      AwsAccountId: ACCOUNT_ID,
                      DashboardId: DASHBOARD_ID,
                      IdentityType: 'IAM',
                      ResetDisabled: false, 
                      SessionLifetimeInMinutes: 100,
                      UndoRedoDisabled: false 
                    };

                    qsClient.getDashboardEmbedUrl(getDashboardParams, function (err, data) {
                      if (err) {
                        console.log(err, err.stack); 
                        res.json({
                          err
                        })
                      } 
                      else {
                        console.log(data);
                        res.json({
                          data
                        })
                      }
                    });
                  } 
                  else {
                    res.json({
                      err
                    })
                  }
                } 
                else {
                  setTimeout(function () {
                    var getDashboardParams = {
                      AwsAccountId: ACCOUNT_ID,
                      DashboardId: DASHBOARD_ID,
                      IdentityType: 'IAM',
                      ResetDisabled: false,
                      SessionLifetimeInMinutes: 100,
                      UndoRedoDisabled: false
                    };

                    qsClient.getDashboardEmbedUrl(getDashboardParams, function (err, data) {
                      if (err) {
                        console.log(err, err.stack);
                        res.json({
                          err
                        })
                      } else {
                        console.log(data);
                        res.json({
                          data
                        })
                      }
                    });

                  }, 2000);

                }
              });

            }
          });
        }
      });
    }
  });

});

app.listen(3000, function() {
  console.log("App started")
});

// Export the app object. When executing the application local this does nothing. However,
// to port it to AWS Lambda we will create a wrapper around that will load the app from
// this file
module.exports = app
