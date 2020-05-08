import React, { Component } from 'react';
import { Redirect } from 'react-router';

import Embed from './Embed';

import "./report.css";
import API from "@aws-amplify/api";

interface ReportProps {
  isAuthenticated: boolean;
}

interface ReportState {
  redirect: boolean;
}

export default class Report extends Component<ReportProps, ReportState> {
  constructor(props: ReportProps) {
    super(props);

    this.state = {
      redirect: false,
    };
  }

  render() {
    if (this.state.redirect) return <Redirect to='/' />
    return (
      <div className="Reports">
        <Embed />
      </div>
    );
  }
}