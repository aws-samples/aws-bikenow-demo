import React from "react";
import { Redirect } from 'react-router';
import { Table, Spinner } from "react-bootstrap";

import "./reviews.css";
import API from "@aws-amplify/api";

interface ReviewsProps {
  isAuthenticated: boolean;
}

interface ReviewsState {
  isLoading: boolean,
  redirect: boolean,
  reviews: Review[],
}

interface Review {
  userId: string;
  stationId: number;
  stationName: string;
  review: string;
  createdDate: Date;
}

export default class Reviews extends React.Component<ReviewsProps, ReviewsState> {
  constructor(props: ReviewsProps) {
    super(props);

    this.state = {
      isLoading: true,
      redirect: false,
      reviews: [],
    };
  }

  async componentDidMount() {
    if (!this.props.isAuthenticated) {
      return;
    }

    try {
      const result = await this.reviews();
      let reviews: Review[] = []
      for (let i = 0; i < result.length; i++) {
        let element = result[i];

        let review : Review = {
          userId: element.user_id,
          stationId: element.station_id,
          stationName: element.station_name,
          review: element.review,
          createdDate: new Date(element.create_date)
        };
        reviews.push(review);
      }      
      this.setState({ reviews: reviews.reverse() });
    } catch(e) {
      alert(e);
    }

    this.setState({ isLoading: false });
  }

  reviews() {
    return API.get("bikenow", "/reviews", null);
  }

  renderReviewsList(reviews: Review[]) {
    let reviewsList: Review[] = [];

    return reviewsList.concat(reviews).map(
      (review, i) =>
        <tr key={i}>
          <td>{review.stationName}</td>
          <td>{review.review}</td>
          <td>{new Date(review.createdDate).toLocaleDateString()}</td>
        </tr>
    );
  }

  render() {
    if (this.state.redirect) return <Redirect to='/' />

    return (
      <div className="Reviews">
        <h1 className="text-center">Review History</h1>
          <Table variant="dark">
            <thead>
              <tr>
                <th>Station Name</th>
                <th>Review</th>
                <th>Date</th>
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
                this.renderReviewsList(this.state.reviews)
              }
            </tbody>
          </Table>
          {
            !this.state.isLoading && (!this.state.reviews || this.state.reviews.length === 0) ?               
              <div className="text-center">You have not made any reviews. <a href="/" className="empty-text">Find a bike station</a> to write your first review!</div>
              : ""
          }
      </div>
    );
  }
}