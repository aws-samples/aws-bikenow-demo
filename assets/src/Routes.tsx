import React from "react";
import { Route, Switch } from "react-router-dom";
import PropsRoute from "./common/PropsRoute";
import Home from "./modules/signup/Home";
import Login from "./modules/signup/Login";
import Signup from "./modules/signup/Signup";
import Rides from "./modules/signup/Rides";
import Reviews from "./modules/signup/Reviews";
import Report from "./modules/report/Report";
import NotFound from "./modules/notFound/NotFound";

interface RouteProps {
  isAuthenticated: boolean;
  userHasAuthenticated: (authenticated: boolean) => void;
}

export const Routes: React.SFC<RouteProps> = (childProps) =>
  <Switch>
    <PropsRoute path="/" exact component={Home} props={childProps} />
    <PropsRoute path="/login" exact component={Login} props={childProps} />
    <PropsRoute path="/signup" exact component={Signup} props={childProps} />
    <PropsRoute path="/rides" exact component={Rides} props={childProps} />
    <PropsRoute path="/reviews" exact component={Reviews} props={childProps} />
    <PropsRoute path="/report" exact component={Report} props={childProps} />
    <Route component={NotFound} />
  </Switch>;