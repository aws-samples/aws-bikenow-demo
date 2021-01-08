import Auth from "@aws-amplify/auth";
import React, { Component } from "react";
import { withRouter } from "react-router-dom";
import { Form, Nav, Navbar, Button } from "react-bootstrap";
import "./App.css";
import { Routes } from "./Routes";

interface AppProps {
  history: any;
}

interface AppState {
  isAuthenticated: boolean;
  isAuthenticating: boolean;
}

class App extends Component<AppProps, AppState> {
  constructor(props: AppProps) {
    super(props);

    this.state = {
      isAuthenticated: false,
      isAuthenticating: true
    };

    document.title = "AWS BikeNow Demo"
  }

  async componentDidMount() {
    try {
      if (await Auth.currentSession()) {
        this.userHasAuthenticated(true);
      }
    }
    catch (e) {
      if (e !== 'No current user') {
        alert(e);
      }
    }

    this.setState({ isAuthenticating: false });
  }

  userHasAuthenticated = (authenticated: boolean) => {
    this.setState({ isAuthenticated: authenticated });
  }

  handleLogout = async () => {
    await Auth.signOut();

    this.userHasAuthenticated(false);
    this.props.history.push("/login");
  }

  showLoggedInBar = () => (
    <Form inline>
      <Button variant="outline-light" href="/rides" className="mr-sm-2 uniform-width">Rides</Button>
      <Button variant="outline-light" href="/reviews" className="mr-sm-2 uniform-width">Reviews</Button>
      <Button variant="outline-light" href="/report" className="mr-sm-2 uniform-width">Report</Button>
      <Button variant="outline-light" onClick={this.handleLogout} className="uniform-width">Log out</Button>
    </Form>
  );

  showLoggedOutBar = () => (
    <Form inline>
      <Button variant="outline-light" href="/signup" className="mr-sm-2 uniform-width">Sign up</Button>
      <Button variant="outline-light" href="/login" className="uniform-width">Login</Button>
    </Form>
  );

  render() {
    const childProps = {
      isAuthenticated: this.state.isAuthenticated,
      userHasAuthenticated: this.userHasAuthenticated
    };

    return (
      !this.state.isAuthenticating &&
      <div className="App container">
        <Navbar navbar-light="true" className="mb-3 navbar">
          <Navbar.Brand href="/">AWS BikeNow Demo</Navbar.Brand>
          <Navbar.Toggle />
          <Navbar.Collapse>
            <Nav className="ml-auto">
              {this.state.isAuthenticated ? this.showLoggedInBar() : this.showLoggedOutBar()}
            </Nav>
          </Navbar.Collapse>
        </Navbar>
        <Routes isAuthenticated={childProps.isAuthenticated} userHasAuthenticated={childProps.userHasAuthenticated} />
      </div>
    );
  }
}

export default withRouter(App as any);