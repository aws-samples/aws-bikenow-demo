import React, { Component } from "react";
import { Accordion, Card, Button, Table, Spinner, FormLabel, FormControl, Modal, Form, Col } from "react-bootstrap";
import API from "@aws-amplify/api";
import { Redirect } from "react-router-dom";
import { Map, TileLayer, CircleMarker, Popup } from "react-leaflet";
import DatePicker from "react-datepicker";

import bikenowImage from "../../images/bikenow-demo.png";
import "./home.css";
import "react-datepicker/dist/react-datepicker.css";
import { stat } from "fs";

interface HomeProps {
  isAuthenticated: boolean;
}

interface HomeState {
  isLoading: boolean;
  redirect: string;
  bikeStations: BikeStation[];
  ride: Ride;
  searchInput: string;
  predictInput: Date;
  isSearchOpen: boolean;
  showRideModal: boolean;
  showReviewModal: boolean;
  isUpdating: boolean;
  review: Review;
  reviews: Review[];
}

interface BikeStation {
  stationId: number;
  name: string;
  lon: number;
  lat: number;
  numOfBikes: number;
  capacity: number;
  lastReported: number;
}

interface Ride {
  stationId: number;
  stationName: string;
  duration: number;
  price: number;
}

interface Review {
  userId: string;
  stationId: number;
  stationName: string;
  review: string;
  createdDate: Date;
}

export default class Home extends Component<HomeProps, HomeState> {
  constructor(props: HomeProps) {
    super(props);

    this.state = {
      isLoading: false,
      redirect: '',
      bikeStations: [],
      searchInput: '',
      predictInput: new Date(),
      isSearchOpen: false,
      showRideModal: false,
      showReviewModal: false,
      isUpdating: false,
      ride: { stationId: 0, stationName: '', duration: 0, price: 0 },
      review: { userId: '', stationId: 0, stationName: '', review: '', createdDate: new Date() },
      reviews: []
    };
  }

  onCreate = () => {
    this.setState({ redirect: '' });
  }

  async componentDidMount() {
    if (!this.props.isAuthenticated) {
      return;
    }

    try {
      this.bindBikeStationsToMap();
    } catch (e) {
      alert(e);
    }

    this.setState({ isLoading: false });
  }

  bikeStations(query_string='*') {
    let myInit = {
      queryStringParameters: {
        q: query_string
      }
    }
    return API.get('bikenow', '/stations/', myInit);
  }

  predictions() {
    let year = this.state.predictInput.getFullYear();
    let month = this.state.predictInput.getMonth() + 1;
    let day = this.state.predictInput.getDate();
    let hour = this.state.predictInput.getHours();
    let stationIds = this.state.bikeStations.map(o => o.stationId);

    let query = {
      year: year,
      month: month,
      day: day,
      hour: hour,
      station_ids: stationIds
    }

    return API.post('aimlApi', '/plan/', { body: query });
  }

  reviews(stationId: number) {
    let myInit = {
      queryStringParameters: {
        stationId: stationId,
      }
    };
    return API.get('bikenow', '/reviews/', myInit);      
  }

  async bindBikeStationsToMap(query_string='*') {
    let result = await this.bikeStations(query_string);

    let stationList: BikeStation[] = [];

    for (let i = 0; i < result.hits.hits.length; i++) {
      let item = result.hits.hits[i]._source;

      let new_station: BikeStation = {
        stationId: item.station_id,
        name: item.name,
        lon: item.lon,
        lat: item.lat,
        numOfBikes: (item.hasOwnProperty('num_bikes_available') ? item.num_bikes_available : 0),
        capacity: (item.hasOwnProperty('capacity') ? item.capacity : 0),
        lastReported: item.last_reported
      };
      stationList.push(new_station);
    }

    const bikeStations = stationList;
    this.setState({ bikeStations });
  }

  async bindPredictionsToMap() {
    let result = await this.predictions();
    let stationsList: BikeStation[] = this.state.bikeStations;

    for (let i = 0; i < stationsList.length; i++) {
      stationsList[i].numOfBikes = result[stationsList[i].stationId];
    }
    
    this.setState({ bikeStations: stationsList });
  }

