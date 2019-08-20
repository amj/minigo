import React from 'react';
import godash from 'godash';
import {Goban} from 'react-go-board';
/*
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/
import Button from '@material-ui/core/Button';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import ToggleButton from '@material-ui/lab/ToggleButton';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import {styled} from '@material-ui/styles';
import axios from 'axios';
import Chart from 'react-google-charts';
import colormap from 'colormap';

import './App.css';

const MyButton = styled(Button)({
    margin: 10,
});

const colors = colormap({
  colormap: 'copper',
  nshades: 50,
  format: 'rgbaString',
  alpha: [0.05,1]
});

class DefaultDict {
  constructor(defaultInit) {
    return new Proxy({}, {
      get: (target, name) => name in target ?
        target[name] :
        (target[name] = typeof defaultInit === 'function' ?
          new defaultInit().valueOf() :
          defaultInit)
      })
  }
}

class Joseki extends React.Component {
  constructor(props) {
        super(props);
        this.state = {
          moves: "",
          board: new godash.Board(),
          nextColor: godash.BLACK,
          passNext: true,  // was 'pass' one of the next moves played here.
          other_highlights: null, // if so, what moves were considered then?
          search_enabled: false,
          tableData: null,
          highlights: null,
          count: null,
          run: 'v17',
        };

        this.resetBoard = this.resetBoard.bind(this);
        this.coordinateClicked = this.coordinateClicked.bind(this);
        this.search = this.search.bind(this);
        this.pass = this.pass.bind(this);
        this.handleRunChange = this.handleRunChange.bind(this);
  }

  handleRunChange(event, newRun) {
    this.setState({
      run: newRun,
    });

    this.updateHeatmap("");
  }

  coordinateClicked(coordinate) {
      var m = this.state.nextColor === godash.BLACK ? "B[" : "W[";
      m = m + godash.coordinateToSgfPoint(coordinate) + "];";
      var num_moves = (this.state.moves.match(/;/g)||[]).length - 1;

      this.setState({
          board: godash.addMove(this.state.board, coordinate, this.state.nextColor),
          nextColor: (this.state.nextColor === godash.BLACK ? godash.WHITE : godash.BLACK),
          moves: this.state.moves + m,
          highlights: null,
          search_enabled: num_moves >= 4 ? true : false
      });

      this.updateHeatmap(m);
  }

  updateHeatmap(m) {
      axios.post('/nexts', {
        params: {
          prefix: this.state.moves + m,
          run: this.state.run
        }
      }).then(response => {
        var next = this.state.nextColor === godash.BLACK ? 'W' : 'B';
        // make a dumb defaultdict
        var highlights = new DefaultDict(Array);
        var other_highlights = new DefaultDict(Array);
        var passFound = false;
        for (const [coord,freq] of Object.entries(response.data.next_moves)) { 
            if (coord[0] === next) {
              passFound = true;
              other_highlights[colors[Math.floor(freq * 48)]].push(godash.sgfPointToCoordinate(coord.slice(2,4)))
              continue;
            }
            highlights[colors[Math.floor(freq * 48)]].push(godash.sgfPointToCoordinate(coord.slice(2,4)))
        }
        this.setState({
            highlights: highlights,
            other_highlights: other_highlights,
            passNext: passFound,
            count: response.data.count
        });
      });
  }

  resetBoard() {
    this.setState({
      board: new godash.Board(),
      nextColor: godash.BLACK,
      passNext: true,
      moves: "",
      highlights: null,
      other_highlights: null,
      search_enabled: false,
    });
  }

  pass() {
      this.setState({
          nextColor: (this.state.nextColor === godash.BLACK ? godash.WHITE : godash.BLACK),
          other_highlights: this.state.highlights,
          highlights: this.state.other_highlights
      });
  }

  search() {
    axios.post('/search', {
      params: {
        sgf: this.state.moves,
      }
    }).then(response => {
      console.log(response.data);
      this.setState({
        tableData: [response.data.cols, ...response.data.rows]
      });

    });
  }

  render() {
    return (
      <div className="App">
        <AppBar position="static">
          <Toolbar>
                <h3 className="{classes.title}">
                  Joseki Explorer
                </h3>
          </Toolbar>
        </AppBar>
        <div style={{ marginTop:20 }}> </div>
        <Container>
              <Typography variant="h4" align='left' gutterBottom>
              {this.state.moves ? this.state.moves : "Click to explore joseki"}
              </Typography>
              <Typography variant="h5" align='left' gutterBottom>
              { this.state.moves ?
                <p>Seen: {this.state.count} times </p>
                    : <p>&nbsp;</p>
              }
              </Typography>

          <Grid container justify="flex-start" spacing={1}>
            <Grid item xs={6}>
                <Goban
                    board={this.state.board}
                    onCoordinateClick={this.coordinateClicked}
                    highlights={this.state.highlights}
                />
                <MyButton variant="contained" onClick={this.search}
                          color="primary" disabled={!this.state.search_enabled}>Search</MyButton>
                <MyButton variant="contained" onClick={this.pass}
                          color={this.state.passNext ? "secondary" : "default"}>Pass</MyButton>
                <MyButton variant="contained" onClick={this.resetBoard}>Clear</MyButton>
            <ToggleButtonGroup variant="contained" exclusive value={this.state.run} onChange={this.handleRunChange}>
                <ToggleButton variant="contained" value="v15">v15</ToggleButton>
                <ToggleButton variant="contained" value="v16">v16</ToggleButton>
                <ToggleButton variant="contained" value="v17">v17</ToggleButton>
            </ToggleButtonGroup>
            </Grid>

            <Grid item xs={6}>
                <Chart
                    loader={ <p> Chart goes here </p> }
                    chartType="ScatterChart"
                    data={this.state.tableData}
                    options = {{
                              title: `How many times sequences was seen over training`,
                              hAxis: {title: '% of training',
                                      viewWindow: {min: 0, max: 100}},
                              vAxis: {title: 'Frequency', logScale: true},
                              legend: { position : 'bottom'},
                              theme: 'material',
                              pointSize: 3,
                    }}
                    height={'600px'}
                    width={'800px'}
                />
            </Grid>
          </Grid>
        </Container>
      </div>
    );
  }
}

function App() {
  return ( <Joseki /> );
}

export default App;
