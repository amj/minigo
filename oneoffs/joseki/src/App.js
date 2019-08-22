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

import React from 'react';
import axios from 'axios';
import colormap from 'colormap';

import {range, flatten} from 'lodash';
import go from 'godash';
import godash from 'godash';
import {Goban} from './goban';

import Button from '@material-ui/core/Button';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import ToggleButton from '@material-ui/lab/ToggleButton';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import {styled} from '@material-ui/styles';

import Chart from 'react-google-charts';
import KeyboardEventHandler from 'react-keyboard-event-handler';

import './App.css';


const MyButton = styled(Button)({
    margin: 10,
});

const colors = colormap({
  colormap: 'copper',
  nshades: 50,
  format: 'rgbaString',
  alpha: [0.01,1]
});


// Lol "const"
const defaultHighlights = {}
defaultHighlights[colors[0]] = flatten(range(10).map(idx => {
        return range(10-idx).map(jdx => {
          return {x: 18-idx, y:9-jdx };
        });
      }));

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
          other_highlights: defaultHighlights, // if so, what moves were considered then?
          highlights: defaultHighlights,
          search_enabled: false,
          tableData: null,
          count: null,
          run: null,
        };

        this.resetBoard = this.resetBoard.bind(this);
        this.coordinateClicked = this.coordinateClicked.bind(this);
        this.search = this.search.bind(this);
        this.pass = this.pass.bind(this);
        this.handleRunChange = this.handleRunChange.bind(this);
        this.prevMove = this.prevMove.bind(this);
        this.handleKeyDown = this.handleKeyDown.bind(this);

}

  handleKeyDown(key, e) {
    if (key === 'left') {
      this.prevMove(e);
    }
  }

  resetBoard() {
    this.setState({
      board: new godash.Board(),
      nextColor: godash.BLACK,
      passNext: true,
      moves: "",
      highlights: defaultHighlights,
      other_highlights: defaultHighlights,
      tableData: null,
      search_enabled: false,
      run: null,
    });
  }

  searchEnabled(moves) {
      return (moves.match(/;/g)||[]).length >= 3 ? true : false;
  }

  prevMove(event) {
      var num_moves = (this.state.moves.match(/;/g)||[]).length;
      if (num_moves <= 1){
        return;
      }
      var new_moves = this.state.moves.split(';')
      new_moves.pop()
      var m = new_moves.pop()
      new_moves = new_moves.join(';') + ';'
      this.setState({
        board: godash.removeStone(this.state.board, godash.sgfPointToCoordinate(m.slice(2,4))),
        nextColor: (this.state.nextColor === godash.BLACK ? godash.WHITE : godash.BLACK),
        moves: new_moves,
        search_enabled: this.searchEnabled(new_moves)
      }, () => { 
        this.updateHeatmap();
        if(num_moves >= 1) {
          this.search();
        }
      });

  }

  handleRunChange(event, newRun) {
    this.setState({
      run: newRun,
    }, () => {
      console.log('run changed to', this.state.run);
      this.updateHeatmap();
    });
  }

  coordinateClicked(coordinate) {
      var m = this.state.nextColor === godash.BLACK ? "B[" : "W[";
      m = m + godash.coordinateToSgfPoint(coordinate) + "];";
      var num_moves = (this.state.moves.match(/;/g)||[]).length;

      this.setState({
          board: godash.addMove(this.state.board, coordinate, this.state.nextColor),
          nextColor: (this.state.nextColor === godash.BLACK ? godash.WHITE : godash.BLACK),
          moves: this.state.moves + m,
          highlights: null,
          search_enabled: this.searchEnabled(this.state.moves+m)
      }, () => {
        this.updateHeatmap();
        if(num_moves >= 1) {
          this.search();
        }
      });
  }

  updateHeatmap() {
      axios.post('/nexts', {
        params: {
          prefix: this.state.moves,
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
        console.log(highlights);
        this.setState({
            highlights: highlights,
            other_highlights: other_highlights,
            passNext: passFound,
            count: response.data.count
        });
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
        <KeyboardEventHandler
            handleKeys={['left', 'right']}
                onKeyEvent={(key, e) => {
                  this.handleKeyDown(key, e);
                }} />

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
              {this.state.moves ? this.state.moves : "The active sequence will appear here"}
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
                    view_window={{x:[8,19], y:[0,10]}} 
                />
                <MyButton variant="contained" onClick={this.search}
                          color="primary" disabled={!this.state.search_enabled}>Search</MyButton>
                <MyButton variant="contained" onClick={this.pass}
                          color={this.state.passNext ? "secondary" : "default"}>Tenuki</MyButton>
                <MyButton variant="contained" onClick={this.resetBoard}>Clear</MyButton>
            <ToggleButtonGroup variant="contained" exclusive value={this.state.run} onChange={this.handleRunChange} size='small'>
                <ToggleButton variant="contained" value="v15">v15</ToggleButton>
                <ToggleButton variant="contained" value="v16">v16</ToggleButton>
                <ToggleButton variant="contained" value="v17">v17</ToggleButton>
            </ToggleButtonGroup>
            </Grid>

            <Grid item xs={6}>
            {this.state.tableData === null ? (<div >
              <Typography variant="h5" align='left' gutterBottom>
              <p> Explore Minigo's most common opening moves during its training by clicking on the board to the left. </p>
              </Typography>
              <Typography variant="subtitle1" align='left' gutterBottom>
              <p> For sequences longer than two moves, a frequency graph will appear here showing the openings' popularity over time. </p>
              <p> Joseki's beginning with black or white are tabulated independently, as are transpositions.</p>
              <p> If tenuki was a frequently played option, 'tenuki' button will be enabled to toggle the next color to be played. </p>
              </Typography>
              </div>) :
                <Chart
                    loader={ <p> Chart loading... </p> }
                    chartType="ScatterChart"
                    data={this.state.tableData}
                    options = {{
                              title: `How frequently this sequence was seen over training`,
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
            }
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
