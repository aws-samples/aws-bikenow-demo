import React from "react";
import { Redirect } from 'react-router';
import { Table, Spinner } from "react-bootstrap";

import "./rides.css";
import API from "@aws-amplify/api";

interface RidesProps {
  isAuthenticated: boolean;
}

interface RidesState {
  isLoading: boolean,
  redirect: boolean,
  rides: Ride[],
}

interface Ride {
  id: number;
  userId: string;
  stationId: number;
  stationName: string;
  duration: number;
  price: number;
  createdDate: Date;
}

export default class Rides extends React.Component<RidesProps, RidesState> {
  constructor(props: RidesProps) {
    super(props);

    this.state = {
      isLoading: true,
      redirect: false,
      rides: [],
    };
  }

  async componentDidMount() {
    if (!this.props.isAuthenticated) {
      return;
    }

    try {
      const rides = await this.rides();
      this.setState({ rides });
    } catch(e) {
      alert(e);
    }

    this.setState({ isLoading: false });
  }

  rides() {
    return API.get("bikenow", "/rides", null);
  }

  renderRidesList(rides: Ride[]) {
    const ridesList: Ride[] = [];

    return ridesList.concat(rides).map(
      (ride, i) =>
        <tr key={ride.id}>
          <td>{ride.stationName}</td>
          <td>{ride.duration} hours</td>
          <td>${ride.price.toFixed(2)}</td>
          <td>{new Date(ride.createdDate).toLocaleDateString()}</td>
        </tr>
    );
  }

  render() {
    if (this.state.redirect) return <Redirect to='/' />

    return (
      <div className="Rides">
        <h1 className="text-center">Ride History</h1>
          <Table variant="dark">
            <thead>
              <tr>
                <th>Station Name</th>
                <th>Duration</th>
                <th>Cost</th>
                <th>Ride Date</th>
              </tr>
            </thead>
            <tbody>
              {
                this.state.isLoading ?
                (
                  <tr>
                    <td>
                      <Spinner animation="border" className="center-spinner" />
                    </td>
                  </tr>
                ) :
                this.renderRidesList(this.state.rides)
              }
            </tbody>
          </Table>
          {
            !this.state.isLoading && (!this.state.rides || this.state.rides.length === 0) ?               
              <div className="text-center">You do not have any ride history. <a href="/" className="empty-text">Find a bike station</a> to start your first ride!</div>
              : ""
          }
      </div>
    );
  }
}