  async bindReviewsToModal(stationId: number) {
    let result = await this.reviews(stationId)
    
    let reviews: Review[] = [];
    for (let i = 0; i < result.length; i++) {
      let review: Review = {
        userId: result[i].user_id,
        stationId: result[i].station_id,
        stationName: result[i].station_name,
        review: result[i].review,
        createdDate: new Date(result[i].create_date),
      };

      reviews.push(review);
    }
    
    this.setState({
      reviews: reviews.reverse(),
      isLoading: false,
    })
  }

  validateSearchForm = () => {
    return this.state.searchInput.length > 0;
  }

  validateToggle = () => {
    return this.state.isSearchOpen ? "arrow-up" : "arrow-down";
  }

  validateRideForm = () => {
    return this.state.ride.duration > 0;
  }

  validateReviewForm = () => {
    return this.state.review.review.trim().length > 3;
  }

  handleSearchChange = (event: any) => {
    const { id, value } = event.target;
    this.setState({
      searchInput: value 
    });
  }

  handleSearchClick = () => {
    this.bindBikeStationsToMap(this.state.searchInput);
  }

  handleSearchKeyPress = (event: any) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      this.bindBikeStationsToMap(this.state.searchInput);
    }
  }

  handleClearClick = () => { 
    this.setState({searchInput: ''}); 
    this.bindBikeStationsToMap('*');
  }

  handleToggleClick = () => {
    let toggleState = !this.state.isSearchOpen;
    this.setState({isSearchOpen: toggleState});
  }

  handlePredictChange = (date: Date) => {
    this.setState({
      predictInput: date
    })
  }

  handlePredictClick = () => {
    this.bindPredictionsToMap();
  }

  handleRideClick = (station: BikeStation) => {
    const ride: Ride = {
      stationId: station.stationId,
      stationName: station.name,
      duration: 0,
      price: 0
    };
    this.setState( { ride });
    this.handleToggleRideModal(true);
  }

  handleRideDurationChange = (event: any) => {
    const hourlyRate = 3.15;

    let ride = this.state.ride;
    ride.duration = event.target.value;
    ride.price = ride.duration * hourlyRate;
    this.setState( { ride });
  }

  handleReviewChange = (event: any) => {
    let review = this.state.review;
    review.review = event.target.value;
    if (review.review.length <= 140) {
      this.setState( { review });
    }
  }

  handleRentClick = () => {
    this.setState({
      isUpdating: true,
    })

    return API.post("bikenow", "/rides", { body: {
      station_id: this.state.ride.stationId,
      station_name: this.state.ride.stationName,
      duration: this.state.ride.duration,
      price: this.state.ride.price,
    }}).then((value: any) => {
      this.setState({
        isUpdating: false,
        showRideModal: false,
        redirect: '/rides'
      });
    });
  }

  handleReviewSubmitClick = () => {
    this.setState({
      isUpdating: true,
    })

    return API.post("bikenow", "/reviews", { body: {
      station_id: this.state.review.stationId,
      station_name: this.state.review.stationName,
      review: this.state.review.review,
    }}).then((value: any) => {
      this.setState({
        isUpdating: false,
        isLoading: true,
        review: {
          userId: '',
          stationId: this.state.review.stationId,
          stationName: this.state.review.stationName,
          review: '',
          createdDate: new Date(),
        }
      });
      this.bindReviewsToModal(this.state.review.stationId);
    })
  }

  handleReviewsClick = (station: BikeStation) => {
    const review: Review = {
      userId: '',
      stationId: station.stationId,
      stationName: station.name,
      review: '',
      createdDate: new Date(),
    };
    this.setState( { 
      review: review,
      isLoading: true,
    });
    this.handleToggleReviewModal(true);
    this.bindReviewsToModal(station.stationId);
  }

  handleToggleRideModal = (shouldShow: boolean) => {
    this.setState({
      showRideModal: shouldShow
    });
  }

  handleToggleReviewModal = (shouldShow: boolean) => {
    this.setState({
      showReviewModal: shouldShow
    });
  }

  renderReviewsList(reviews: Review[]) {
    let reviewsList: Review[] = [];

    return reviewsList.concat(reviews).map(
      (review, i) =>
        <tr key={i}>
          <td>{new Date(review.createdDate).toLocaleDateString()}</td>
          <td>{review.review}</td>
        </tr>
    );
  }

  renderReviewModal() {
    const { review } = this.state;
    return (
      <Modal
        show={this.state.showReviewModal}
        onHide={() => this.handleToggleReviewModal(false)}
        container={this}
        aria-labelledby="contained-modal-title"
        id="contained-modal">
        <Modal.Header closeButton>
          <Modal.Title id="contained-modal-title">{ review.stationName }</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <h5 className="modal-prompt">Write a review:</h5>
          <Form>
            <Form.Control as="textarea" rows="4" value={review.review} onChange={this.handleReviewChange} />
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button
            type="button"
            variant="danger"
            className="uniform-width"
            disabled={!this.validateReviewForm()}
            onClick={this.handleReviewSubmitClick}>
            {this.state.isUpdating ?
              <span><Spinner size="sm" animation="border" className="mr-2" />Updating</span> :
              <span>Submit</span>}
            </Button>
        </Modal.Footer>
        <Modal.Body>
          {
            this.state.isLoading ?
              <Spinner animation="border" className="center-spinner" /> :
              (this.state.reviews.length === 0) ?
                <div className="text-center">This bike station does not have any reviews.</div> :
                <Table variant="light">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Review</th>
                  </tr>
                </thead>
                <tbody>
                  { this.renderReviewsList(this.state.reviews) }
                </tbody>
                </Table>
          }
        </Modal.Body>
      </Modal>
    );
  }

  renderRideModal() {
    const { ride } = this.state;
    return (
      <Modal
        show={this.state.showRideModal}
        onHide={() => this.handleToggleRideModal(false)}
        container={this}
        aria-labelledby="contained-modal-title"
        id="contained-modal">
        <Modal.Header closeButton>
          <Modal.Title id="contained-modal-title">{ ride.stationName }</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <h5 className="modal-prompt">How long do you want to ride?</h5>
          <Form>
            <Form.Row className="form-header">
              <Form.Group as={Col}>
                <FormLabel className="form-header">Hours</FormLabel>
              </Form.Group>
              <Form.Group as={Col}>
                <FormLabel>Total</FormLabel>
              </Form.Group>
            </Form.Row>
            <Form.Row>
              <Form.Group as={Col}>
                <select value={ride.duration} onChange={this.handleRideDurationChange} className="form-control">
                  <option value="0">0</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                  <option value="9">9</option>
                </select>
              </Form.Group>
              <Form.Group as={Col} className="modal-price">$
                { this.state.ride.price.toFixed(2) }
              </Form.Group>
            </Form.Row>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button
            type="button"
            variant="danger"
            className="uniform-width"
            disabled={!this.validateRideForm()}
            onClick={this.handleRentClick}>
            {this.state.isUpdating ?
              <span><Spinner size="sm" animation="border" className="mr-2" />Updating</span> :
              <span>Rent</span>}
            </Button>
        </Modal.Footer>
      </Modal>
    );
  }

  renderBikeStations(bikeStations: BikeStation[]) {
    let stationsList: BikeStation[] = [];
    return stationsList.concat(bikeStations).map(
      (station, i) => {
        let markerColor = 'black';
        if (station.numOfBikes >= 10) markerColor = 'green';
        else if (station.numOfBikes >= 5) markerColor = 'yellow';
        else if (station.numOfBikes >= 1) markerColor = 'red';
        return (
          <CircleMarker key={station.stationId} center={[station.lat, station.lon]} color={markerColor} radius={10}>
            <Popup className='request-popup'>
              <Table>
                <thead>
                  <tr>
                    <th colSpan={2} className='popup-title'>{station.name}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className='popup-label'>Bikes Available:</td>
                    <td className='popup-caption'>{station.numOfBikes}</td>
                  </tr>
                  <tr>
                    <td className='popup-label'>Station Capacity:</td>
                    <td className='popup-caption'>{station.capacity}</td>
                  </tr>
                  <tr>
                    <td align='center'><Button variant="primary" type='button' className='uniform-width' onClick={() => this.handleRideClick(station)}>Ride</Button></td>
                    <td align='center'><Button variant="primary" type='button' className='uniform-width' onClick={() => this.handleReviewsClick(station)}>Reviews</Button></td>
                  </tr>
                </tbody>
              </Table>
            </Popup>
          </CircleMarker>
        )
      }
    )
  }

  renderLanding() {
    return (
      <div className="lander">
        <h2>Real-time Station Status</h2>
        <hr />
        <p>AWS BikeNow Demo is a sample web application that demonstrates the breadth and depth of database, analytics, and AI/ML services on AWS. AWS offers the broadest and deepest portfolio of purpose-built, fully managed database services as well as the most comprehensive, secure, scalable, and cost-effective portfolio of analytics services. With AWS BikeNow Demo, developers can use AWS database and analytics services to manage data through the entirety of its lifecycle, from ingestion, storage, feature engineering, visualization, and analysis in support of data-driven innovation.</p>
        <div className="button-container col-md-12">
          <a href="/signup" className="orange-link">Sign up to explore the demo</a>
        </div>
        <img src={bikenowImage} className="img-fluid full-width lander-screen" alt="Screenshot"></img>
      </div>);
  }

  renderHome() {
    const position = {
      lat: 40.7397,
      lon: -73.9945,
      zoom: 14,
    }
    return (
          <div>
            <h2>Real-time Bike Station Status</h2>
            <Form>
              <Form.Row>
                <Form.Group as={Col} md="8">
                  <FormControl 
                    id="search"
                    minLength={1}
                    placeholder="Search bike stations.."
                    value={this.state.searchInput}
                    onChange={this.handleSearchChange}
                    onKeyPress={this.handleSearchKeyPress}
                    required />
                </Form.Group>
                <Form.Group as={Col} md="1">
                  <Button variant="primary" type='button' className='uniform-width' onClick={this.handleSearchClick} disabled={!this.validateSearchForm()}>Search</Button>
                </Form.Group>
                <Form.Group as={Col} md="1">
                  <Button variant="primary" type='button' className='uniform-width' onClick={this.handleClearClick}>Clear</Button>
                </Form.Group>
              </Form.Row>
            </Form>
            <Accordion>
              <Card className="adv-search-header">
                <Card.Header className="adv-search-header">
                  <Accordion.Toggle as={Card.Header} variant="link" eventKey="0" className="adv-search-toggle" onClick={this.handleToggleClick}>
                    <p><i className={this.validateToggle()}></i>&nbsp;&nbsp;Plan Your Trip</p>
                  </Accordion.Toggle>
                </Card.Header>
                <Accordion.Collapse eventKey="0">
                  <Card.Body className="adv-search-body">
                    <Form>
                      <Form.Row>
                        <Form.Group as={Col} md="8">
                          <DatePicker selected={this.state.predictInput} 
                                      onChange={this.handlePredictChange} 
                                      showTimeSelect 
                                      dateFormat="Pp" />
                        </Form.Group>
                        <Form.Group as={Col} md="1">
                          <Button variant="primary" type="button" className="uniform-width" onClick={this.handlePredictClick}>Plan</Button>
                        </Form.Group>
                      </Form.Row>
                    </Form>
                  </Card.Body>
                </Accordion.Collapse>
              </Card>
            </Accordion>
            <Map center={[position.lat, position.lon]} zoom={position.zoom}>
              <TileLayer
                attribution='&amp;copy <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
                { this.renderBikeStations(this.state.bikeStations) }        
            </Map>
            <div>&nbsp;</div>
            { this.state.showRideModal && this.renderRideModal() }
            { this.state.showReviewModal && this.renderReviewModal() }
          </div>          
        );
  }

  render() {
    let { redirect } = this.state;
    if (redirect) {
      return <Redirect push to={redirect} />;
    }

    return (
      <div className="Home">
        {this.props.isAuthenticated ? this.renderHome() : this.renderLanding()}
      </div>
    );
  }
}